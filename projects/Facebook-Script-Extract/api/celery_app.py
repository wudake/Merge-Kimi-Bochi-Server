from celery import Celery

from api.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "transcriber",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["api.tasks.worker"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1小时超时
    worker_prefetch_multiplier=1,
)
