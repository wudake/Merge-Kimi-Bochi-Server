import pytest

from src.utils import extract_video_id, is_valid_facebook_url, is_valid_video_url


class TestIsValidVideoUrl:
    """测试通用视频 URL 验证函数"""

    @pytest.mark.parametrize(
        "url",
        [
            # Facebook URLs
            "https://www.facebook.com/watch?v=123456789",
            "http://facebook.com/watch?v=abc123",
            "https://facebook.com/share/v/xyz789/",
            "https://fb.watch/shortcode123",
            "https://www.facebook.com/mypage/videos/987654321",
            "https://www.facebook.com/groups/mygroup/posts/555666777",
            # YouTube URLs
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "http://youtube.com/watch?v=abc123",
            "https://youtube.com/shorts/Shorts123",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
            "https://www.youtube.com/v/dQw4w9WgXcQ",
        ],
    )
    def test_valid_urls(self, url):
        assert is_valid_video_url(url) is True

    @pytest.mark.parametrize(
        "url",
        [
            "",
            "not-a-url",
            "ftp://facebook.com/watch?v=123",
            "https://vimeo.com/123456",
            "https://www.facebook.com/",
            "https://www.facebook.com/profile",
            None,
        ],
    )
    def test_invalid_urls(self, url):
        assert is_valid_video_url(url) is False


class TestIsValidFacebookUrl:
    """测试 Facebook URL 验证函数（向后兼容）"""

    @pytest.mark.parametrize(
        "url",
        [
            "https://www.facebook.com/watch?v=123456789",
            "http://facebook.com/watch?v=abc123",
            "https://facebook.com/share/v/xyz789/",
            "https://fb.watch/shortcode123",
            "https://www.facebook.com/mypage/videos/987654321",
            "https://www.facebook.com/groups/mygroup/posts/555666777",
        ],
    )
    def test_valid_urls(self, url):
        assert is_valid_facebook_url(url) is True

    @pytest.mark.parametrize(
        "url",
        [
            "",
            "not-a-url",
            "ftp://facebook.com/watch?v=123",
            "https://youtube.com/watch?v=123",
            "https://www.facebook.com/",
            "https://www.facebook.com/profile",
            None,
        ],
    )
    def test_invalid_urls(self, url):
        assert is_valid_facebook_url(url) is False


class TestExtractVideoId:
    """测试视频 ID 提取函数"""

    # Facebook
    def test_facebook_watch_url(self):
        assert extract_video_id("https://www.facebook.com/watch?v=abc123") == "abc123"

    def test_facebook_watch_url_with_extra_params(self):
        assert extract_video_id("https://www.facebook.com/watch?v=abc123&ref=share") == "abc123"

    def test_facebook_videos_url(self):
        assert extract_video_id("https://www.facebook.com/mypage/videos/987654") == "987654"

    def test_facebook_share_url(self):
        assert extract_video_id("https://www.facebook.com/share/v/xyz789/") == "xyz789"

    def test_facebook_fb_watch_url(self):
        assert extract_video_id("https://fb.watch/shortcode123") == "shortcode123"

    # YouTube
    def test_youtube_watch_url(self):
        assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_youtube_watch_url_with_extra_params(self):
        assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10s") == "dQw4w9WgXcQ"

    def test_youtube_shorts_url(self):
        assert extract_video_id("https://youtube.com/shorts/Shorts123") == "Shorts123"

    def test_youtu_be_url(self):
        assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_youtube_embed_url(self):
        assert extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_youtube_v_url(self):
        assert extract_video_id("https://www.youtube.com/v/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_invalid_url_returns_none(self):
        assert extract_video_id("https://example.com") is None

    def test_empty_url_returns_none(self):
        assert extract_video_id("") is None
