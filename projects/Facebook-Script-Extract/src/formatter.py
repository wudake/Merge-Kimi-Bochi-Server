import json
from pathlib import Path


def format_txt(data: dict) -> str:
    return data["full_text"]


def format_srt(data: dict) -> str:
    lines = []
    for seg in data["segments"]:
        start = _seconds_to_srt_time(seg["start"])
        end = _seconds_to_srt_time(seg["end"])
        lines.append(f"{seg['id']}\n{start} --> {end}\n{seg['text']}\n")
    return "\n".join(lines)


def format_vtt(data: dict) -> str:
    lines = ["WEBVTT\n"]
    for seg in data["segments"]:
        start = _seconds_to_vtt_time(seg["start"])
        end = _seconds_to_vtt_time(seg["end"])
        lines.append(f"{start} --> {end}\n{seg['text']}\n")
    return "\n".join(lines)


def format_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def _seconds_to_srt_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _seconds_to_vtt_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def save(data: dict, output_path: str, fmt: str = "txt"):
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if fmt == "txt":
        content = format_txt(data)
    elif fmt == "srt":
        content = format_srt(data)
    elif fmt == "vtt":
        content = format_vtt(data)
    elif fmt == "json":
        content = format_json(data)
    else:
        raise ValueError(f"不支持的格式: {fmt}")

    path.write_text(content, encoding="utf-8")
    return str(path)
