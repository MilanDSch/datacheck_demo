"""The provider functions: the only code that knows how FastAPI builds each layer."""

from typing import Annotated

from fastapi import Depends

from ..repositories.datasets import DatasetRepository
from ..repositories.storage import LocalStorage, Storage
from ..services.datasets import DatasetService

_repo = DatasetRepository()  # one shared store for the whole process, for now
_storage = LocalStorage("./uploads")


def get_dataset_repo() -> DatasetRepository:
    return _repo


DatasetRepoDep = Annotated[DatasetRepository, Depends(get_dataset_repo)]


def get_storage() -> Storage:
    return _storage


StorageDep = Annotated[Storage, Depends(get_storage)]


def get_dataset_service(repo: DatasetRepoDep, storage: StorageDep) -> DatasetService:
    return DatasetService(repo, storage, max_upload_mb=100)


DatasetServiceDep = Annotated[DatasetService, Depends(get_dataset_service)]
