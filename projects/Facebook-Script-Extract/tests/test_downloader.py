from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.downloader import VideoDownloader


class TestVideoDownloader:
    @patch("src.downloader.yt_dlp.YoutubeDL")
    def test_download_success(self, mock_ytdl_class, tmp_path):
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {"id": "test123"}
        mock_ytdl_class.return_value.__enter__.return_value = mock_ydl

        # 模拟下载后文件存在
        video_file = tmp_path / "test123.mp4"
        video_file.write_text("fake video content")

        downloader = VideoDownloader(temp_dir=str(tmp_path))
        result = downloader.download("https://www.facebook.com/watch?v=test123")

        assert result == str(video_file)
        mock_ydl.extract_info.assert_called_once()

    @patch("src.downloader.yt_dlp.YoutubeDL")
    def test_download_file_not_found(self, mock_ytdl_class, tmp_path):
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {"id": "nonexistent"}
        mock_ytdl_class.return_value.__enter__.return_value = mock_ydl

        # 不创建文件，模拟文件不存在
        downloader = VideoDownloader(temp_dir=str(tmp_path))
        with pytest.raises(FileNotFoundError, match="未找到下载的视频文件"):
            downloader.download("https://www.facebook.com/watch?v=nonexistent")

    @patch("src.downloader.requests")
    @patch("src.downloader.FacebookAdsExtractor")
    def test_download_ads_library_direct_url(self, mock_extractor_class, mock_requests, tmp_path):
        """测试 Ads Library 直链下载路径."""
        mock_extractor = MagicMock()
        mock_extractor.extract.return_value = "https://video.fbcdn.net/ad_video_hd.mp4"
        mock_extractor_class.return_value = mock_extractor

        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"fake", b"video", b"data"]
        mock_requests.get.return_value = mock_response

        downloader = VideoDownloader(temp_dir=str(tmp_path))
        result = downloader.download("https://www.facebook.com/ads/library/?id=1539922477140995")

        assert result.endswith(".mp4")
        assert Path(result).exists()
        mock_requests.get.assert_called_once()

    @patch("src.downloader.yt_dlp.YoutubeDL")
    @patch("src.downloader.FacebookAdsExtractor")
    def test_download_ads_library_watch_fallback(self, mock_extractor_class, mock_ytdl_class, tmp_path):
        """测试 Ads Library 提取到 watch 页时回退到 yt_dlp."""
        mock_extractor = MagicMock()
        mock_extractor.extract.return_value = "https://www.facebook.com/watch/?v=123456"
        mock_extractor_class.return_value = mock_extractor

        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {"id": "watch123"}
        mock_ytdl_class.return_value.__enter__.return_value = mock_ydl

        video_file = tmp_path / "watch123.mp4"
        video_file.write_text("fake video content")

        downloader = VideoDownloader(temp_dir=str(tmp_path))
        result = downloader.download("https://www.facebook.com/ads/library/?id=1539922477140995")

        assert result == str(video_file)
        mock_ydl.extract_info.assert_called_once()

    def test_creates_temp_dir(self, tmp_path):
        new_dir = tmp_path / "new_temp"
        assert not new_dir.exists()
        VideoDownloader(temp_dir=str(new_dir))
        assert new_dir.exists()

    def test_existing_temp_dir(self, tmp_path):
        existing = tmp_path / "existing"
        existing.mkdir()
        VideoDownloader(temp_dir=str(existing))
        assert existing.exists()
