from unittest.mock import MagicMock, patch

import pytest

from src.local_transcriber import LocalTranscriber


class TestLocalTranscriberInit:
    @patch("src.local_transcriber.WhisperModel")
    def test_init_default_params(self, mock_model_class):
        mock_model_class.return_value = MagicMock()
        t = LocalTranscriber()
        mock_model_class.assert_called_once_with("tiny", device="cpu", compute_type="int8")
        assert t.language is None

    @patch("src.local_transcriber.WhisperModel")
    def test_init_custom_params(self, mock_model_class):
        mock_model_class.return_value = MagicMock()
        t = LocalTranscriber(
            model_size="large-v3",
            device="cuda",
            compute_type="float16",
            language="zh",
        )
        mock_model_class.assert_called_once_with(
            "large-v3", device="cuda", compute_type="float16"
        )
        assert t.language == "zh"

    @patch("src.local_transcriber.WhisperModel")
    def test_init_suppresses_warnings(self, mock_model_class):
        mock_model_class.return_value = MagicMock()
        with patch("src.local_transcriber.warnings.filterwarnings") as mock_filter:
            LocalTranscriber()
            mock_filter.assert_called_once_with("ignore", category=FutureWarning)


class TestLocalTranscriberTranscribe:
    @patch("src.local_transcriber.WhisperModel")
    def test_transcribe_success(self, mock_model_class):
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model

        mock_segment1 = MagicMock()
        mock_segment1.start = 0.0
        mock_segment1.end = 2.5
        mock_segment1.text = "Hello world"

        mock_segment2 = MagicMock()
        mock_segment2.start = 3.0
        mock_segment2.end = 5.0
        mock_segment2.text = "This is a test"

        mock_info = MagicMock()
        mock_info.language = "en"
        mock_info.duration = 10.0

        mock_model.transcribe.return_value = (
            iter([mock_segment1, mock_segment2]),
            mock_info,
        )

        transcriber = LocalTranscriber(language="en")
        result = transcriber.transcribe("/fake/path/audio.mp3")

        assert result["language"] == "en"
        assert result["duration"] == 10.0
        assert result["full_text"] == "Hello world This is a test"
        assert len(result["segments"]) == 2
        assert result["segments"][0]["id"] == 0
        assert result["segments"][1]["id"] == 1
        assert result["segments"][1]["text"] == "This is a test"

        call_args = mock_model.transcribe.call_args[1]
        assert call_args["language"] == "en"
        assert call_args["condition_on_previous_text"] is True
        assert call_args["vad_filter"] is True

    @patch("src.local_transcriber.WhisperModel")
    def test_transcribe_no_language(self, mock_model_class):
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model

        mock_info = MagicMock()
        mock_info.language = "auto"
        mock_info.duration = 5.0

        mock_model.transcribe.return_value = (iter([]), mock_info)

        transcriber = LocalTranscriber()
        result = transcriber.transcribe("/fake/path/audio.mp3")

        call_args = mock_model.transcribe.call_args[1]
        assert call_args["language"] is None

    @patch("src.local_transcriber.WhisperModel")
    def test_transcribe_empty_segments(self, mock_model_class):
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model

        mock_info = MagicMock()
        mock_info.language = "zh"
        mock_info.duration = 0.0

        mock_model.transcribe.return_value = (iter([]), mock_info)

        transcriber = LocalTranscriber()
        result = transcriber.transcribe("/fake/path/audio.mp3")

        assert result["segments"] == []
        assert result["full_text"] == ""
