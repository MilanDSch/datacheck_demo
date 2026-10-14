from fastapi import APIRouter, Depends, HTTPException, UploadFile

from ..core.auth import User, require_role
from ..core.settings import SettingsDep
from ..schemas.datasets import DatasetOut
from ..services.datasets import InvalidUpload, TooLarge
from .deps import DatasetServiceDep

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("", response_model=DatasetOut, status_code=201)
def upload_dataset(
    file: UploadFile,
    settings: SettingsDep,
    service: DatasetServiceDep,
    user: User = Depends(require_role("Researcher", "Admin")),
) -> DatasetOut:
    limit = settings.max_upload_mb * 1024 * 1024
    data = file.file.read(limit + 1)  # never read more than the limit plus one byte
    try:
        dataset = service.upload(file.filename or "upload.csv", data, owner_oid=user.oid)
    except TooLarge:
        raise HTTPException(status_code=413, detail="file too large") from None
    except InvalidUpload as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    return DatasetOut.model_validate(dataset)


@router.get("", response_model=list[DatasetOut])
def list_datasets(
    service: DatasetServiceDep,
    _: User = Depends(require_role("Viewer", "Researcher", "Admin")),
) -> list[DatasetOut]:
    return [DatasetOut.model_validate(d) for d in service.list_all()]
