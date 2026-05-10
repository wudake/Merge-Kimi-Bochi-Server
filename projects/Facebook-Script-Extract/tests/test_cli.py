import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from main import main


class TestCLIMain:
    @patch("main.load_dotenv")
    @patch("main.is_valid_video_url")
    @patch("main.VideoDownloader")
    @patch("main.AudioExtractor")
    @patch("main.Transcriber")
    @patch("main.save")
    def test_api_mode_success(
        self,
        mock_save,
        mock_transcriber_class,
        mock_extractor_class,
        mock_downloader_class,
        mock_is_valid,
        mock_load_dotenv,
        tmp_path,
        monkeypatch,
    ):
        mock_is_valid.return_value = True

        mock_downloader = MagicMock()
        mock_downloader.download.return_value = str(tmp_path / "video.mp4")
        mock_downloader_class.return_value = mock_downloader

        mock_extractor = MagicMock()
        mock_extractor.extract.return_value = str(tmp_path / "audio.mp3")
        mock_extractor_class.return_value = mock_extractor

        mock_transcriber = MagicMock()
        mock_transcriber.transcribe.return_value = {
            "language": "en",
            "duration": 10.5,
        }
        mock_transcriber_class.return_value = mock_transcriber

        mock_save.return_value = str(tmp_path / "result.txt")

        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setattr(sys, "argv", [
            "main.py",
            "https://www.facebook.com/watch?v=123",
            "--output", str(tmp_path / "result.txt"),
            "--temp-dir", str(tmp_path),
            "--format", "txt",
        ])

        main()

        mock_downloader.download.assert_called_once_with(
            "https://www.facebook.com/watch?v=123"
        )
        mock_extractor.extract.assert_called_once()
        mock_transcriber.transcribe.assert_called_once()
        mock_save.assert_called_once()

    @patch("main.load_dotenv")
    @patch("main.is_valid_video_url")
    @patch("main.VideoDownloader")
    @patch("main.AudioExtractor")
    @patch("main.LocalTranscriber")
    @patch("main.save")
    def test_local_mode_success(
        self,
        mock_save,
        mock_local_class,
        mock_extractor_class,
        mock_downloader_class,
        mock_is_valid,
        mock_load_dotenv,
        tmp_path,
        monkeypatch,
    ):
        mock_is_valid.return_value = True

        mock_downloader = MagicMock()
        mock_downloader.download.return_value = str(tmp_path / "video.mp4")
        mock_downloader_class.return_value = mock_downloader

        mock_extractor = MagicMock()
        mock_extractor.extract.return_value = str(tmp_path / "audio.mp3")
        mock_extractor_class.return_value = mock_extractor

        mock_local = MagicMock()
        mock_local.transcribe.return_value = {
            "language": "zh",
            "duration": 5.0,
        }
        mock_local_class.return_value = mock_local

        mock_save.return_value = str(tmp_path / "result.txt")

        monkeypatch.setattr(sys, "argv", [
            "main.py",
            "https://www.facebook.com/watch?v=123",
            "--local",
            "--output", str(tmp_path / "result.txt"),
            "--temp-dir", str(tmp_path),
            "--language", "zh",
            "--model-size", "base",
            "--device", "cpu",
        ])

        main()

        mock_local_class.assert_called_once_with(
            model_size="base",
            device="cpu",
            language="zh",
        )

    @patch("main.load_dotenv")
    @patch("main.is_valid_video_url")
    def test_invalid_url_exits(self, mock_is_valid, mock_load_dotenv, monkeypatch):
        mock_is_valid.return_value = False
        monkeypatch.setattr(sys, "argv", [
            "main.py",
            "https://example.com",
        ])

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    @patch("main.load_dotenv")
    @patch("main.is_valid_video_url")
    def test_no_api_key_exits(self, mock_is_valid, mock_load_dotenv, monkeypatch):
        mock_is_valid.return_value = True
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setattr(sys, "argv", [
            "main.py",
            "https://www.facebook.com/watch?v=123",
        ])

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    @patch("main.load_dotenv")
    @patch("main.is_valid_video_url")
    @patch("main.VideoDownloader")
    @patch("main.AudioExtractor")
    @patch("main.LocalTranscriber")
    @patch("main.save")
    def test_auto_language_for_local(
        self,
        mock_save,
        mock_local_class,
        mock_extractor_class,
        mock_downloader_class,
        mock_is_valid,
        mock_load_dotenv,
        tmp_path,
        monkeypatch,
    ):
        mock_is_valid.return_value = True

        mock_downloader = MagicMock()
        mock_downloader.download.return_value = str(tmp_path / "video.mp4")
        mock_downloader_class.return_value = mock_downloader

        mock_extractor = MagicMock()
        mock_extractor.extract.return_value = str(tmp_path / "audio.mp3")
        mock_extractor_class.return_value = mock_extractor

        mock_local = MagicMock()
        mock_local.transcribe.return_value = {"language": "auto", "duration": 1.0}
        mock_local_class.return_value = mock_local

        mock_save.return_value = str(tmp_path / "result.txt")

        monkeypatch.setattr(sys, "argv", [
            "main.py",
            "https://www.facebook.com/watch?v=123",
            "--local",
            "--language", "auto",
            "--temp-dir", str(tmp_path),
            "--output", str(tmp_path / "result.txt"),
        ])

        main()

        mock_local_class.assert_called_once_with(
            model_size="small",
            device="cpu",
            language=None,
        )
