import json
from pathlib import Path

import pytest

from src.formatter import (
    _seconds_to_srt_time,
    _seconds_to_vtt_time,
    format_json,
    format_srt,
    format_txt,
    format_vtt,
    save,
)


@pytest.fixture
def sample_data():
    return {
        "language": "zh",
        "duration": 12.5,
        "full_text": "Hello world. This is a test.",
        "segments": [
            {"id": 1, "start": 0.0, "end": 3.5, "text": "Hello world."},
            {"id": 2, "start": 4.0, "end": 7.123, "text": "This is a test."},
        ],
    }


class TestFormatTxt:
    def test_returns_full_text(self, sample_data):
        assert format_txt(sample_data) == "Hello world. This is a test."

    def test_empty_text(self):
        assert format_txt({"full_text": ""}) == ""


class TestFormatSrt:
    def test_basic_formatting(self, sample_data):
        result = format_srt(sample_data)
        lines = result.strip().split("\n")
        assert "1" in lines[0]
        assert "00:00:00,000 --> 00:00:03,500" in lines[1]
        assert "Hello world." in lines[2]

    def test_multiple_segments(self, sample_data):
        result = format_srt(sample_data)
        assert result.count("-->") == 2

    def test_empty_segments(self):
        result = format_srt({"segments": []})
        assert result == ""


class TestFormatVtt:
    def test_has_webvtt_header(self, sample_data):
        result = format_vtt(sample_data)
        assert result.startswith("WEBVTT\n")

    def test_time_format_uses_dot(self, sample_data):
        result = format_vtt(sample_data)
        assert "00:00:00.000 --> 00:00:03.500" in result

    def test_empty_segments(self):
        result = format_vtt({"segments": []})
        assert result == "WEBVTT\n"


class TestFormatJson:
    def test_returns_valid_json(self, sample_data):
        result = format_json(sample_data)
        parsed = json.loads(result)
        assert parsed["language"] == "zh"
        assert parsed["duration"] == 12.5

    def test_pretty_printed(self, sample_data):
        result = format_json(sample_data)
        assert "\n" in result
        assert "  " in result


class TestSecondsToSrtTime:
    @pytest.mark.parametrize(
        "seconds,expected",
        [
            (0.0, "00:00:00,000"),
            (3.5, "00:00:03,500"),
            (61.1, "00:01:01,100"),
            (3661.5, "01:01:01,500"),
            (3600.0, "01:00:00,000"),
        ],
    )
    def test_conversions(self, seconds, expected):
        assert _seconds_to_srt_time(seconds) == expected


class TestSecondsToVttTime:
    @pytest.mark.parametrize(
        "seconds,expected",
        [
            (0.0, "00:00:00.000"),
            (3.5, "00:00:03.500"),
            (61.1, "00:01:01.100"),
            (3661.5, "01:01:01.500"),
        ],
    )
    def test_conversions(self, seconds, expected):
        assert _seconds_to_vtt_time(seconds) == expected


class TestSave:
    def test_save_txt(self, tmp_path, sample_data):
        path = tmp_path / "output.txt"
        result = save(sample_data, str(path), fmt="txt")
        assert Path(result).exists()
        assert path.read_text(encoding="utf-8") == "Hello world. This is a test."

    def test_save_json(self, tmp_path, sample_data):
        path = tmp_path / "output.json"
        result = save(sample_data, str(path), fmt="json")
        assert Path(result).exists()
        parsed = json.loads(path.read_text(encoding="utf-8"))
        assert parsed["language"] == "zh"

    def test_save_srt(self, tmp_path, sample_data):
        path = tmp_path / "output.srt"
        result = save(sample_data, str(path), fmt="srt")
        assert Path(result).exists()
        content = path.read_text(encoding="utf-8")
        assert "-->" in content

    def test_save_vtt(self, tmp_path, sample_data):
        path = tmp_path / "output.vtt"
        result = save(sample_data, str(path), fmt="vtt")
        assert Path(result).exists()
        content = path.read_text(encoding="utf-8")
        assert content.startswith("WEBVTT")

    def test_invalid_format_raises(self, tmp_path, sample_data):
        with pytest.raises(ValueError, match="不支持的格式"):
            save(sample_data, str(tmp_path / "output.docx"), fmt="docx")

    def test_creates_parent_directories(self, tmp_path, sample_data):
        nested = tmp_path / "deep" / "nested" / "output.txt"
        result = save(sample_data, str(nested), fmt="txt")
        assert Path(result).exists()
