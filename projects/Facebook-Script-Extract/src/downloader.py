import socket
from pathlib import Path
from urllib.parse import urlparse

import requests
import yt_dlp

from .ads_extractor import FacebookAdsExtractor

# 强制使用 IPv4（避免容器环境 IPv6 不可达导致连接失败）
_orig_getaddrinfo = socket.getaddrinfo

def _getaddrinfo_ipv4_only(host, port, family=0, type=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)

socket.getaddrinfo = _getaddrinfo_ipv4_only


class VideoDownloader:
    def __init__(self, temp_dir: str = "./temp"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self._ads_extractor = FacebookAdsExtractor(headless=True)

    def download(self, url: str) -> str:
        # Facebook Ads Library 需要特殊处理
        if FacebookAdsExtractor.is_ads_library_url(url):
            return self._download_ads_library(url)
        return self._download_ytdlp(url)

    def _download_ytdlp(self, url: str) -> str:
        output_template = str(self.temp_dir / "%(id)s.%(ext)s")
        ydl_opts = {
            'format': 'best[height<=720][ext=mp4]/best[height<=720]/best',
            'merge_output_format': 'mp4',
            'outtmpl': output_template,
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 60,
            'retries': 5,
            'fragment_retries': 5,
            'file_access_retries': 5,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_id = info.get('id', 'unknown')
            # 找到下载的文件
            for f in self.temp_dir.iterdir():
                if f.stem == video_id and f.suffix in ('.mp4', '.webm', '.mkv'):
                    return str(f)
        raise FileNotFoundError("未找到下载的视频文件")

    def _download_ads_library(self, url: str) -> str:
        """从 Facebook Ads Library 下载广告视频."""
        video_url = self._ads_extractor.extract(url)

        # 如果是 watch 页链接，回退到 yt_dlp
        if "/watch/?v=" in video_url:
            return self._download_ytdlp(video_url)

        # 直链下载：从 URL 路径中提取文件名，去掉查询参数
        path = urlparse(video_url).path
        filename = Path(path).name or f"ad_{hash(video_url) & 0xFFFFFFFF}.mp4"
        if not filename.endswith('.mp4'):
            filename += '.mp4'
        # 避免文件名过长（Linux 限制 255 字节）
        if len(filename) > 200:
            filename = f"ad_{hash(video_url) & 0xFFFFFFFF}.mp4"
        output_path = self.temp_dir / filename

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Referer": "https://www.facebook.com/",
        }
        response = requests.get(video_url, headers=headers, stream=True, timeout=120)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        return str(output_path)
