import json
import os
import sys
import time
import traceback
import warnings
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import redis
from celery import Task

# 确保项目根目录在路径中
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api.celery_app import celery_app
from api.core.config import get_settings
from src.audio_extractor import AudioExtractor
from src.downloader import VideoDownloader
from src.formatter import save as formatter_save
from src.local_transcriber import LocalTranscriber
from src.transcriber import Transcriber
from src.utils import extract_video_id, is_valid_video_url

settings = get_settings()

# Redis 连接（用于存储任务元数据）
redis_client = redis.from_url(settings.redis_url, decode_responses=True)

# 模型缓存，worker 进程内复用
_model_cache = {}


def _get_local_transcriber(model_size: str, device: str, language: str | None):
    key = (model_size, device, language)
    if key not in _model_cache:
        _model_cache[key] = LocalTranscriber(
            model_size=model_size,
            device=device,
            language=language,
        )
    return _model_cache[key]


def _publish_update(task_id: str, **fields):
    """通过 Redis Pub/Sub 推送实时进度"""
    try:
        redis_client.publish(
            "task_updates",
            json.dumps({"task_id": task_id, **fields}),
        )
    except Exception:
        pass


def _update_task_meta(task_id: str, **fields):
    key = f"task_meta:{task_id}"
    data = {}
    for k, v in fields.items():
        if isinstance(v, datetime):
            data[k] = v.isoformat()
        elif v is not None:
            data[k] = str(v)
    if data:
        redis_client.hset(key, mapping=data)
        # 同时推送实时进度
        _publish_update(task_id, **{k: v for k, v in fields.items() if k not in ("updated_at", "completed_at")})


def _get_task_meta(task_id: str) -> dict:
    key = f"task_meta:{task_id}"
    return redis_client.hgetall(key) or {}


def _init_task_meta(task_id: str, url: str, params: dict):
    key = f"task_meta:{task_id}"
    now = datetime.now().isoformat()
    redis_client.hset(key, mapping={
        "id": task_id,
        "url": url,
        "status": "pending",
        "language": params.get("language", "en"),
        "output_format": params.get("output_format", "json"),
        "use_local": str(params.get("use_local", True)),
        "model_size": params.get("model_size", "tiny"),
        "created_at": now,
        "progress": "0",
    })
    redis_client.expire(key, 86400 * settings.result_retention_days)
    _publish_update(task_id, status="pending", progress=0)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def process_video(self: Task, task_id: str, url: str, params: dict):
    """Celery 任务：下载视频 -> 提取音频 -> 语音识别 -> 保存结果"""
    temp_dir = Path(settings.temp_dir) / task_id
    output_dir = Path(settings.output_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    _init_task_meta(task_id, url, params)

    try:
        # 1. 验证链接
        if not is_valid_video_url(url):
            raise ValueError("无效的视频链接，仅支持 Facebook 和 YouTube")

        # 2. 下载视频
        self.update_state(state="DOWNLOADING", meta={"progress": 10})
        _update_task_meta(task_id, status="downloading", progress=10, updated_at=datetime.now())

        downloader = VideoDownloader(temp_dir=str(temp_dir))
        video_path = downloader.download(url)

        # 3. 提取音频
        self.update_state(state="EXTRACTING_AUDIO", meta={"progress": 30})
        _update_task_meta(task_id, status="extracting_audio", progress=30, updated_at=datetime.now())

        extractor = AudioExtractor(temp_dir=str(temp_dir))
        audio_path = extractor.extract(video_path)

        # 4. 语音识别
        self.update_state(state="TRANSCRIBING", meta={"progress": 50})
        _update_task_meta(task_id, status="transcribing", progress=50, updated_at=datetime.now())

        language = None if params.get("language") == "auto" else params.get("language")

        if params.get("use_local", True):
            transcriber = _get_local_transcriber(
                model_size=params.get("model_size", "tiny"),
                device=params.get("device", "cpu"),
                language=language,
            )
        else:
            api_key = settings.openai_api_key
            if not api_key:
                raise ValueError("未配置 OPENAI_API_KEY，无法使用 API 模式")
            transcriber = Transcriber(api_key=api_key, language=params.get("language", "en"))

        result = transcriber.transcribe(audio_path)

        # 5. 保存结果
        self.update_state(state="SAVING", meta={"progress": 90})
        _update_task_meta(task_id, status="saving", progress=90, updated_at=datetime.now())

        output_path = output_dir / f"{task_id}.{params.get('output_format', 'json')}"
        formatter_save(result, str(output_path), fmt=params.get("output_format", "json"))

        # 复制视频到输出目录供下载
        video_output = output_dir / f"{task_id}.mp4"
        import shutil
        shutil.copy2(video_path, video_output)

        # 更新元数据
        _update_task_meta(
            task_id,
            status="completed",
            progress=100,
            language=result.get("language", ""),
            duration=str(result.get("duration", 0)),
            result_url=f"/tasks/{task_id}/download",
            video_url=f"/tasks/{task_id}/download-video",
            updated_at=datetime.now(),
            completed_at=datetime.now(),
        )

        # 清理临时文件
        for f in temp_dir.iterdir():
            if f.is_file():
                f.unlink()
        temp_dir.rmdir()

        return {
            "task_id": task_id,
            "status": "completed",
            "language": result.get("language"),
            "duration": result.get("duration"),
            "output_file": str(output_path),
        }

    except Exception as exc:
        error_msg = str(exc)
        tb = traceback.format_exc()
        _update_task_meta(
            task_id,
            status="failed",
            error_message=error_msg,
            updated_at=datetime.now(),
        )
        # 记录到日志文件
        log_path = output_dir / f"{task_id}.error.log"
        log_path.write_text(f"{error_msg}\n\n{tb}", encoding="utf-8")
        raise self.retry(exc=exc) from exc
