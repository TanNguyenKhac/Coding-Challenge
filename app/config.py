from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./chemistry.db"
    artifacts_dir: str = "./artifacts/videos"

    codex_api_base: Optional[str] = None
    codex_api_key: str = "no-key-needed"
    codex_model: str = "qwen2.5:7b"

    anthropic_api_key: Optional[str] = None

    max_retries: int = 2
    max_concurrent_jobs: int = 2


settings = Settings()
