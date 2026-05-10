from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class TaskStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    EXTRACTING_AUDIO = "extracting_audio"
    TRANSCRIBING = "transcribing"
    COMPLETED = "completed"
    FAILED = "failed"


class OutputFormat(str, Enum):
    TXT = "txt"
    SRT = "srt"
    VTT = "vtt"
    JSON = "json"


class ModelSize(str, Enum):
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE_V3 = "large-v3"


class Device(str, Enum):
    CPU = "cpu"
    CUDA = "cuda"


class TaskCreate(BaseModel):
    url: str = Field(..., description="Facebook 或 YouTube 视频链接")
    language: str = Field(default="en", description="音频语言，auto 为自动检测")
    output_format: OutputFormat = Field(default=OutputFormat.JSON, description="输出格式")
    use_local: bool = Field(default=True, description="是否使用本地 Whisper 模型")
    model_size: ModelSize = Field(default=ModelSize.TINY, description="本地模型大小")
    device: Device = Field(default=Device.CPU, description="推理设备")


class TaskInfo(BaseModel):
    id: str
    status: TaskStatus
    url: str
    language: str
    output_format: OutputFormat
    use_local: bool
    model_size: ModelSize
    created_at: datetime
    updated_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    result_url: str | None = None
    progress: int = Field(default=0, ge=0, le=100, description="处理进度百分比")


class TaskResult(BaseModel):
    id: str
    status: TaskStatus
    language: str | None = None
    duration: float | None = None
    segments: list[dict] | None = None
    full_text: str | None = None
    output_file: str | None = None
    video_url: str | None = None
    error_message: str | None = None
