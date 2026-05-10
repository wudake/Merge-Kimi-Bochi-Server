"""
抖音视频下载器 v3.0 - 移动端 API 方案
绕过网页版限制，使用移动端接口
"""
import re
import json
import asyncio
import hashlib
import time
import random
from pathlib import Path
from urllib.parse import unquote, parse_qs, urlparse


class DouyinMobileDownloader:
    """使用移动端 API 下载抖音视频"""

    # 移动端 API 配置
    API_ENDPOINT = "https://www.iesdouyin.com/aweme/v1/web/aweme/detail/"
    USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.25"
    
    def __init__(self, raw_dir="videos/raw"):
        self.raw_dir = Path(raw_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)

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
        
        # 短链接处理
        if 'v.douyin.com' in url or 'iesdouyin.com' in url:
            return None
        return None

    def generate_params(self, video_id):
        """生成请求参数（模拟移动端签名）"""
        # 基础参数
        params = {
            "device_platform": "webapp",
            "aid": "6383",
            "channel": "channel_pc_web",
            "aweme_id": video_id,
            "pc_client_type": "1",
            "version_code": "170400",
            "version_name": "17.4.0",
            "cookie_enabled": "true",
            "screen_width": "1920",
            "screen_height": "1080",
            "browser_language": "zh-CN",
            "browser_platform": "MacIntel",
            "browser_name": "Chrome",
            "browser_version": "120.0.0.0",
            "browser_online": "true",
            "engine_name": "Blink",
            "engine_version": "120.0.0.0",
            "os_name": "Mac+OS",
            "os_version": "10.15.7",
            "cpu_core_num": "8",
            "device_memory": "8",
            "platform": "PC",
            "downlink": "10",
            "effective_type": "4g",
            "round_trip_time": "50",
            "webid": str(random.randint(10000000000000000000, 99999999999999999999)),
            "msToken": self._generate_ms_token(),
        }
        return params

    def _generate_ms_token(self):
        """生成 msToken"""
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        return ''.join(random.choice(chars) for _ in range(107))

    def _generate_ttwid(self):
        """生成 ttwid cookie"""
        import requests
        
        try:
            url = "https://ttwid.bytedance.com/ttwid/union/register/"
            headers = {
                "User-Agent": self.USER_AGENT,
                "Content-Type": "application/json",
            }
            data = {
                "region": "cn",
                "aid": 6383,
                "needFid": False,
                "service": "www.iesdouyin.com",
                "migrate_info": {"ticket": "", "source": "node"},
                "cbUrlProtocol": "https",
                "union": True
            }
            
            resp = requests.post(url, headers=headers, json=data, timeout=10)
            for cookie in resp.cookies:
                if cookie.name == "ttwid":
                    return cookie.value
        except Exception as e:
            print(f"生成 ttwid 失败: {e}")
        
        return None

    def get_video_info(self, video_id):
        """获取视频信息"""
        import requests
        
        params = self.generate_params(video_id)
        
        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": f"https://www.douyin.com/video/{video_id}",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
        }
        
        # 生成 ttwid
        ttwid = self._generate_ttwid()
        if ttwid:
            headers["Cookie"] = f"ttwid={ttwid}"
        
        try:
            url = f"{self.API_ENDPOINT}?{self._dict_to_query(params)}"
            print(f"🔍 请求 API: {url[:80]}...")
            
            resp = requests.get(url, headers=headers, timeout=15)
            
            if resp.status_code == 200:
                data = resp.json()
                return data
            else:
                print(f"❌ API 请求失败: {resp.status_code}")
                print(f"   响应: {resp.text[:200]}")
                return None
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return None

    def _dict_to_query(self, params):
        """字典转查询字符串"""
        from urllib.parse import urlencode
        return urlencode(params)

    def parse_video_urls(self, data):
        """从 API 响应中解析视频 URL"""
        urls = []
        
        try:
            aweme = data.get("aweme_detail", {})
            if not aweme:
                aweme = data.get("aweme_list", [{}])[0]
            
            video_info = aweme.get("video", {})
            
            # 播放地址
            play_addr = video_info.get("play_addr", {})
            if play_addr:
                # URL 列表
                url_list = play_addr.get("url_list", [])
                for url in url_list:
                    if url and url not in urls:
                        urls.append(url)
                
                # URI 构建 URL
                uri = play_addr.get("uri", "")
                if uri:
                    # 构建播放地址
                    hd_url = f"https://www.iesdouyin.com/aweme/v1/play/?video_id={uri}&ratio=1080p"
                    if hd_url not in urls:
                        urls.append(hd_url)
            
            # 下载地址（无水印）
            download_addr = video_info.get("download_addr", {})
            if download_addr:
                url_list = download_addr.get("url_list", [])
                for url in url_list:
                    if url and url not in urls:
                        urls.append(url)
            
            # 动态封面视频
            dynamic_cover = video_info.get("dynamic_cover", {})
            if dynamic_cover:
                url_list = dynamic_cover.get("url_list", [])
                for url in url_list:
                    if url and url not in urls:
                        urls.append(url)
                        
        except Exception as e:
            print(f"解析视频 URL 失败: {e}")
        
        return urls

    def download(self, url, filename=None):
        """下载抖音视频"""
        import requests
        
        # 处理短链接
        final_url = url
        video_id = self.extract_video_id(url)
        
        if not video_id:
            print(f"🔗 检测到短链接，解析中...")
            try:
                headers = {"User-Agent": self.USER_AGENT}
                resp = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
                final_url = resp.url
                video_id = self.extract_video_id(final_url)
                print(f"📍 真实链接: {final_url}")
            except Exception as e:
                print(f"❌ 短链接解析失败: {e}")
                return {"status": "error", "error": str(e)}
        
        if not video_id:
            return {"status": "error", "error": "无法解析视频 ID"}
        
        if not filename:
            filename = f"douyin_{video_id}.mp4"
        
        output_path = self.raw_dir / filename
        
        print(f"🚀 开始下载抖音视频")
        print(f"📌 Video ID: {video_id}")
        
        # 获取视频信息
        print("🔍 获取视频信息...")
        data = self.get_video_info(video_id)
        
        if not data:
            return {"status": "error", "error": "获取视频信息失败"}
        
        # 检查状态
        status_code = data.get("status_code", 0)
        if status_code != 0:
            error_msg = data.get("status_msg", "未知错误")
            print(f"❌ API 错误: {error_msg}")
            return {"status": "error", "error": error_msg}
        
        # 解析视频 URL
        video_urls = self.parse_video_urls(data)
        
        if not video_urls:
            print("❌ 未找到视频地址")
            return {"status": "error", "error": "未找到视频地址"}
        
        print(f"📊 找到 {len(video_urls)} 个视频地址")
        for i, vurl in enumerate(video_urls[:3]):
            print(f"   #{i+1}: {vurl[:60]}...")
        
        # 选择最佳视频（第一个通常是最高质量）
        video_url = video_urls[0]
        
        # 下载视频
        print(f"\n📥 开始下载...")
        
        try:
            headers = {
                "User-Agent": self.USER_AGENT,
                "Accept": "*/*",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Range": "bytes=0-",
            }
            
            # 检查文件大小
            head_resp = requests.head(video_url, headers=headers, timeout=10)
            total_size = int(head_resp.headers.get("content-length", 0))
            
            if total_size > 0:
                print(f"📦 文件大小: {total_size / 1024 / 1024:.2f} MB")
            
            # 下载
            resp = requests.get(video_url, headers=headers, stream=True, timeout=120)
            resp.raise_for_status()
            
            with open(output_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = output_path.stat().st_size / 1024 / 1024
            
            # 获取视频信息
            aweme = data.get("aweme_detail", {})
            desc = aweme.get("desc", "")
            author = aweme.get("author", {}).get("nickname", "")
            
            print(f"✅ 下载完成!")
            print(f"   文件: {output_path}")
            print(f"   大小: {file_size:.2f} MB")
            print(f"   作者: {author}")
            print(f"   描述: {desc[:50]}..." if len(desc) > 50 else f"   描述: {desc}")
            
            return {
                "status": "success",
                "video_id": video_id,
                "url": url,
                "video_url": video_url,
                "output_path": str(output_path),
                "size_mb": file_size,
                "author": author,
                "desc": desc,
                "platform": "douyin"
            }
            
        except Exception as e:
            print(f"❌ 下载失败: {e}")
            return {"status": "error", "error": str(e)}


def download_douyin_video(url, output_dir="videos/raw"):
    """便捷函数"""
    dl = DouyinMobileDownloader(output_dir)
    return dl.download(url)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
        result = download_douyin_video(url)
        print("\n" + "="*50)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("Usage: python douyin_mobile_downloader.py <douyin_url>")
        print("Example: python douyin_mobile_downloader.py https://www.douyin.com/video/1234567890")
