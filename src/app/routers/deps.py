"""The provider functions: the only code that knows how FastAPI builds each layer.

The classes they build (repositories, services) stay plain Python and never import FastAPI.
"""

from typing import Annotated

from fastapi import Depends, Request

from ..core.settings import SettingsDep
from ..repositories.datasets import DatasetRepository
from ..repositories.storage import Storage
from ..services.datasets import DatasetService


def get_storage(request: Request) -> Storage:
    return request.app.state.storage


StorageDep = Annotated[Storage, Depends(get_storage)]


def get_dataset_repo(request: Request) -> DatasetRepository:
    return request.app.state.dataset_repo  # in memory until chapter 8


DatasetRepoDep = Annotated[DatasetRepository, Depends(get_dataset_repo)]


def get_dataset_service(repo: DatasetRepoDep, storage: StorageDep, settings: SettingsDep) -> DatasetService:
    return DatasetService(repo, storage, settings.max_upload_mb)


DatasetServiceDep = Annotated[DatasetService, Depends(get_dataset_service)]
