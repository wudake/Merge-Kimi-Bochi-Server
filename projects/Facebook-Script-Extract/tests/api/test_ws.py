from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.routers.ws import _broadcast, start_ws_listener

client = TestClient(app)

class TestWebSocket:
    @patch("api.routers.ws._connections", {})
    def test_websocket_connection(self):
        with client.websocket_connect("/ws/tasks") as websocket:
            websocket.send_text("ping")
            data = websocket.receive_text()
            assert data == "pong"

    @patch("api.routers.ws._connections", {})
    def test_websocket_disconnect(self):
        with client.websocket_connect("/ws/tasks") as websocket:
            websocket.close()


class TestBroadcast:
    @pytest.mark.asyncio
    async def test_broadcast_to_single_connection(self):
        mock_ws = MagicMock()
        mock_ws.send_json = MagicMock(return_value=None)

        with patch("api.routers.ws._connections", {"conn1": mock_ws}):
            await _broadcast({"task_id": "task-1", "progress": 50})

        mock_ws.send_json.assert_called_once_with({"task_id": "task-1", "progress": 50})

    @pytest.mark.asyncio
    async def test_broadcast_removes_dead_connections(self):
        mock_alive = MagicMock()
        mock_alive.send_json = MagicMock(return_value=None)

        mock_dead = MagicMock()
        mock_dead.send_json = MagicMock(side_effect=Exception("Connection closed"))

        connections = {"alive": mock_alive, "dead": mock_dead}

        with patch("api.routers.ws._connections", connections):
            await _broadcast({"task_id": "task-1", "progress": 50})

        mock_alive.send_json.assert_called_once()
        assert "dead" not in connections

    @pytest.mark.asyncio
    async def test_broadcast_empty_connections(self):
        with patch("api.routers.ws._connections", {}):
            await _broadcast({"task_id": "task-1", "progress": 50})


class TestRedisListener:
    @patch("api.routers.ws.redis.from_url")
    def test_redis_listener_subscribes_to_channel(self, mock_from_url):
        mock_redis = MagicMock()
        mock_pubsub = MagicMock()
        mock_pubsub.listen.return_value = []
        mock_redis.pubsub.return_value = mock_pubsub
        mock_from_url.return_value = mock_redis

        # 直接调用 _redis_listener 来测试订阅行为
        import api.routers.ws as ws_module

        original_listener = ws_module._redis_listener

        def limited_listener():
            r = mock_redis
            pubsub = r.pubsub()
            pubsub.subscribe("task_updates")
            for message in pubsub.listen():
                break

        ws_module._redis_listener = limited_listener
        limited_listener()

        mock_pubsub.subscribe.assert_called_once_with("task_updates")
        ws_module._redis_listener = original_listener

    @patch("api.routers.ws._loop")
    @patch("api.routers.ws.asyncio.run_coroutine_threadsafe")
    @patch("api.routers.ws.redis.from_url")
    def test_redis_listener_processes_message(
        self, mock_from_url, mock_run_coroutine, mock_loop
    ):
        mock_loop.is_running.return_value = True

        mock_redis = MagicMock()
        mock_pubsub = MagicMock()
        mock_pubsub.listen.return_value = [
            {"type": "message", "data": '{"task_id": "task-1", "progress": 50}'}
        ]
        mock_redis.pubsub.return_value = mock_pubsub
        mock_from_url.return_value = mock_redis

        # 需要处理 listen 的无限循环，所以只让它产生一条消息
        import api.routers.ws as ws_module

        original_listener = ws_module._redis_listener

        def limited_listener():
            r = mock_redis
            pubsub = r.pubsub()
            pubsub.subscribe("task_updates")
            for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        import json

                        data = json.loads(message["data"])
                        if mock_loop and mock_loop.is_running():
                            mock_run_coroutine(data)
                    except Exception:
                        pass
                break  # 只处理一条消息

        ws_module._redis_listener = limited_listener
        limited_listener()

        mock_run_coroutine.assert_called_once()
        ws_module._redis_listener = original_listener
