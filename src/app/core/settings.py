from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Request
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")  # .env has keys we do not use today

    database_url: str = "sqlite:///./datacheck.db"
    upload_dir: str = "./uploads"
    max_upload_mb: int = 100
    feature_csv_export: bool = False  # a feature flag: off until we are ready


@lru_cache
def get_settings() -> Settings:
    return Settings()


def current_settings(request: Request) -> Settings:
    """The settings the app was built with (create_app puts them on app.state)."""
    return request.app.state.settings


SettingsDep = Annotated[Settings, Depends(current_settings)]
