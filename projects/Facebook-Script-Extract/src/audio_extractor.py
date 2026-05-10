import os
import subprocess
from pathlib import Path


class AudioExtractor:
    def __init__(self, temp_dir: str = "./temp"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def extract(self, video_path: str) -> str:
        video = Path(video_path)
        audio_path = self.temp_dir / f"{video.stem}.mp3"
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vn",
            "-acodec", "libmp3lame",
            "-q:a", "2",
            "-y",
            str(audio_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"音频提取失败: {result.stderr}")
        return str(audio_path)
