import os
from pathlib import Path

from openai import OpenAI


class Transcriber:
    def __init__(self, api_key: str | None = None, language: str = "auto"):
        self.client = OpenAI(api_key=api_key)
        self.language = None if language == "auto" else language

    def transcribe(self, audio_path: str) -> dict:
        with open(audio_path, "rb") as audio_file:
            kwargs = {
                "model": "whisper-1",
                "file": audio_file,
                "response_format": "verbose_json",
                "timestamp_granularities": ["segment"],
            }
            if self.language:
                kwargs["language"] = self.language
            transcript = self.client.audio.transcriptions.create(**kwargs)

        segments = []
        for seg in transcript.segments:
            segments.append({
                "id": seg.id,
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip(),
            })

        return {
            "language": transcript.language,
            "duration": transcript.duration,
            "segments": segments,
            "full_text": transcript.text,
        }
