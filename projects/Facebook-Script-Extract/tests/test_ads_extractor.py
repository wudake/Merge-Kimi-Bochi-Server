from unittest.mock import MagicMock, patch

import pytest

from src.ads_extractor import (
    FacebookAdsExtractor,
    _collect_urls,
    _guess_quality,
)


class TestFacebookAdsExtractor:
    def test_is_ads_library_url_true(self):
        assert FacebookAdsExtractor.is_ads_library_url(
            "https://www.facebook.com/ads/library/?id=1539922477140995"
        )
        assert FacebookAdsExtractor.is_ads_library_url(
            "https://facebook.com/ads/library/?id=123"
        )

    def test_is_ads_library_url_false(self):
        assert not FacebookAdsExtractor.is_ads_library_url(
            "https://www.facebook.com/watch?v=123"
        )
        assert not FacebookAdsExtractor.is_ads_library_url(
            "https://www.youtube.com/watch?v=123"
        )
        assert not FacebookAdsExtractor.is_ads_library_url("")

    def test_pick_best_prioritizes_hd(self):
        extractor = FacebookAdsExtractor()
        urls = [
            {"url": "http://fbcdn.net/sd.mp4", "quality": 360, "source": "cdn"},
            {"url": "http://fbcdn.net/hd.mp4", "quality": 720, "source": "cdn"},
            {"url": "http://fbcdn.net/watch", "quality": 0, "source": "watch"},
        ]
        best = extractor._pick_best(urls)
        assert best == "http://fbcdn.net/hd.mp4"

    def test_pick_best_prefers_cdn_over_watch(self):
        extractor = FacebookAdsExtractor()
        urls = [
            {"url": "http://fbcdn.net/sd.mp4", "quality": 360, "source": "cdn"},
            {"url": "https://facebook.com/watch/?v=123", "quality": 0, "source": "watch"},
        ]
        best = extractor._pick_best(urls)
        assert best == "http://fbcdn.net/sd.mp4"

    @patch("src.ads_extractor.sync_playwright")
    def test_extract_returns_video_url(self, mock_sync_pw, tmp_path):
        """Mock Playwright 全流程，验证能提取到视频 URL."""
        mock_response = MagicMock()
        mock_response.url = "https://video.fbsin1-1.fna.fbcdn.net/v/test_hd.mp4"

        mock_page = MagicMock()
        mock_page.goto = MagicMock()
        mock_page.wait_for_timeout = MagicMock()
        mock_page.locator.return_value.first.count.return_value = 0

        # 手动触发 on("response") 回调来模拟拦截到视频
        def fake_on(event, handler):
            if event == "response":
                handler(mock_response)

        mock_page.on = fake_on

        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page

        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context

        mock_pw = MagicMock()
        mock_pw.chromium.launch.return_value = mock_browser
        mock_sync_pw.return_value.__enter__.return_value = mock_pw

        extractor = FacebookAdsExtractor(headless=True)
        result = extractor.extract("https://www.facebook.com/ads/library/?id=123")
        assert result == mock_response.url

    @patch("src.ads_extractor.sync_playwright")
    def test_extract_raises_when_no_video_found(self, mock_sync_pw):
        mock_page = MagicMock()
        mock_page.on = MagicMock()
        mock_page.goto = MagicMock()
        mock_page.wait_for_timeout = MagicMock()
        mock_page.locator.return_value.first.count.return_value = 0

        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page

        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context

        mock_pw = MagicMock()
        mock_pw.chromium.launch.return_value = mock_browser
        mock_sync_pw.return_value.__enter__.return_value = mock_pw

        extractor = FacebookAdsExtractor(headless=True)
        with pytest.raises(RuntimeError, match="未从 Ads Library 页面提取到视频链接"):
            extractor.extract("https://www.facebook.com/ads/library/?id=123")

    def test_extract_import_error_without_playwright(self):
        with patch.dict("sys.modules", {"playwright.sync_api": None}):
            extractor = FacebookAdsExtractor()
            with pytest.raises(RuntimeError, match="playwright"):
                extractor.extract("https://www.facebook.com/ads/library/?id=123")


class TestGuessQuality:
    def test_guess_quality_1080(self):
        assert _guess_quality("http://cdn/test_1080.mp4") == 1080

    def test_guess_quality_720(self):
        assert _guess_quality("http://cdn/test_hd.mp4") == 720

    def test_guess_quality_360(self):
        assert _guess_quality("http://cdn/test_360p.mp4") == 360

    def test_guess_quality_unknown(self):
        assert _guess_quality("http://cdn/test.mp4") == 0


class TestCollectUrls:
    def test_collect_playable_url(self):
        storage = []
        data = {"playable_url": "http://fbcdn.net/video.mp4"}
        _collect_urls(data, storage)
        assert len(storage) == 1
        assert storage[0]["url"] == "http://fbcdn.net/video.mp4"

    def test_collect_playable_url_hd(self):
        storage = []
        data = {"playable_url_quality_hd": "http://fbcdn.net/video_hd.mp4"}
        _collect_urls(data, storage)
        assert len(storage) == 1
        assert storage[0]["quality"] == 720

    def test_collect_nested(self):
        storage = []
        data = {"a": {"b": {"playable_url": "http://fbcdn.net/nested.mp4"}}}
        _collect_urls(data, storage)
        assert len(storage) == 1

    def test_ignores_non_http(self):
        storage = []
        data = {"playable_url": "blob:http://fbcdn.net/video"}
        _collect_urls(data, storage)
        assert len(storage) == 0
