from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Response, UploadFile

from ..core.auth import User, require_role
from ..core.flags import require_flag
from ..core.settings import SettingsDep
from ..db.models import Visibility
from ..schemas.datasets import DatasetOut, DatasetVisibilityUpdate
from ..services.datasets import InvalidUpload, TooLarge
from ..services.errors import DatasetNotFound, NotAllowed
from .deps import DatasetServiceDep

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("", response_model=DatasetOut, status_code=201)
def upload_dataset(
    file: UploadFile,
    settings: SettingsDep,
    service: DatasetServiceDep,
    visibility: Annotated[Visibility, Form()] = Visibility.PRIVATE,
    user: User = Depends(require_role("Researcher", "Admin")),
) -> DatasetOut:
    limit = settings.max_upload_mb * 1024 * 1024
    data = file.file.read(limit + 1)  # never read more than the limit plus one byte
    try:
        dataset = service.upload(
            file.filename or "upload.csv", data, owner_oid=user.oid, visibility=visibility
        )
    except TooLarge:
        raise HTTPException(status_code=413, detail="file too large") from None
    except InvalidUpload as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    return DatasetOut.model_validate(dataset)


@router.get("", response_model=list[DatasetOut])
def list_datasets(
    service: DatasetServiceDep,
    user: User = Depends(require_role("Viewer", "Researcher", "Admin")),
) -> list[DatasetOut]:
    return [DatasetOut.model_validate(d) for d in service.list_visible(user)]


@router.get("/export.csv", dependencies=[Depends(require_flag("csv_export"))])
def export_datasets(
    service: DatasetServiceDep,
    user: User = Depends(require_role("Researcher", "Admin")),
) -> Response:
    lines = ["id,name,rows"] + [f"{d.id},{d.name},{d.rows}" for d in service.list_visible(user)]
    return Response(chr(10).join(lines) + chr(10), media_type="text/csv")


@router.patch("/{dataset_id}", response_model=DatasetOut)
def set_dataset_visibility(
    dataset_id: int,
    body: DatasetVisibilityUpdate,
    service: DatasetServiceDep,
    user: User = Depends(require_role("Researcher", "Admin")),
) -> DatasetOut:
    try:
        return DatasetOut.model_validate(service.set_visibility(dataset_id, user, body.visibility))
    except DatasetNotFound:
        raise HTTPException(status_code=404, detail="dataset not found") from None
    except NotAllowed:
        raise HTTPException(status_code=403, detail="you may only change your own datasets") from None


@router.delete("/{dataset_id}", status_code=204)
def delete_dataset(
    dataset_id: int,
    service: DatasetServiceDep,
    user: User = Depends(require_role("Researcher", "Admin")),
) -> None:
    try:
        service.delete(dataset_id, user)
    except DatasetNotFound:
        raise HTTPException(status_code=404, detail="dataset not found") from None
    except NotAllowed:
        raise HTTPException(status_code=403, detail="you may only delete your own datasets") from None
