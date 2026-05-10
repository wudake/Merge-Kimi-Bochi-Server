"""
抖音视频下载器 - 使用 MeowLoad API
API 文档: https://docs.henghengmao.com/en/developer/media-downloader-api
"""
import requests
import json
from pathlib import Path


class DouyinAPIDownloader:
    """使用 MeowLoad API 下载抖音视频"""
    
    API_URL = "https://api.meowload.net/openapi/extract/post"
    API_KEY = "677046-5d0wi3dy0nru"
    
    def __init__(self, raw_dir="videos/raw"):
        self.raw_dir = Path(raw_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_video_id(self, url: str) -> str:
        """从抖音链接中提取视频 ID"""
        import re
        patterns = [
            r'/video/(\d+)',
            r'video/(\d+)',
            r'v\.douyin\.com/(\w+)',
            r'/share/video/(\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def download(self, url: str, filename: str = None) -> dict:
        """
        下载抖音视频
        
        Args:
            url: 抖音分享链接
            filename: 保存文件名（可选）
        
        Returns:
            dict: 下载结果
        """
        video_id = self.extract_video_id(url)
        if not video_id:
            print(f"❌ 无法解析抖音 URL: {url}")
            return {"status": "error", "error": "无效的抖音链接格式"}
        
        if not filename:
            filename = f"douyin_{video_id}.mp4"
        
        output_path = self.raw_dir / filename
        
        print(f"🚀 开始下载抖音视频: {url}")
        print(f"📌 Video ID: {video_id}")
        
        # 调用 MeowLoad API
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.API_KEY,
            "accept-language": "zh"
        }
        
        payload = {"url": url}
        
        try:
            response = requests.post(
                self.API_URL,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            # 处理错误响应
            if response.status_code != 200:
                error_data = response.json() if response.text else {"message": "未知错误"}
                error_msg = error_data.get("message", f"HTTP {response.status_code}")
                
                # 处理特定错误码
                if response.status_code == 401:
                    error_msg = "API Key 无效或已过期"
                elif response.status_code == 402:
                    error_msg = "API 额度已用完，请联系管理员充值"
                elif response.status_code == 400:
                    error_msg = f"提取失败: {error_msg}"
                
                print(f"❌ API 错误: {error_msg}")
                return {
                    "status": "error",
                    "error": error_msg,
                    "video_id": video_id,
                    "url": url
                }
            
            # 解析成功响应
            data = response.json()
            medias = data.get("medias", [])
            
            if not medias:
                print("❌ API 返回结果中没有媒体文件")
                return {
                    "status": "error",
                    "error": "未找到视频文件",
                    "video_id": video_id,
                    "url": url
                }
            
            # 获取第一个视频
            video_media = None
            for media in medias:
                if media.get("media_type") == "video":
                    video_media = media
                    break
            
            if not video_media:
                print("❌ 未找到视频类型的媒体")
                return {
                    "status": "error",
                    "error": "未找到视频文件",
                    "video_id": video_id,
                    "url": url
                }
            
            video_url = video_media.get("resource_url")
            if not video_url:
                print("❌ 视频下载链接为空")
                return {
                    "status": "error",
                    "error": "视频下载链接为空",
                    "video_id": video_id,
                    "url": url
                }
            
            print(f"📥 获取到视频链接: {video_url[:60]}...")
            
            # 下载视频文件
            download_headers = {}
            if video_media.get("headers"):
                download_headers = video_media["headers"]
            
            print(f"📥 开始下载视频文件...")
            video_response = requests.get(
                video_url,
                headers=download_headers,
                stream=True,
                timeout=120
            )
            video_response.raise_for_status()
            
            # 获取文件大小
            total_size = int(video_response.headers.get('content-length', 0))
            if total_size > 0:
                print(f"📦 文件大小: {total_size / 1024 / 1024:.2f} MB")
            
            # 保存文件
            with open(output_path, 'wb') as f:
                downloaded = 0
                for chunk in video_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
            
            # 验证文件
            if not output_path.exists() or output_path.stat().st_size == 0:
                print("❌ 下载的文件为空")
                return {
                    "status": "error",
                    "error": "下载失败，文件为空",
                    "video_id": video_id,
                    "url": url
                }
            
            file_size = output_path.stat().st_size / 1024 / 1024
            print(f"✅ 下载完成: {output_path} ({file_size:.2f} MB)")
            
            return {
                "status": "success",
                "note_id": f"douyin_{video_id}",
                "video_id": video_id,
                "url": url,
                "video_url": video_url,
                "output_path": str(output_path),
                "size_mb": round(file_size, 2),
                "caption": data.get("text", ""),
                "source": "douyin_api"
            }
            
        except requests.exceptions.Timeout:
            print("❌ API 请求超时")
            return {
                "status": "error",
                "error": "请求超时，请稍后重试",
                "video_id": video_id,
                "url": url
            }
        except requests.exceptions.RequestException as e:
            print(f"❌ 网络请求错误: {e}")
            return {
                "status": "error",
                "error": f"网络错误: {str(e)}",
                "video_id": video_id,
                "url": url
            }
        except Exception as e:
            import traceback
            print(f"❌ 未知错误: {e}")
            print(traceback.format_exc())
            return {
                "status": "error",
                "error": str(e),
                "video_id": video_id,
                "url": url
            }


# 便捷函数
def download_douyin_video(url: str, output_dir: str = "videos/raw") -> dict:
    """便捷函数：下载抖音视频"""
    dl = DouyinAPIDownloader(raw_dir=output_dir)
    return dl.download(url)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
        result = download_douyin_video(url)
        print("\n" + "="*50)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("Usage: python douyin_api_downloader.py <douyin_url>")
        print("Example: python douyin_api_downloader.py 'https://v.douyin.com/xxxxx'")
