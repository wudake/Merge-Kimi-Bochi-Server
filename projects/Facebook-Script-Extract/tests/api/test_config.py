import os
from unittest.mock import patch

import pytest

from api.core.config import Settings, get_settings


class TestSettings:
    def test_default_values(self):
        s = Settings()
        assert s.app_name == "Facebook Video Script Extractor API"
        assert s.debug is False
        assert s.redis_url == "redis://localhost:6379/1"
        assert s.celery_broker_url == "redis://localhost:6379/1"
        assert s.celery_result_backend == "redis://localhost:6379/1"
        assert s.default_model_size == "tiny"
        assert s.default_device == "cpu"
        assert s.default_language == "en"
        assert s.temp_dir == "./temp"
        assert s.output_dir == "./output"
        assert s.openai_api_key is None
        assert s.result_retention_days == 7

    @patch.dict(os.environ, {"DEBUG": "true"}, clear=False)
    def test_env_override(self):
        s = Settings()
        assert s.debug is True

    @patch.dict(os.environ, {"REDIS_URL": "redis://custom:6380/1"}, clear=False)
    def test_redis_url_override(self):
        s = Settings()
        assert s.redis_url == "redis://custom:6380/1"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test123"}, clear=False)
    def test_openai_api_key(self):
        s = Settings()
        assert s.openai_api_key == "sk-test123"


class TestGetSettings:
    def test_returns_settings(self):
        s = get_settings()
        assert isinstance(s, Settings)

    def test_cached(self):
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

    def test_lru_cache_behavior(self):
        # 清除缓存后重新获取
        get_settings.cache_clear()
        s1 = get_settings()
        get_settings.cache_clear()
        s2 = get_settings()
        # 清除缓存后应该创建新实例（虽然内容相同）
        assert s1 is not s2
        assert s1.app_name == s2.app_name
