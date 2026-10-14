from fastapi import FastAPI

from .core.auth import TokenValidator, entra_validator
from .core.settings import Settings, get_settings
from .repositories.datasets import DatasetRepository
from .repositories.storage import LocalStorage, Storage
from .routers import datasets, me


def create_app(
    settings: Settings | None = None,
    storage: Storage | None = None,
    validator: TokenValidator | None = None,
) -> FastAPI:
    """The composition root: the one place that decides what gets plugged in."""
    settings = settings or get_settings()
    app = FastAPI(title="DataCheck API")
    app.state.settings = settings
    app.state.storage = storage or LocalStorage(settings.upload_dir)
    app.state.dataset_repo = DatasetRepository()  # in memory until chapter 8
    if settings.auth_mode == "entra":
        app.state.validator = validator or entra_validator(settings.tenant_id, settings.api_client_id)
    for router in (me.router, datasets.router):
        app.include_router(router, prefix="/api/v1")
    return app
