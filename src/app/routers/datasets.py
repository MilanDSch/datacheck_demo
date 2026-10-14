from datetime import UTC, datetime

from fastapi import APIRouter, UploadFile

from ..schemas.datasets import DatasetOut

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("", response_model=DatasetOut, status_code=201)
def upload_dataset(file: UploadFile) -> DatasetOut:
    data = file.file.read()
    rows = len(data.decode("utf-8").splitlines()) - 1  # minus the header line
    return DatasetOut(id=1, name=file.filename or "upload.csv", rows=rows, created_at=datetime.now(UTC))
