from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.core.config import get_settings
from api.routers import health, tasks, ws

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    ws.start_ws_listener()
    yield


app = FastAPI(
    title=settings.app_name,
    description="将 Facebook / YouTube 视频音频提取并转写为文字脚本的后端 API",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(tasks.router)
app.include_router(ws.router)


@app.get("/")
def root():
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs",
    }
