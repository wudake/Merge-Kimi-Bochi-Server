from unittest.mock import MagicMock, patch

import pytest

from src.transcriber import Transcriber


class TestTranscriberInit:
    @patch("src.transcriber.OpenAI")
    def test_init_with_api_key(self, mock_openai):
        t = Transcriber(api_key="sk-test", language="zh")
        mock_openai.assert_called_once_with(api_key="sk-test")
        assert t.language == "zh"

    @patch("src.transcriber.OpenAI")
    def test_init_auto_language(self, mock_openai):
        t = Transcriber(api_key="sk-test", language="auto")
        assert t.language is None

    @patch("src.transcriber.OpenAI")
    def test_init_default_language(self, mock_openai):
        t = Transcriber(api_key="sk-test")
        assert t.language is None


class TestTranscriberTranscribe:
    @patch("src.transcriber.OpenAI")
    def test_transcribe_success(self, mock_openai_class, tmp_path):
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        # 模拟响应
        mock_segment = MagicMock()
        mock_segment.id = 0
        mock_segment.start = 0.0
        mock_segment.end = 3.5
        mock_segment.text = "Hello world"

        mock_response = MagicMock()
        mock_response.language = "en"
        mock_response.duration = 12.5
        mock_response.text = "Hello world"
        mock_response.segments = [mock_segment]

        mock_client.audio.transcriptions.create.return_value = mock_response

        transcriber = Transcriber(api_key="sk-test", language="en")

        audio_path = tmp_path / "audio.mp3"
        audio_path.write_text("fake audio")

        result = transcriber.transcribe(str(audio_path))

        assert result["language"] == "en"
        assert result["duration"] == 12.5
        assert result["full_text"] == "Hello world"
        assert len(result["segments"]) == 1
        assert result["segments"][0]["text"] == "Hello world"

        # 验证调用参数
        call_kwargs = mock_client.audio.transcriptions.create.call_args[1]
        assert call_kwargs["model"] == "whisper-1"
        assert call_kwargs["language"] == "en"
        assert call_kwargs["response_format"] == "verbose_json"

    @patch("src.transcriber.OpenAI")
    def test_transcribe_auto_language_no_language_param(self, mock_openai_class, tmp_path):
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.language = "zh"
        mock_response.duration = 5.0
        mock_response.text = "你好"
        mock_response.segments = []

        mock_client.audio.transcriptions.create.return_value = mock_response

        transcriber = Transcriber(api_key="sk-test", language="auto")

        audio_path = tmp_path / "audio.mp3"
        audio_path.write_text("fake audio")

        result = transcriber.transcribe(str(audio_path))

        call_kwargs = mock_client.audio.transcriptions.create.call_args[1]
        assert "language" not in call_kwargs
        assert result["language"] == "zh"

    @patch("src.transcriber.OpenAI")
    def test_transcribe_multiple_segments(self, mock_openai_class, tmp_path):
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        segments = []
        for i in range(3):
            seg = MagicMock()
            seg.id = i
            seg.start = float(i * 2)
            seg.end = float(i * 2 + 1.5)
            seg.text = f"Segment {i} "
            segments.append(seg)

        mock_response = MagicMock()
        mock_response.language = "en"
        mock_response.duration = 10.0
        mock_response.text = "Segment 0 Segment 1 Segment 2"
        mock_response.segments = segments

        mock_client.audio.transcriptions.create.return_value = mock_response

        transcriber = Transcriber(api_key="sk-test")
        audio_path = tmp_path / "audio.mp3"
        audio_path.write_text("fake audio")

        result = transcriber.transcribe(str(audio_path))

        assert len(result["segments"]) == 3
        assert result["segments"][2]["id"] == 2
