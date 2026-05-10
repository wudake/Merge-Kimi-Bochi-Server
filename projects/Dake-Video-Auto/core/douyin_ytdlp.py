"""
抖音视频下载器 v5.0 - yt-dlp + Cookie 方案
需要配置抖音 Cookie 才能使用
"""
import re
import json
import subprocess
from pathlib import Path


class DouyinYTDLP:
    """使用 yt-dlp + Cookie 下载抖音视频"""

    def __init__(self, raw_dir="videos/raw", cookies_file="cookies/douyin_cookies.txt"):
        self.raw_dir = Path(raw_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.cookies_file = Path(cookies_file)

    def extract_video_id(self, url):
        """提取视频 ID"""
        patterns = [
            r'/video/(\d+)',
            r'/share/video/(\d+)',
            r'modal_id=(\d+)',
            r'/note/(\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        if 'v.douyin.com' in url or 'iesdouyin.com' in url:
            return None
        return None

    def download(self, url, filename=None):
        """下载抖音视频"""
        import requests
        
        # 处理短链接
        final_url = url
        video_id = self.extract_video_id(url)
        
        if not video_id and ('v.douyin.com' in url or 'iesdouyin.com' in url):
            print(f"🔗 解析短链接...")
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X)",
                    "Accept": "text/html",
                }
                resp = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
                final_url = resp.url
                video_id = self.extract_video_id(final_url)
                print(f"📍 真实链接: {final_url}")
            except Exception as e:
                print(f"⚠️ 短链接解析失败: {e}")
        
        if not video_id:
            return {"status": "error", "error": "无法解析视频 ID"}
        
        if not filename:
            filename = f"douyin_{video_id}.mp4"
        
        output_path = self.raw_dir / filename
        
        print(f"🚀 开始下载抖音视频: {video_id}")
        
        # 检查 Cookie 文件
        if not self.cookies_file.exists():
            error_msg = f"Cookie 文件不存在: {self.cookies_file}\n请从浏览器导出抖音 Cookie 并保存到该路径"
            print(f"❌ {error_msg}")
            return {
                "status": "error",
                "error": error_msg,
                "video_id": video_id
            }
        
        print(f"🍪 使用 Cookie: {self.cookies_file}")
        
        # 构建 yt-dlp 命令
        output_template = str(self.raw_dir / f"douyin_{video_id}.%(ext)s")
        
        cmd = [
            "yt-dlp",
            "--cookies", str(self.cookies_file),
            "--output", output_template,
            "--format", "best",  # 最佳质量
            "--no-warnings",
            "--user-agent", "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15",
            "--referer", "https://www.douyin.com/",
            "--add-header", "Accept:*/*",
            "--add-header", "Accept-Language:zh-CN,zh;q=0.9",
            "--merge-output-format", "mp4",
            "--no-check-certificates",
            final_url
        ]
        
        print(f"⏳ 执行下载...")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180,
                encoding='utf-8'
            )
            
            # 检查输出
            stdout = result.stdout
            stderr = result.stderr
            
            if result.returncode == 0:
                # 查找下载的文件
                downloaded_file = None
                for f in self.raw_dir.glob(f"douyin_{video_id}*"):
                    if f.suffix in ['.mp4', '.webm', '.mkv']:
                        downloaded_file = f
                        break
                
                if downloaded_file:
                    # 确保是 mp4 格式
                    if downloaded_file.suffix != '.mp4':
                        mp4_path = downloaded_file.with_suffix('.mp4')
                        downloaded_file.rename(mp4_path)
                        downloaded_file = mp4_path
                    
                    file_size = downloaded_file.stat().st_size / 1024 / 1024
                    print(f"✅ 下载成功: {downloaded_file.name} ({file_size:.2f} MB)")
                    
                    return {
                        "status": "success",
                        "note_id": video_id,
                        "video_id": video_id,
                        "url": url,
                        "output_path": str(downloaded_file),
                        "output_name": downloaded_file.name,
                        "size_mb": file_size,
                        "platform": "douyin"
                    }
                else:
                    print(f"⚠️ 下载完成但未找到文件")
                    return {
                        "status": "error",
                        "error": "下载完成但未找到文件",
                        "stdout": stdout,
                        "stderr": stderr
                    }
            else:
                error_msg = self._parse_error(stderr)
                print(f"❌ 下载失败: {error_msg}")
                return {
                    "status": "error",
                    "error": error_msg,
                    "stdout": stdout,
                    "stderr": stderr,
                    "video_id": video_id
                }
                
        except subprocess.TimeoutExpired:
            print(f"❌ 下载超时")
            return {"status": "error", "error": "下载超时（超过3分钟）"}
        except Exception as e:
            print(f"❌ 下载异常: {e}")
            return {"status": "error", "error": str(e)}

    def _parse_error(self, stderr):
        """解析错误信息"""
        if "Forbidden" in stderr or "403" in stderr:
            return "Cookie 已过期或无效，请重新导出"
        elif "Unable to extract" in stderr:
            return "无法解析视频信息，请检查链接是否正确"
        elif "Video unavailable" in stderr:
            return "视频不可用或已被删除"
        elif "Private video" in stderr:
            return "视频是私密的，无法下载"
        elif "Sign in" in stderr or "login" in stderr.lower():
            return "需要登录，请检查 Cookie 文件"
        else:
            # 返回主要错误信息
            lines = stderr.strip().split('\n')
            for line in lines:
                if 'error' in line.lower() or 'Error' in line:
                    return line.strip()
            return stderr[:200] if stderr else "未知错误"


def download_douyin_video(url, output_dir="videos/raw", cookies_file="cookies/douyin_cookies.txt"):
    """便捷函数"""
    dl = DouyinYTDLP(output_dir, cookies_file)
    return dl.download(url)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
        result = download_douyin_video(url)
        print("\n" + "="*50)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("Usage: python douyin_ytdlp.py <douyin_url>")
        print("Example: python douyin_ytdlp.py https://www.douyin.com/video/1234567890")
        print("\n注意：需要先在 cookies/douyin_cookies.txt 中配置 Cookie")
