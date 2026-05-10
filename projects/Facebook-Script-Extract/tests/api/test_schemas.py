from datetime import datetime

import pytest
from pydantic import ValidationError

from api.models.schemas import (
    Device,
    ModelSize,
    OutputFormat,
    TaskCreate,
    TaskInfo,
    TaskResult,
    TaskStatus,
)


class TestEnums:
    def test_task_status_values(self):
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.DOWNLOADING == "downloading"
        assert TaskStatus.EXTRACTING_AUDIO == "extracting_audio"
        assert TaskStatus.TRANSCRIBING == "transcribing"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"

    def test_output_format_values(self):
        assert OutputFormat.TXT == "txt"
        assert OutputFormat.SRT == "srt"
        assert OutputFormat.VTT == "vtt"
        assert OutputFormat.JSON == "json"

    def test_model_size_values(self):
        assert ModelSize.TINY == "tiny"
        assert ModelSize.BASE == "base"
        assert ModelSize.SMALL == "small"
        assert ModelSize.MEDIUM == "medium"
        assert ModelSize.LARGE_V3 == "large-v3"

    def test_device_values(self):
        assert Device.CPU == "cpu"
        assert Device.CUDA == "cuda"


class TestTaskCreate:
    def test_valid_minimal(self):
        tc = TaskCreate(url="https://www.facebook.com/watch?v=123")
        assert tc.url == "https://www.facebook.com/watch?v=123"
        assert tc.language == "en"
        assert tc.output_format == OutputFormat.JSON
        assert tc.use_local is True
        assert tc.model_size == ModelSize.TINY
        assert tc.device == Device.CPU

    def test_valid_full(self):
        tc = TaskCreate(
            url="https://www.facebook.com/watch?v=123",
            language="zh",
            output_format=OutputFormat.SRT,
            use_local=False,
            model_size=ModelSize.LARGE_V3,
            device=Device.CUDA,
        )
        assert tc.language == "zh"
        assert tc.output_format == OutputFormat.SRT
        assert tc.use_local is False

    def test_missing_url_raises(self):
        with pytest.raises(ValidationError):
            TaskCreate()

    def test_url_must_be_string(self):
        with pytest.raises(ValidationError):
            TaskCreate(url=123)


class TestTaskInfo:
    def test_valid(self):
        now = datetime.now()
        ti = TaskInfo(
            id="task-123",
            status=TaskStatus.PENDING,
            url="https://example.com",
            language="en",
            output_format=OutputFormat.TXT,
            use_local=True,
            model_size=ModelSize.SMALL,
            created_at=now,
            progress=0,
        )
        assert ti.id == "task-123"
        assert ti.progress == 0

    def test_optional_fields(self):
        now = datetime.now()
        ti = TaskInfo(
            id="task-123",
            status=TaskStatus.COMPLETED,
            url="https://example.com",
            language="en",
            output_format=OutputFormat.JSON,
            use_local=False,
            model_size=ModelSize.BASE,
            created_at=now,
            updated_at=now,
            completed_at=now,
            error_message="Something went wrong",
            result_url="/tasks/task-123/download",
            progress=100,
        )
        assert ti.error_message == "Something went wrong"
        assert ti.result_url == "/tasks/task-123/download"

    def test_progress_bounds(self):
        now = datetime.now()
        with pytest.raises(ValidationError):
            TaskInfo(
                id="task-123",
                status=TaskStatus.PENDING,
                url="https://example.com",
                language="en",
                output_format=OutputFormat.TXT,
                use_local=True,
                model_size=ModelSize.SMALL,
                created_at=now,
                progress=101,
            )

        with pytest.raises(ValidationError):
            TaskInfo(
                id="task-123",
                status=TaskStatus.PENDING,
                url="https://example.com",
                language="en",
                output_format=OutputFormat.TXT,
                use_local=True,
                model_size=ModelSize.SMALL,
                created_at=now,
                progress=-1,
            )


class TestTaskResult:
    def test_valid_minimal(self):
        tr = TaskResult(id="task-123", status=TaskStatus.PENDING)
        assert tr.id == "task-123"
        assert tr.language is None
        assert tr.duration is None
        assert tr.segments is None
        assert tr.full_text is None
        assert tr.output_file is None
        assert tr.error_message is None

    def test_valid_full(self):
        tr = TaskResult(
            id="task-123",
            status=TaskStatus.COMPLETED,
            language="zh",
            duration=120.5,
            segments=[{"id": 1, "text": "Hello"}],
            full_text="Hello world",
            output_file="/path/to/result.json",
            error_message=None,
        )
        assert tr.duration == 120.5
        assert tr.segments == [{"id": 1, "text": "Hello"}]
