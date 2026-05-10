import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


@pytest.fixture
def mock_redis():
    with patch("api.routers.tasks.redis_client") as mock:
        yield mock


@pytest.fixture
def mock_celery_app():
    with patch("api.routers.tasks.celery_app") as mock:
        yield mock


class TestCreateTask:
    @patch("api.routers.tasks.process_video")
    @patch("api.routers.tasks._init_task_meta")
    @patch("api.routers.tasks._build_task_info")
    def test_create_task_success(self, mock_build, mock_init, mock_process):
        mock_build.return_value = {
            "id": "test-uuid",
            "status": "pending",
            "url": "https://www.facebook.com/watch?v=123",
            "language": "auto",
            "output_format": "json",
            "use_local": True,
            "model_size": "small",
            "created_at": datetime.now().isoformat(),
            "progress": 0,
        }

        response = client.post(
            "/tasks",
            json={
                "url": "https://www.facebook.com/watch?v=123",
                "language": "auto",
                "output_format": "json",
                "use_local": True,
            },
        )

        assert response.status_code == 202
        mock_init.assert_called_once()
        mock_process.apply_async.assert_called_once()

    def test_create_task_invalid_url_type(self):
        response = client.post(
            "/tasks",
            json={"url": 123},
        )
        assert response.status_code == 422

    def test_create_task_missing_url(self):
        response = client.post(
            "/tasks",
            json={},
        )
        assert response.status_code == 422


def _make_task_info(task_id: str, status: str = "pending"):
    from api.models.schemas import TaskInfo, OutputFormat, TaskStatus
    now = datetime.now()
    return TaskInfo(
        id=task_id,
        status=TaskStatus(status),
        url="https://www.facebook.com/watch?v=123",
        language="auto",
        output_format=OutputFormat.JSON,
        use_local=True,
        model_size="small",
        created_at=now,
        progress=0,
    )


class TestListTasks:
    @patch("api.routers.tasks._build_task_info")
    def test_list_tasks_success(self, mock_build, mock_redis):
        mock_redis.keys.return_value = ["task_meta:task-1", "task_meta:task-2"]
        mock_build.side_effect = [
            _make_task_info("task-1", "completed"),
            _make_task_info("task-2", "pending"),
        ]

        response = client.get("/tasks")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == "task-1"

    @patch("api.routers.tasks._build_task_info")
    def test_list_tasks_with_pagination(self, mock_build, mock_redis):
        mock_redis.keys.return_value = [
            "task_meta:task-1",
            "task_meta:task-2",
            "task_meta:task-3",
        ]
        mock_build.side_effect = [
            _make_task_info("task-1"),
            _make_task_info("task-2"),
        ]

        response = client.get("/tasks?skip=0&limit=2")

        assert response.status_code == 200
        assert len(response.json()) == 2

    @patch("api.routers.tasks._build_task_info")
    def test_list_tasks_skip_broken_meta(self, mock_build, mock_redis):
        mock_redis.keys.return_value = ["task_meta:task-1", "task_meta:broken"]
        from fastapi import HTTPException

        def side_effect(task_id):
            if task_id == "broken":
                raise HTTPException(status_code=404)
            return _make_task_info(task_id)

        mock_build.side_effect = side_effect

        response = client.get("/tasks")
        assert response.status_code == 200
        assert len(response.json()) == 1


class TestGetTask:
    @patch("api.routers.tasks._build_task_info")
    def test_get_task_success(self, mock_build):
        mock_build.return_value = {
            "id": "task-123",
            "status": "completed",
            "url": "https://example.com",
            "language": "en",
            "output_format": "json",
            "use_local": True,
            "model_size": "small",
            "created_at": datetime.now().isoformat(),
            "progress": 100,
        }

        response = client.get("/tasks/task-123")
        assert response.status_code == 200
        assert response.json()["id"] == "task-123"

    @patch("api.routers.tasks._build_task_info")
    def test_get_task_not_found(self, mock_build):
        from fastapi import HTTPException

        mock_build.side_effect = HTTPException(status_code=404, detail="任务不存在")

        response = client.get("/tasks/nonexistent")
        assert response.status_code == 404


class TestDownloadResult:
    @patch("api.routers.tasks._get_task_meta")
    def test_download_completed_task(self, mock_get_meta, tmp_path):
        with patch("api.routers.tasks.settings") as mock_settings:
            mock_settings.output_dir = str(tmp_path)
            mock_get_meta.return_value = {
                "status": "completed",
                "output_format": "json",
            }

            output_file = tmp_path / "task-123.json"
            output_file.write_text('{"test": true}')

            response = client.get("/tasks/task-123/download")
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json"

    @patch("api.routers.tasks._get_task_meta")
    def test_download_task_not_completed(self, mock_get_meta):
        mock_get_meta.return_value = {
            "status": "pending",
            "output_format": "json",
        }

        response = client.get("/tasks/task-123/download")
        assert response.status_code == 400

    @patch("api.routers.tasks._get_task_meta")
    def test_download_file_not_found(self, mock_get_meta, tmp_path):
        with patch("api.routers.tasks.settings") as mock_settings:
            mock_settings.output_dir = str(tmp_path)
            mock_get_meta.return_value = {
                "status": "completed",
                "output_format": "json",
            }

            response = client.get("/tasks/task-123/download")
            assert response.status_code == 404

    @patch("api.routers.tasks._get_task_meta")
    def test_download_task_not_exists(self, mock_get_meta):
        mock_get_meta.return_value = {}

        response = client.get("/tasks/task-123/download")
        assert response.status_code == 404

    @patch("api.routers.tasks._get_task_meta")
    def test_download_txt_format(self, mock_get_meta, tmp_path):
        with patch("api.routers.tasks.settings") as mock_settings:
            mock_settings.output_dir = str(tmp_path)
            mock_get_meta.return_value = {
                "status": "completed",
                "output_format": "txt",
            }

            output_file = tmp_path / "task-123.txt"
            output_file.write_text("Hello world")

            response = client.get("/tasks/task-123/download")
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/plain; charset=utf-8"


class TestGetTaskResult:
    @patch("api.routers.tasks._get_task_meta")
    def test_get_result_completed_json(self, mock_get_meta, tmp_path):
        with patch("api.routers.tasks.settings") as mock_settings:
            mock_settings.output_dir = str(tmp_path)
            mock_get_meta.return_value = {
                "status": "completed",
                "language": "en",
                "duration": "10.5",
                "output_format": "json",
            }

            output_file = tmp_path / "task-123.json"
            output_file.write_text(
                json.dumps(
                    {
                        "segments": [{"id": 1, "text": "Hello"}],
                        "full_text": "Hello world",
                    }
                )
            )

            response = client.get("/tasks/task-123/result")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert data["segments"] == [{"id": 1, "text": "Hello"}]
            assert data["full_text"] == "Hello world"

    @patch("api.routers.tasks._get_task_meta")
    def test_get_result_pending(self, mock_get_meta, tmp_path):
        with patch("api.routers.tasks.settings") as mock_settings:
            mock_settings.output_dir = str(tmp_path)
            mock_get_meta.return_value = {
                "status": "pending",
                "output_format": "json",
            }

            response = client.get("/tasks/task-123/result")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "pending"
            assert data["segments"] is None
            assert data["full_text"] is None

    @patch("api.routers.tasks._get_task_meta")
    def test_get_result_task_not_exists(self, mock_get_meta):
        mock_get_meta.return_value = {}

        response = client.get("/tasks/task-123/result")
        assert response.status_code == 404

    @patch("api.routers.tasks._get_task_meta")
    def test_get_result_corrupted_json(self, mock_get_meta, tmp_path):
        with patch("api.routers.tasks.settings") as mock_settings:
            mock_settings.output_dir = str(tmp_path)
            mock_get_meta.return_value = {
                "status": "completed",
                "output_format": "json",
            }

            output_file = tmp_path / "task-123.json"
            output_file.write_text("not valid json")

            response = client.get("/tasks/task-123/result")
            assert response.status_code == 200
            data = response.json()
            assert data["segments"] is None


class TestDeleteTask:
    @patch("api.routers.tasks._get_task_meta")
    @patch("api.routers.tasks.AsyncResult")
    def test_delete_completed_task(self, mock_async_result, mock_get_meta, tmp_path, mock_redis, mock_celery_app):
        with patch("api.routers.tasks.settings") as mock_settings:
            mock_settings.output_dir = str(tmp_path)
            mock_get_meta.return_value = {
                "status": "completed",
                "output_format": "json",
            }

            # 创建输出文件
            (tmp_path / "task-123.json").write_text('{"test": true}')
            (tmp_path / "task-123.mp4").write_text("video")

            response = client.delete("/tasks/task-123")

            assert response.status_code == 204
            mock_celery_app.control.revoke.assert_not_called()
            mock_redis.delete.assert_called_once_with("task_meta:task-123")
            mock_async_result.return_value.forget.assert_called_once()
            assert not (tmp_path / "task-123.json").exists()
            assert not (tmp_path / "task-123.mp4").exists()

    @patch("api.routers.tasks._get_task_meta")
    @patch("api.routers.tasks.AsyncResult")
    def test_delete_active_task(self, mock_async_result, mock_get_meta, tmp_path, mock_redis, mock_celery_app):
        with patch("api.routers.tasks.settings") as mock_settings:
            mock_settings.output_dir = str(tmp_path)
            mock_get_meta.return_value = {
                "status": "downloading",
                "output_format": "json",
            }

            response = client.delete("/tasks/task-123")

            assert response.status_code == 204
            mock_celery_app.control.revoke.assert_called_once_with("task-123", terminate=True)
            mock_redis.delete.assert_called_once_with("task_meta:task-123")
            mock_async_result.return_value.forget.assert_called_once()

    @patch("api.routers.tasks._get_task_meta")
    def test_delete_task_not_found(self, mock_get_meta):
        mock_get_meta.return_value = {}

        response = client.delete("/tasks/nonexistent")
        assert response.status_code == 404

    @patch("api.routers.tasks._get_task_meta")
    @patch("api.routers.tasks.AsyncResult")
    def test_delete_task_file_cleanup_error_ignored(
        self, mock_async_result, mock_get_meta, tmp_path, mock_redis, mock_celery_app
    ):
        with patch("api.routers.tasks.settings") as mock_settings:
            mock_settings.output_dir = str(tmp_path)
            mock_get_meta.return_value = {
                "status": "completed",
                "output_format": "json",
            }

            # 创建一个目录（而非文件）来触发 unlink 失败
            (tmp_path / "task-123.json").mkdir()

            response = client.delete("/tasks/task-123")

            assert response.status_code == 204
            mock_redis.delete.assert_called_once_with("task_meta:task-123")


class TestClearAllTasks:
    @patch("api.routers.tasks._get_task_meta")
    @patch("api.routers.tasks.AsyncResult")
    def test_clear_all_tasks(self, mock_async_result, mock_get_meta, tmp_path, mock_redis, mock_celery_app):
        with patch("api.routers.tasks.settings") as mock_settings:
            mock_settings.output_dir = str(tmp_path)
            mock_redis.keys.return_value = ["task_meta:task-1", "task_meta:task-2"]

            def side_effect(task_id):
                if task_id == "task-1":
                    return {"status": "completed", "output_format": "json"}
                return {"status": "downloading", "output_format": "txt"}

            mock_get_meta.side_effect = side_effect

            (tmp_path / "task-1.json").write_text("{}")
            (tmp_path / "task-2.txt").write_text("hello")

            response = client.delete("/tasks")

            assert response.status_code == 204
            assert mock_redis.delete.call_count == 2
            mock_celery_app.control.revoke.assert_called_once_with("task-2", terminate=True)
            assert mock_async_result.return_value.forget.call_count == 2
            assert not (tmp_path / "task-1.json").exists()
            assert not (tmp_path / "task-2.txt").exists()

    @patch("api.routers.tasks._get_task_meta")
    @patch("api.routers.tasks.AsyncResult")
    def test_clear_all_empty(self, mock_async_result, mock_get_meta, tmp_path, mock_redis, mock_celery_app):
        with patch("api.routers.tasks.settings") as mock_settings:
            mock_settings.output_dir = str(tmp_path)
            mock_redis.keys.return_value = []

            response = client.delete("/tasks")

            assert response.status_code == 204
            mock_redis.delete.assert_not_called()
            mock_celery_app.control.revoke.assert_not_called()

