"""The provider functions: the only code that knows how FastAPI builds each layer.

The classes they build (repositories, services) stay plain Python and never import FastAPI.
"""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from ..core.settings import SettingsDep
from ..db.session import new_session
from ..repositories.datasets import DatasetRepository
from ..repositories.storage import Storage
from ..services.datasets import DatasetService


def get_session(request: Request) -> Iterator[Session]:
    """One session per request: open before the endpoint runs, always closed afterwards."""
    with new_session(request.app.state.engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


def get_storage(request: Request) -> Storage:
    return request.app.state.storage


StorageDep = Annotated[Storage, Depends(get_storage)]


def get_dataset_repo(session: SessionDep) -> DatasetRepository:
    return DatasetRepository(session)


DatasetRepoDep = Annotated[DatasetRepository, Depends(get_dataset_repo)]


def get_dataset_service(repo: DatasetRepoDep, storage: StorageDep, settings: SettingsDep) -> DatasetService:
    return DatasetService(repo, storage, settings.max_upload_mb)


DatasetServiceDep = Annotated[DatasetService, Depends(get_dataset_service)]
