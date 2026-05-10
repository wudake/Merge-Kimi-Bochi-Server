import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.audio_extractor import AudioExtractor


class TestAudioExtractor:
    @patch("src.audio_extractor.subprocess.run")
    def test_extract_success(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        video_path = tmp_path / "video.mp4"
        video_path.write_text("fake video")

        extractor = AudioExtractor(temp_dir=str(tmp_path))
        result = extractor.extract(str(video_path))

        expected_path = str(tmp_path / "video.mp3")
        assert result == expected_path

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "ffmpeg"
        assert "-i" in args
        assert str(video_path) in args
        assert expected_path in args

    @patch("src.audio_extractor.subprocess.run")
    def test_extract_failure(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(returncode=1, stderr="ffmpeg error: codec not found")

        video_path = tmp_path / "video.mp4"
        video_path.write_text("fake video")

        extractor = AudioExtractor(temp_dir=str(tmp_path))
        with pytest.raises(RuntimeError, match="音频提取失败"):
            extractor.extract(str(video_path))

    @patch("src.audio_extractor.subprocess.run")
    def test_ffmpeg_command_args(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        video_path = tmp_path / "video.mp4"
        video_path.write_text("fake video")

        extractor = AudioExtractor(temp_dir=str(tmp_path))
        extractor.extract(str(video_path))

        args = mock_run.call_args[0][0]
        assert "-vn" in args
        assert "-acodec" in args
        assert "libmp3lame" in args
        assert "-q:a" in args
        assert "2" in args
        assert "-y" in args

    def test_creates_temp_dir(self, tmp_path):
        new_dir = tmp_path / "audio_temp"
        assert not new_dir.exists()
        AudioExtractor(temp_dir=str(new_dir))
        assert new_dir.exists()
