"""
抖音视频下载器 v2.0 - 优化版
解决片头广告问题，获取真实视频
"""
import re
import json
import asyncio
from pathlib import Path
from urllib.parse import unquote
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# Playwright 自带 Chromium 路径
import glob as _glob
_playwright_chrome = _glob.glob("/ms-playwright/chromium-*/chrome-linux64/chrome")
CHROME_PATH = _playwright_chrome[0] if _playwright_chrome else "/usr/bin/google-chrome"


class DouyinPlaywrightDownloader:
    """优化的抖音视频下载器"""

    def __init__(self, raw_dir="videos/raw", headless=True):
        self.raw_dir = Path(raw_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.headless = headless

    def extract_video_id(self, url):
        """提取抖音视频 ID"""
        patterns = [
            r'/video/(\d+)',
            r'/share/video/(\d+)',
            r'video/(\d+)',
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

    async def download(self, url, filename=None):
        """下载抖音视频 - 优化版"""
        # 处理短链接
        final_url = url
        video_id = self.extract_video_id(url)
        
        if not video_id and ('v.douyin.com' in url or 'iesdouyin.com' in url):
            print(f"🔗 检测到短链接，正在解析...")
            try:
                import requests
                headers = {
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
                }
                resp = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
                final_url = resp.url
                video_id = self.extract_video_id(final_url)
                print(f"📍 真实链接: {final_url[:80]}...")
            except Exception as e:
                print(f"⚠️ 短链接解析失败: {e}")
        
        if not video_id:
            print(f"❌ 无法解析 URL: {url}")
            return {"status": "error", "error": "无法解析 URL"}

        if not filename:
            filename = f"douyin_{video_id}.mp4"

        output_path = self.raw_dir / filename

        print(f"🚀 开始下载抖音视频: {url}")
        print(f"📌 Video ID: {video_id}")

        # 存储所有捕获的视频信息
        captured_videos = []  # [(url, size, type), ...]
        api_data = {}  # 存储从API获取的数据

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                executable_path=CHROME_PATH,
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process'
                ]
            )

            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1280, 'height': 800}
            )

            # 反检测脚本
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en'] });
            """)

            page = await context.new_page()

            # 监听响应 - 捕获视频和API数据
            async def handle_response(response):
                resp_url = response.url
                
                # 捕获视频请求
                if any(ext in resp_url.lower() for ext in ['.mp4', '.mov', '.m3u8']):
                    if any(domain in resp_url for domain in ['douyin', 'bytedance', 'iesdouyin', 'douyinvod']):
                        try:
                            headers = response.headers
                            content_length = headers.get('content-length', '0')
                            size = int(content_length) if content_length else 0
                            
                            # 判断视频类型
                            vtype = 'unknown'
                            if 'hd' in resp_url.lower():
                                vtype = 'hd'
                            elif any(x in resp_url.lower() for x in ['_hd', '1080', '720']):
                                vtype = 'hd'
                            elif any(x in resp_url.lower() for x in ['preview', 'cover']):
                                vtype = 'preview'
                            
                            captured_videos.append((resp_url, size, vtype))
                            size_mb = size / 1024 / 1024 if size > 0 else 0
                            print(f"🎯 发现视频: {vtype} | {size_mb:.2f}MB | {resp_url[:50]}...")
                        except:
                            captured_videos.append((resp_url, 0, 'unknown'))
                            print(f"🎯 发现视频: unknown | {resp_url[:50]}...")
                
                # 捕获API响应中的视频数据
                if '/aweme/v1/web/aweme/detail/' in resp_url or '/aweme/v2/comment/list/' in resp_url:
                    try:
                        text = await response.text()
                        data = json.loads(text)
                        api_data.update(data)
                    except:
                        pass

            page.on("response", handle_response)

            try:
                print("⏳ 正在加载页面...")
                await page.goto(final_url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)

                # 尝试点击播放按钮触发真实视频加载
                print("▶️  尝试点击播放按钮...")
                play_selectors = [
                    '.xgplayer-play',
                    '[class*="play"]',
                    'xg-video-container',
                    'video',
                    '[data-e2e="video-play"]',
                    '.player-container'
                ]
                
                for selector in play_selectors:
                    try:
                        elem = await page.query_selector(selector)
                        if elem:
                            await elem.click(force=True)
                            print(f"   已点击: {selector}")
                            await asyncio.sleep(3)
                            break
                    except:
                        continue

                # 滚动触发更多加载
                print("⏳ 等待视频加载...")
                await page.evaluate("window.scrollBy(0, 300)")
                await asyncio.sleep(3)
                
                # 再次点击确保播放
                try:
                    video_elem = await page.query_selector('video')
                    if video_elem:
                        await video_elem.click(force=True)
                        await asyncio.sleep(2)
                except:
                    pass

                # 从页面源码中提取 render 数据（包含真实视频地址）
                print("🔍 提取页面数据...")
                content = await page.content()
                
                # 方法1: SSR_HYDRATED_DATA
                render_data_match = re.search(r'<script[^>]*>window\._SSR_HYDRATED_DATA\s*=\s*({.*?})</script>', content, re.DOTALL)
                if render_data_match:
                    try:
                        render_data = json.loads(render_data_match.group(1))
                        self._extract_videos_from_data(render_data, captured_videos)
                    except Exception as e:
                        print(f"   SSR数据解析失败: {e}")

                # 方法2: 查找 render data 的其他形式
                render_data_patterns = [
                    r'<script[^>]*>window\._SSR_HYDRATED_DATA\s*=\s*({.+?})</script>',
                    r'<script[^>]*>window\.__INITIAL_STATE__\s*=\s*({.+?})</script>',
                    r'<script[^>]*>window\.__DATA__\s*=\s*({.+?})</script>',
                ]
                
                for pattern in render_data_patterns:
                    matches = re.findall(pattern, content, re.DOTALL)
                    for match in matches:
                        try:
                            data = json.loads(match)
                            self._extract_videos_from_data(data, captured_videos)
                        except:
                            pass

                # 方法3: 从页面中查找 aweme/detail API 的数据
                detail_match = re.search(r'"aweme_detail":\s*({.+?"anchor_info")', content, re.DOTALL)
                if detail_match:
                    try:
                        detail_data = json.loads(detail_match.group(1) + ']}')
                        self._extract_videos_from_data({"detail": detail_data}, captured_videos)
                    except:
                        pass

                # 等待更多视频请求
                await asyncio.sleep(5)
                
            except PlaywrightTimeout:
                print("⚠️ 页面加载超时，但可能已获取到视频")
            except Exception as e:
                print(f"❌ 页面访问出错: {e}")

            await browser.close()

        # 选择最佳视频
        video_url = self._select_best_video(captured_videos)
        
        if not video_url:
            print("❌ 未找到有效的视频地址")
            print(f"   捕获的视频数量: {len(captured_videos)}")
            for i, (url, size, vtype) in enumerate(captured_videos[:5]):
                print(f"   #{i+1}: {vtype} - {url[:60]}...")
            return {"video_id": video_id, "url": url, "status": "no_video_found"}

        print(f"\n📥 开始下载视频...")
        print(f"🔗 选中URL: {video_url[:80]}...")

        # 下载视频
        import requests
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Referer': 'https://www.douyin.com/',
                'Accept': '*/*',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Range': 'bytes=0-'
            }
            
            # 先获取视频信息
            head_resp = requests.head(video_url, headers=headers, timeout=10)
            total_size = int(head_resp.headers.get('content-length', 0))
            
            if total_size > 0:
                print(f"📦 文件大小: {total_size / 1024 / 1024:.2f} MB")
                
                if total_size < 1024 * 1024:  # 小于1MB可能是广告
                    print(f"⚠️ 文件过小 ({total_size/1024:.1f}KB)，可能是预览/广告")
                    # 尝试查找更大的视频
                    alt_url = self._find_larger_video(captured_videos, total_size)
                    if alt_url:
                        print(f"🔄 尝试下载更大的视频...")
                        video_url = alt_url
                        head_resp = requests.head(video_url, headers=headers, timeout=10)
                        total_size = int(head_resp.headers.get('content-length', 0))
                        print(f"📦 新文件大小: {total_size / 1024 / 1024:.2f} MB")

            # 流式下载
            response = requests.get(video_url, headers=headers, stream=True, timeout=120)
            response.raise_for_status()

            with open(output_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

            file_size = output_path.stat().st_size / 1024 / 1024
            
            if file_size > 0.5:  # 正常视频应该大于0.5MB
                print(f"✅ 下载完成: {output_path} ({file_size:.2f} MB)")
                return {
                    "note_id": video_id,
                    "url": url,
                    "video_url": video_url,
                    "output_path": str(output_path),
                    "status": "success",
                    "size_mb": file_size,
                    "platform": "douyin"
                }
            else:
                print(f"⚠️ 下载的文件过小 ({file_size:.2f}MB)，可能是广告")
                output_path.unlink(missing_ok=True)
                return {
                    "status": "error",
                    "error": f"下载的文件过小 ({file_size:.2f}MB)，可能是广告/预览",
                    "video_id": video_id
                }

        except Exception as e:
            print(f"❌ 下载失败: {e}")
            return {"video_id": video_id, "url": url, "status": "download_failed", "error": str(e)}

    def _extract_videos_from_data(self, data, captured_list):
        """从数据结构中提取视频URL"""
        urls_found = []
        
        def traverse(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, str):
                        # 查找视频URL
                        if any(ext in value.lower() for ext in ['.mp4', '.mov']):
                            if any(domain in value for domain in ['douyin', 'bytedance', 'iesdouyin']):
                                clean_url = unquote(value.replace('\\u002F', '/').replace('\\/', '/'))
                                if clean_url not in urls_found:
                                    urls_found.append(clean_url)
                                    # 根据URL特征判断类型
                                    vtype = 'hd' if 'hd' in clean_url.lower() or '720' in clean_url or '1080' in clean_url else 'normal'
                                    captured_list.append((clean_url, 0, vtype))
                                    print(f"📦 数据提取: {vtype} | {clean_url[:60]}...")
                    elif isinstance(value, (dict, list)):
                        traverse(value)
            elif isinstance(obj, list):
                for item in obj:
                    traverse(item)
        
        traverse(data)

    def _select_best_video(self, captured_videos):
        """选择最佳视频URL"""
        if not captured_videos:
            return None
        
        # 去重
        seen = set()
        unique_videos = []
        for url, size, vtype in captured_videos:
            base_url = url.split('?')[0]
            if base_url not in seen:
                seen.add(base_url)
                unique_videos.append((url, size, vtype))
        
        print(f"\n📊 找到 {len(unique_videos)} 个唯一视频:")
        for i, (url, size, vtype) in enumerate(unique_videos[:10]):
            size_str = f"{size/1024/1024:.1f}MB" if size > 0 else "未知"
            print(f"   #{i+1}: {vtype} | {size_str} | {url[:50]}...")
        
        # 优先选择策略：
        # 1. 有大小信息的，选最大的
        # 2. 标记为 HD 的
        # 3. URL 中包含 hd/1080/720 的
        
        videos_with_size = [(url, size, vtype) for url, size, vtype in unique_videos if size > 0]
        
        if videos_with_size:
            # 按大小排序，选择最大的
            videos_with_size.sort(key=lambda x: x[1], reverse=True)
            best = videos_with_size[0]
            print(f"\n✅ 选择最大文件: {best[1]/1024/1024:.2f}MB")
            return best[0]
        
        # 没有大小信息，按类型选择
        for url, size, vtype in unique_videos:
            if vtype == 'hd':
                print(f"\n✅ 选择 HD 视频")
                return url
        
        # 最后选择第一个
        if unique_videos:
            print(f"\n✅ 选择第一个可用视频")
            return unique_videos[0][0]
        
        return None

    def _find_larger_video(self, captured_videos, current_size):
        """查找比当前更大的视频"""
        for url, size, vtype in captured_videos:
            if size > current_size * 2:  # 大2倍以上
                return url
        return None


async def download_douyin_video(url, output_dir="videos/raw", headless=True):
    """便捷函数"""
    dl = DouyinPlaywrightDownloader(output_dir, headless)
    return await dl.download(url)


if __name__ == "__main__":
    import sys
    import os

    has_display = os.environ.get('DISPLAY') is not None

    if len(sys.argv) > 1:
        url = sys.argv[1]
        headless = not has_display
        if headless:
            print("🖥️  无图形界面，使用 headless 模式")
        else:
            print("🖥️  检测到图形界面，显示浏览器窗口")

        result = asyncio.run(download_douyin_video(url, headless=headless))
        print("\n" + "="*50)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("Usage: python douyin_downloader.py <douyin_url>")
        print("Example: python douyin_downloader.py https://www.douyin.com/video/1234567890")
