from functools import lru_cache
from typing import Annotated, Literal, Self

from fastapi import Depends, Request
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str = "sqlite:///./datacheck.db"
    upload_dir: str = "./uploads"
    max_upload_mb: int = 100
    auth_mode: Literal["off", "entra"] = "off"  # "off" is for local development only
    tenant_id: str = ""
    api_client_id: str = ""
    feature_csv_export: bool = False  # a feature flag: off until we are ready

    @model_validator(mode="after")
    def entra_needs_ids(self) -> Self:
        """Fail fast: real tokens cannot be checked without the tenant and the API id."""
        if self.auth_mode == "entra" and not (self.tenant_id and self.api_client_id):
            raise ValueError("AUTH_MODE=entra needs TENANT_ID and API_CLIENT_ID")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


def current_settings(request: Request) -> Settings:
    """The settings the app was built with (create_app puts them on app.state)."""
    return request.app.state.settings


SettingsDep = Annotated[Settings, Depends(current_settings)]
