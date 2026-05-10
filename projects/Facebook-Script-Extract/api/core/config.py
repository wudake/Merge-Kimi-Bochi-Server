from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 应用
    app_name: str = "Facebook Video Script Extractor API"
    debug: bool = False

    # Redis / Celery (整合系统使用 DB 1)
    redis_url: str = "redis://localhost:6379/1"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/1"

    # 模型默认参数
    default_model_size: str = "tiny"
    default_device: str = "cpu"
    default_language: str = "en"

    # 路径
    temp_dir: str = "./temp"
    output_dir: str = "./output"

    # OpenAI（可选）
    openai_api_key: str | None = None

    # 结果保留天数
    result_retention_days: int = 7

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
