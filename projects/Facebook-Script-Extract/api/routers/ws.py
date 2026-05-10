import asyncio
import json
import threading
from typing import Dict

import redis
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from api.core.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/ws", tags=["websocket"])

# 活跃的 WebSocket 连接
_connections: Dict[str, WebSocket] = {}
_loop: asyncio.AbstractEventLoop | None = None


async def _broadcast(data: dict):
    """向所有连接广播消息"""
    dead = []
    for conn_id, ws in list(_connections.items()):
        try:
            await ws.send_json(data)
        except Exception:
            dead.append(conn_id)
    for conn_id in dead:
        _connections.pop(conn_id, None)


def _redis_listener():
    """在后台线程中监听 Redis pub/sub，收到消息后通过事件循环广播"""
    r = redis.from_url(settings.redis_url, decode_responses=True)
    pubsub = r.pubsub()
    pubsub.subscribe("task_updates")
    for message in pubsub.listen():
        if message["type"] == "message":
            try:
                data = json.loads(message["data"])
                if _loop and _loop.is_running():
                    asyncio.run_coroutine_threadsafe(_broadcast(data), _loop)
            except Exception:
                pass


def start_ws_listener():
    """启动 Redis 监听线程（应在应用启动时调用）"""
    global _loop
    _loop = asyncio.get_event_loop()
    threading.Thread(target=_redis_listener, daemon=True).start()


@router.websocket("/tasks")
async def task_websocket(websocket: WebSocket):
    # Nginx auth_request 已在升级 WebSocket 前完成鉴权
    await websocket.accept()
    conn_id = f"{id(websocket)}"
    _connections[conn_id] = websocket
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        _connections.pop(conn_id, None)
    except Exception:
        _connections.pop(conn_id, None)
