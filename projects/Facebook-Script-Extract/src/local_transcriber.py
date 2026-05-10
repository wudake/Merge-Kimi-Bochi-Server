import warnings
from pathlib import Path

from faster_whisper import WhisperModel


class LocalTranscriber:
    def __init__(
        self,
        model_size: str = "tiny",
        device: str = "cpu",
        compute_type: str = "int8",
        language: str | None = None,
    ):
        # 抑制 torch  future warning
        warnings.filterwarnings("ignore", category=FutureWarning)
        self.language = language
        print(f"[加载模型] faster-whisper '{model_size}' on {device} ({compute_type})...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        print("[加载模型] 完成")

    def transcribe(self, audio_path: str) -> dict:
        segments_iter, info = self.model.transcribe(
            audio_path,
            language=self.language,
            condition_on_previous_text=True,
            vad_filter=True,
        )

        segments = []
        full_text_parts = []
        for i, seg in enumerate(segments_iter):
            segments.append({
                "id": i,
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip(),
            })
            full_text_parts.append(seg.text.strip())

        return {
            "language": info.language,
            "duration": info.duration,
            "segments": segments,
            "full_text": " ".join(full_text_parts),
        }
