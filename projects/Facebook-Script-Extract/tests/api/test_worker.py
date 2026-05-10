import json
from datetime import datetime
from pathlib import Path
from unittest.mock import ANY, MagicMock, patch

import pytest
from celery import Task

from api.tasks.worker import (
    _get_local_transcriber,
    _get_task_meta,
    _init_task_meta,
    _publish_update,
    _update_task_meta,
    process_video,
)


@pytest.fixture
def mock_redis_client():
    with patch("api.tasks.worker.redis_client") as mock:
        yield mock


@pytest.fixture
def mock_settings():
    with patch("api.tasks.worker.settings") as mock:
        mock.temp_dir = "./temp"
        mock.output_dir = "./output"
        mock.result_retention_days = 7
        mock.openai_api_key = "sk-test"
        yield mock


class TestGetTaskMeta:
    def test_get_existing_meta(self, mock_redis_client):
        mock_redis_client.hgetall.return_value = {"status": "pending", "url": "https://example.com"}
        result = _get_task_meta("task-123")
        assert result["status"] == "pending"
        mock_redis_client.hgetall.assert_called_once_with("task_meta:task-123")

    def test_get_nonexistent_meta(self, mock_redis_client):
        mock_redis_client.hgetall.return_value = {}
        result = _get_task_meta("task-123")
        assert result == {}


class TestInitTaskMeta:
    def test_init_creates_hash(self, mock_redis_client):
        _init_task_meta(
            "task-123",
            "https://www.facebook.com/watch?v=123",
            {"language": "auto", "output_format": "json"},
        )

        mock_redis_client.hset.assert_called_once()
        args, kwargs = mock_redis_client.hset.call_args
        assert args[0] == "task_meta:task-123"
        mapping = kwargs["mapping"]
        assert mapping["status"] == "pending"
        assert mapping["url"] == "https://www.facebook.com/watch?v=123"
        assert mapping["progress"] == "0"

    def test_init_sets_expiry(self, mock_redis_client):
        _init_task_meta("task-123", "https://example.com", {})
        mock_redis_client.expire.assert_called_once_with("task_meta:task-123", 86400 * 7)

    def test_init_publishes_update(self, mock_redis_client):
        _init_task_meta("task-123", "https://example.com", {})
        mock_redis_client.publish.assert_called_once()
        call_args = mock_redis_client.publish.call_args
        assert call_args[0][0] == "task_updates"
        data = json.loads(call_args[0][1])
        assert data["task_id"] == "task-123"
        assert data["status"] == "pending"


class TestUpdateTaskMeta:
    def test_update_fields(self, mock_redis_client):
        _update_task_meta("task-123", status="downloading", progress=10)
        mock_redis_client.hset.assert_called_once()
        args, kwargs = mock_redis_client.hset.call_args
        mapping = kwargs["mapping"]
        assert mapping["status"] == "downloading"
        assert mapping["progress"] == "10"

    def test_update_datetime_serialization(self, mock_redis_client):
        now = datetime(2026, 4, 25, 12, 0, 0)
        _update_task_meta("task-123", updated_at=now)
        args, kwargs = mock_redis_client.hset.call_args
        mapping = kwargs["mapping"]
        assert "2026-04-25" in mapping["updated_at"]

    def test_update_none_ignored(self, mock_redis_client):
        _update_task_meta("task-123", status="completed", error_message=None)
        args, kwargs = mock_redis_client.hset.call_args
        mapping = kwargs["mapping"]
        assert "error_message" not in mapping

    def test_update_publishes_non_time_fields(self, mock_redis_client):
        _update_task_meta("task-123", status="downloading", progress=30, updated_at=datetime.now())
        published = json.loads(mock_redis_client.publish.call_args[0][1])
        assert "status" in published
        assert "progress" in published
        assert "updated_at" not in published


class TestPublishUpdate:
    def test_publish_success(self, mock_redis_client):
        _publish_update("task-123", status="completed", progress=100)
        mock_redis_client.publish.assert_called_once_with(
            "task_updates",
            json.dumps({"task_id": "task-123", "status": "completed", "progress": 100}),
        )

    def test_publish_failure_silent(self, mock_redis_client):
        mock_redis_client.publish.side_effect = Exception("Redis error")
        _publish_update("task-123", status="failed")
        # 不应抛出异常


class TestGetLocalTranscriber:
    @patch("api.tasks.worker.LocalTranscriber")
    def test_creates_new_instance(self, mock_transcriber_class):
        mock_instance = MagicMock()
        mock_transcriber_class.return_value = mock_instance

        # 清除缓存
        import api.tasks.worker as worker_module
        worker_module._model_cache.clear()

        result = _get_local_transcriber("small", "cpu", "zh")
        assert result is mock_instance
        mock_transcriber_class.assert_called_once_with(
            model_size="small", device="cpu", language="zh"
        )

    @patch("api.tasks.worker.LocalTranscriber")
    def test_reuses_cached_instance(self, mock_transcriber_class):
        mock_instance = MagicMock()
        mock_transcriber_class.return_value = mock_instance

        import api.tasks.worker as worker_module
        worker_module._model_cache.clear()

        _get_local_transcriber("base", "cuda", "en")
        _get_local_transcriber("base", "cuda", "en")

        mock_transcriber_class.assert_called_once()

    @patch("api.tasks.worker.LocalTranscriber")
    def test_different_params_creates_new(self, mock_transcriber_class):
        mock_instance = MagicMock()
        mock_transcriber_class.return_value = mock_instance

        import api.tasks.worker as worker_module
        worker_module._model_cache.clear()

        _get_local_transcriber("small", "cpu", "zh")
        _get_local_transcriber("base", "cpu", "zh")

        assert mock_transcriber_class.call_count == 2


class TestProcessVideo:
    @patch("api.tasks.worker._init_task_meta")
    @patch("api.tasks.worker.is_valid_video_url")
    @patch("api.tasks.worker.VideoDownloader")
    @patch("api.tasks.worker.AudioExtractor")
    @patch("api.tasks.worker._get_local_transcriber")
    @patch("api.tasks.worker.formatter_save")
    @patch("api.tasks.worker._update_task_meta")
    def test_local_mode_success(
        self,
        mock_update_meta,
        mock_formatter_save,
        mock_get_local,
        mock_extractor_class,
        mock_downloader_class,
        mock_is_valid,
        mock_init_meta,
        mock_settings,
        tmp_path,
    ):
        mock_settings.temp_dir = str(tmp_path / "temp")
        mock_settings.output_dir = str(tmp_path / "output")

        mock_is_valid.return_value = True

        mock_downloader = MagicMock()
        mock_downloader.download.return_value = str(tmp_path / "temp" / "video.mp4")
        mock_downloader_class.return_value = mock_downloader

        mock_extractor = MagicMock()
        mock_extractor.extract.return_value = str(tmp_path / "temp" / "audio.mp3")
        mock_extractor_class.return_value = mock_extractor

        mock_transcriber = MagicMock()
        mock_transcriber.transcribe.return_value = {
            "language": "en",
            "duration": 10.5,
        }
        mock_get_local.return_value = mock_transcriber

        with patch.object(process_video, "update_state"):
            result = process_video.run(
                "task-123",
                "https://www.facebook.com/watch?v=123",
                {
                    "language": "auto",
                    "output_format": "json",
                    "use_local": True,
                    "model_size": "small",
                    "device": "cpu",
                },
            )

        assert result["status"] == "completed"
        assert result["task_id"] == "task-123"
        mock_formatter_save.assert_called_once()
        mock_update_meta.assert_any_call(
            "task-123",
            status="downloading",
            progress=10,
            updated_at=ANY,
        )

    @patch("api.tasks.worker._init_task_meta")
    @patch("api.tasks.worker.is_valid_video_url")
    @patch("api.tasks.worker._update_task_meta")
    def test_invalid_url_raises(self, mock_update_meta, mock_is_valid, mock_init_meta, mock_settings, tmp_path):
        mock_settings.temp_dir = str(tmp_path / "temp")
        mock_settings.output_dir = str(tmp_path / "output")

        mock_is_valid.return_value = False

        with patch.object(process_video, "update_state"):
            with pytest.raises(ValueError, match="无效的视频链接，仅支持 Facebook 和 YouTube"):
                process_video.run(
                    "task-123",
                    "https://example.com",
                    {},
                )

    @patch("api.tasks.worker._init_task_meta")
    @patch("api.tasks.worker.is_valid_video_url")
    @patch("api.tasks.worker.VideoDownloader")
    @patch("api.tasks.worker.AudioExtractor")
    @patch("api.tasks.worker.Transcriber")
    @patch("api.tasks.worker.formatter_save")
    @patch("api.tasks.worker._update_task_meta")
    def test_api_mode_success(
        self,
        mock_update_meta,
        mock_formatter_save,
        mock_transcriber_class,
        mock_extractor_class,
        mock_downloader_class,
        mock_is_valid,
        mock_init_meta,
        mock_settings,
        tmp_path,
    ):
        mock_settings.temp_dir = str(tmp_path / "temp")
        mock_settings.output_dir = str(tmp_path / "output")
        mock_settings.openai_api_key = "sk-test"

        mock_is_valid.return_value = True

        mock_downloader = MagicMock()
        mock_downloader.download.return_value = str(tmp_path / "temp" / "video.mp4")
        mock_downloader_class.return_value = mock_downloader

        mock_extractor = MagicMock()
        mock_extractor.extract.return_value = str(tmp_path / "temp" / "audio.mp3")
        mock_extractor_class.return_value = mock_extractor

        mock_transcriber = MagicMock()
        mock_transcriber.transcribe.return_value = {
            "language": "zh",
            "duration": 5.0,
        }
        mock_transcriber_class.return_value = mock_transcriber

        with patch.object(process_video, "update_state"):
            result = process_video.run(
                "task-123",
                "https://www.facebook.com/watch?v=123",
                {
                    "language": "zh",
                    "output_format": "json",
                    "use_local": False,
                },
            )

        assert result["status"] == "completed"
        mock_transcriber_class.assert_called_once_with(api_key="sk-test", language="zh")

    @patch("api.tasks.worker._init_task_meta")
    @patch("api.tasks.worker.is_valid_video_url")
    @patch("api.tasks.worker.VideoDownloader")
    @patch("api.tasks.worker.AudioExtractor")
    @patch("api.tasks.worker._update_task_meta")
    def test_api_mode_no_key_raises(self, mock_update_meta, mock_extractor_class, mock_downloader_class, mock_is_valid, mock_init_meta, mock_settings, tmp_path):
        mock_settings.temp_dir = str(tmp_path / "temp")
        mock_settings.output_dir = str(tmp_path / "output")
        mock_settings.openai_api_key = None

        mock_is_valid.return_value = True

        mock_downloader = MagicMock()
        mock_downloader.download.return_value = str(tmp_path / "temp" / "video.mp4")
        mock_downloader_class.return_value = mock_downloader

        mock_extractor = MagicMock()
        mock_extractor.extract.return_value = str(tmp_path / "temp" / "audio.mp3")
        mock_extractor_class.return_value = mock_extractor

        with patch.object(process_video, "update_state"):
            with pytest.raises(ValueError, match="未配置 OPENAI_API_KEY"):
                process_video.run(
                    "task-123",
                    "https://www.facebook.com/watch?v=123",
                    {"use_local": False},
                )

    @patch("api.tasks.worker._init_task_meta")
    @patch("api.tasks.worker.is_valid_video_url")
    @patch("api.tasks.worker.VideoDownloader")
    @patch("api.tasks.worker._update_task_meta")
    def test_failure_triggers_retry(
        self,
        mock_update_meta,
        mock_downloader_class,
        mock_is_valid,
        mock_init_meta,
        mock_settings,
        tmp_path,
    ):
        mock_settings.temp_dir = str(tmp_path / "temp")
        mock_settings.output_dir = str(tmp_path / "output")

        mock_is_valid.return_value = True

        mock_downloader = MagicMock()
        mock_downloader.download.side_effect = Exception("Network error")
        mock_downloader_class.return_value = mock_downloader

        with patch.object(process_video, "update_state"):
            with patch.object(process_video, "retry", side_effect=Exception("Retry triggered")):
                with pytest.raises(Exception, match="Retry triggered"):
                    process_video.run(
                        "task-123",
                        "https://www.facebook.com/watch?v=123",
                        {},
                    )

                process_video.retry.assert_called_once()
