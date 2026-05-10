#!/usr/bin/env python3
"""
下载工作进程 - 支持单用户和多用户模式，目前仅支持小红书
"""
import asyncio
import json
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, "core")
from downloader_pw import XHSPlaywrightDownloader
from douyin_api_downloader import DouyinAPIDownloader


def detect_platform(url):
    """检测URL所属平台"""
    url_lower = url.lower()
    if any(domain in url_lower for domain in ['xiaohongshu.com', 'xhslink.com', 'xhscdn.com']):
        return 'xiaohongshu'
    elif any(domain in url_lower for domain in ['douyin.com', 'iesdouyin.com', 'v.douyin.com']):
        return 'douyin'
    return None


def main():
    base_dir = Path(__file__).parent
    
    # 获取用户ID（单用户模式不传user_id）
    user_id = sys.argv[1] if len(sys.argv) > 1 else None
    
    if user_id:
        # 多用户模式
        user_dir = base_dir / "users" / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        raw_dir = user_dir / "videos" / "raw"
        url_file = user_dir / ".temp_url.txt"
        result_file = user_dir / ".temp_result.json"
    else:
        # 单用户模式（兼容旧版本）
        raw_dir = base_dir / "videos" / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        url_file = base_dir / ".temp_url.txt"
        result_file = base_dir / ".temp_result.json"
    
    # 读取 URL
    if not url_file.exists():
        result = {"status": "error", "error": "未找到 URL 文件"}
        result_file.write_text(json.dumps(result))
        return
    
    url = url_file.read_text(encoding='utf-8').strip()
    
    # 检测平台
    platform = detect_platform(url)
    
    # 下载
    async def do_download():
        if platform == 'xiaohongshu':
            print(f"📱 识别平台: 小红书")
            dl = XHSPlaywrightDownloader(raw_dir=str(raw_dir), headless=True)
            return await dl.download(url)
        elif platform == 'douyin':
            print(f"📱 识别平台: 抖音")
            dl = DouyinAPIDownloader(raw_dir=str(raw_dir))
            return dl.download(url)
        else:
            return {"status": "error", "error": f"不支持的平台: {url}"}
    
    try:
        result = asyncio.run(do_download())
    except Exception as e:
        import traceback
        result = {"status": "error", "error": str(e), "traceback": traceback.format_exc()}
    
    # 保存结果
    result_file.write_text(
        json.dumps(result, ensure_ascii=False), 
        encoding='utf-8'
    )


if __name__ == "__main__":
    main()
