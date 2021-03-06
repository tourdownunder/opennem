from typing import Optional

from pydantic import BaseSettings, PostgresDsn, RedisDsn
from scrapy.settings import Settings
from scrapy.utils.project import get_project_settings


class OpennemSettings(BaseSettings):
    env: str = "development"
    db_url: PostgresDsn = "postgresql://opennem:opennem@127.0.0.1:15433/opennem"
    cache_url: RedisDsn = "redis://127.0.0.1"
    sentry_url: Optional[str]

    google_places_api_key: str
    requests_cache_path: str = ".requests"

    slack_hook_url: Optional[str]

    # @todo overwrite scrapy settings here
    scrapy: Optional[Settings] = get_project_settings()

    class Config:
        env_file = ".env"
        fields = {
            "env": {"env": "ENV"},
            "db_url": {"env": "DATABASE_HOST_URL"},
            "cache_url": {"env": "REDIS_HOST_URL"},
            "sentry_url": {"env": "SENTRY_URL"},
            "slack_hook_url": {"env": "WATCHDOG_SLACK_HOOK"},
        }
