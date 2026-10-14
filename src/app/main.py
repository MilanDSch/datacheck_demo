from fastapi import FastAPI

from .core.settings import Settings, get_settings
from .db.session import make_engine
from .repositories.storage import LocalStorage, Storage
from .routers import datasets, jobs


def create_app(
    settings: Settings | None = None,
    storage: Storage | None = None,
) -> FastAPI:
    """The composition root: the one place that decides what gets plugged in.

    The tables are not created here: Alembic owns the schema (alembic upgrade head).
    """
    settings = settings or get_settings()
    app = FastAPI(title="DataCheck API")
    app.state.settings = settings
    app.state.engine = make_engine(settings.database_url)
    app.state.storage = storage or LocalStorage(settings.upload_dir)
    for router in (datasets.router, jobs.router):
        app.include_router(router, prefix="/api/v1")
    return app
