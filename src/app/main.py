from fastapi import FastAPI

from .core.settings import Settings, get_settings
from .repositories.datasets import DatasetRepository
from .repositories.storage import LocalStorage, Storage
from .routers import datasets


def create_app(
    settings: Settings | None = None,
    storage: Storage | None = None,
) -> FastAPI:
    """The composition root: the one place that decides what gets plugged in."""
    settings = settings or get_settings()
    app = FastAPI(title="DataCheck API")
    app.state.settings = settings
    app.state.storage = storage or LocalStorage(settings.upload_dir)
    app.state.dataset_repo = DatasetRepository()  # in memory until chapter 8
    for router in (datasets.router,):
        app.include_router(router, prefix="/api/v1")
    return app
