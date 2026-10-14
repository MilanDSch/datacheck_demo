from fastapi import APIRouter, HTTPException, UploadFile

from ..schemas.datasets import DatasetOut
from ..services.datasets import InvalidUpload, TooLarge
from .deps import DatasetServiceDep

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("", response_model=DatasetOut, status_code=201)
def upload_dataset(file: UploadFile, service: DatasetServiceDep) -> DatasetOut:
    data = file.file.read()
    try:
        dataset = service.upload(file.filename or "upload.csv", data, owner_oid="local")
    except TooLarge:
        raise HTTPException(status_code=413, detail="file too large") from None
    except InvalidUpload as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    return DatasetOut.model_validate(dataset)


@router.get("", response_model=list[DatasetOut])
def list_datasets(service: DatasetServiceDep) -> list[DatasetOut]:
    return [DatasetOut.model_validate(d) for d in service.list_all()]
