import json
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None


class FacebookAdsExtractor:
    """从 Facebook Ads Library 页面提取视频直链."""

    def __init__(self, headless: bool = True, timeout_ms: int = 15000):
        self.headless = headless
        self.timeout_ms = timeout_ms
        self._playwright = None

    def extract(self, ad_url: str) -> str:
        """提取 Ads Library 广告页中的最佳视频 URL.

        返回可直接下载的 MP4 直链或 watch 页链接.
        """
        if sync_playwright is None:
            raise RuntimeError(
                "提取 Facebook Ads Library 视频需要 playwright. "
                "请安装: pip install playwright && playwright install chromium"
            )

        video_urls: list[dict] = []
        watch_ids: set[str] = set()

        def handle_response(response):
            url = response.url

            # GraphQL API: 包含 playable_url
            if "/api/graphql/" in url:
                try:
                    body = response.body().decode("utf-8", errors="ignore")
                    for line in body.strip().split("\n"):
                        if not line:
                            continue
                        data = json.loads(line)
                        _collect_urls(data, video_urls)
                except Exception:
                    pass

            # fbcdn CDN 直链
            if ".mp4" in url and "fbcdn" in url:
                video_urls.append({
                    "url": url,
                    "quality": _guess_quality(url),
                    "source": "cdn",
                })

            # video/unified_cvc API: 提取 vi (video ID)
            if "facebook.com/video/unified_cvc" in url:
                try:
                    body = response.body().decode("utf-8", errors="ignore")
                    match = re.search(r'"vi":\s*"?(\d+)"?', body)
                    if match:
                        watch_ids.add(match.group(1))
                except Exception:
                    pass

        with sync_playwright() as p:  # type: ignore[misc]
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
            )
            page = context.new_page()
            page.on("response", handle_response)

            page.goto(ad_url, wait_until="networkidle", timeout=self.timeout_ms)

            # 尝试点击播放按钮触发视频加载
            try:
                selectors = [
                    'video',
                    '[data-testid="play-button"]',
                    '[aria-label*="Play"]',
                    'div[role="button"]',
                ]
                for sel in selectors:
                    loc = page.locator(sel).first
                    if loc.count() > 0:
                        loc.click(timeout=3000)
                        page.wait_for_timeout(2000)
                        break
            except Exception:
                pass

            # 额外等待更多网络请求
            page.wait_for_timeout(3000)
            browser.close()

        # 从 watch IDs 构造 watch 页链接（yt_dlp 可能能处理 watch 页）
        for vid in watch_ids:
            video_urls.append({
                "url": f"https://www.facebook.com/watch/?v={vid}",
                "quality": 0,
                "source": "watch",
            })

        if not video_urls:
            raise RuntimeError("未从 Ads Library 页面提取到视频链接")

        return self._pick_best(video_urls)

    @staticmethod
    def _pick_best(urls: list[dict]) -> str:
        """优先选 HD > SD > watch 页."""
        def sort_key(item):
            quality = item.get("quality", 0)
            source = item.get("source", "")
            # CDN 直链优于 watch 页
            source_score = 2 if source == "cdn" else 1 if source == "graphql" else 0
            return (quality, source_score)

        urls.sort(key=sort_key, reverse=True)
        return urls[0]["url"]

    @staticmethod
    def is_ads_library_url(url: str) -> bool:
        """判断是否为 Facebook Ads Library URL."""
        parsed = urlparse(url)
        return (
            parsed.netloc in ("facebook.com", "www.facebook.com", "m.facebook.com")
            and "/ads/library/" in parsed.path
        )


def _guess_quality(url: str) -> int:
    """从 URL 猜测视频质量."""
    url_lower = url.lower()
    if "1080" in url_lower or "1080p" in url_lower:
        return 1080
    if "720" in url_lower or "720p" in url_lower or "hd" in url_lower:
        return 720
    if "480" in url_lower or "480p" in url_lower:
        return 480
    if "360" in url_lower or "360p" in url_lower:
        return 360
    return 0


def _collect_urls(obj, storage: list):
    """递归从 Facebook GraphQL 响应中提取 playable_url."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("playable_url", "playable_url_quality_hd") and isinstance(v, str) and v.startswith("http"):
                storage.append({
                    "url": v,
                    "quality": 720 if "hd" in k else 0,
                    "source": "graphql",
                })
            else:
                _collect_urls(v, storage)
    elif isinstance(obj, list):
        for item in obj:
            _collect_urls(item, storage)
