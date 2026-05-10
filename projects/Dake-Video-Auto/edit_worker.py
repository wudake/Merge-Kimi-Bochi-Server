#!/usr/bin/env python3
"""
剪辑工作进程 - 支持详细日志记录
"""
import json
import sys
import traceback
import logging
from pathlib import Path
from datetime import datetime

# 配置日志
sys.path.insert(0, "core")
from editor_advanced import AdvancedVideoEditor

def setup_logging(base_dir):
    """设置日志记录"""
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    log_file = logs_dir / f"edit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return log_file

def main():
    base_dir = Path(__file__).parent
    
    # 获取用户ID（单用户模式不传user_id）
    user_id = sys.argv[1] if len(sys.argv) > 1 else None
    
    if user_id:
        # 多用户模式
        user_dir = base_dir / "users" / user_id
        raw_dir = user_dir / "videos" / "raw"
        output_dir = user_dir / "output"
        config_file = user_dir / ".temp_config.json"
        result_file = user_dir / ".temp_edit_result.json"
        log_file = user_dir / "logs" / f"edit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    else:
        # 单用户模式（兼容旧版本）
        raw_dir = base_dir / "videos" / "raw"
        output_dir = base_dir / "output"
        config_file = base_dir / ".temp_config.json"
        result_file = base_dir / ".temp_edit_result.json"
        log_file = base_dir / "logs" / f"edit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # 确保目录存在
    raw_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    (base_dir / "logs").mkdir(exist_ok=True)
    
    # 设置日志
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("="*60)
    logger.info("🎬 视频剪辑任务启动")
    logger.info(f"📁 原始目录: {raw_dir}")
    logger.info(f"📁 输出目录: {output_dir}")
    logger.info(f"📝 日志文件: {log_file}")
    
    # 读取配置
    if not config_file.exists():
        error_msg = "未找到配置文件"
        logger.error(f"❌ {error_msg}")
        result = {"success": False, "error": error_msg, "logs": [error_msg]}
        result_file.write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
        return
    
    try:
        data = json.loads(config_file.read_text(encoding='utf-8'))
        note_id = data["note_id"]
        config = data.get("config", {})
        
        logger.info(f"📝 视频ID: {note_id}")
        logger.info(f"⚙️ 配置: {json.dumps(config, ensure_ascii=False, indent=2)}")
    except Exception as e:
        error_msg = f"读取配置失败: {str(e)}"
        logger.error(f"❌ {error_msg}")
        logger.error(traceback.format_exc())
        result = {"success": False, "error": error_msg, "logs": [error_msg]}
        result_file.write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
        return
    
    # 初始化编辑器
    editor = AdvancedVideoEditor(
        raw_dir=str(raw_dir),
        edited_dir=str(output_dir),
        assets_dir=str(base_dir / "assets"),
        logos_dir=str(base_dir / "assets" / "logos"),
        bgm_dir=str(base_dir / "assets" / "bgm")
    )
    
    # 查找视频文件
    video_path = editor.raw_dir / f"{note_id}.mp4"
    
    # 兼容抖音下载器的命名格式
    if not video_path.exists():
        video_path = editor.raw_dir / f"douyin_{note_id}.mp4"
        if video_path.exists():
            logger.info(f"🔍 找到抖音视频: {video_path.name}")
    
    if not video_path.exists():
        # 列出目录中的所有文件
        available_files = list(editor.raw_dir.glob("*.mp4"))
        available_names = [f.name for f in available_files]
        
        error_msg = f"原始视频不存在: {note_id}.mp4"
        detail_msg = f"目录中的文件: {available_names}" if available_names else "目录为空"
        logger.error(f"❌ {error_msg}")
        logger.error(f"📂 {detail_msg}")
        
        result = {
            "success": False, 
            "error": error_msg,
            "detail": detail_msg,
            "logs": [error_msg, detail_msg]
        }
        result_file.write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
        return
    
    logger.info(f"✅ 找到视频文件: {video_path}")
    
    # 执行剪辑
    try:
        logger.info("🚀 开始剪辑...")
        output = editor.edit_video(video_path, config)
        
        if output:
            logger.info(f"✅ 剪辑成功: {output}")
            result = {
                "success": True,
                "output_path": str(output),
                "output_name": Path(output).name
            }
        else:
            error_msg = "剪辑失败 (FFmpeg 返回错误)"
            logger.error(f"❌ {error_msg}")
            result = {
                "success": False, 
                "error": error_msg,
                "logs": [error_msg, "请检查 FFmpeg 是否正确安装"]
            }
    except Exception as e:
        error_msg = f"剪辑异常: {str(e)}"
        logger.error(f"❌ {error_msg}")
        logger.error(traceback.format_exc())
        
        # 读取日志文件内容
        log_content = ""
        try:
            if log_file.exists():
                log_content = log_file.read_text(encoding='utf-8')
        except:
            pass
        
        result = {
            "success": False,
            "error": error_msg,
            "traceback": traceback.format_exc(),
            "logs": log_content.split('\n')[-50:] if log_content else [error_msg]
        }
    
    # 保存结果
    result_file.write_text(
        json.dumps(result, ensure_ascii=False),
        encoding='utf-8'
    )
    logger.info("="*60)

if __name__ == "__main__":
    main()
