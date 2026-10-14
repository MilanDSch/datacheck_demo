import csv
import io
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

from ..schemas.datasets import DatasetOut

router = APIRouter(prefix="/datasets", tags=["datasets"])

MAX_UPLOAD_MB = 100
UPLOAD_DIR = Path("./uploads")
DATASETS: list[DatasetOut] = []  # lives in memory: gone on every restart


@router.post("", response_model=DatasetOut, status_code=201)
def upload_dataset(file: UploadFile) -> DatasetOut:
    data = file.file.read()
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail="file too large")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="not a text CSV file") from None
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or "time" not in reader.fieldnames:
        raise HTTPException(status_code=400, detail="no 'time' column")
    rows = sum(1 for _ in reader)
    UPLOAD_DIR.mkdir(exist_ok=True)
    (UPLOAD_DIR / f"{uuid.uuid4().hex}.csv").write_bytes(data)
    dataset = DatasetOut(
        id=len(DATASETS) + 1, name=file.filename or "upload.csv", rows=rows, created_at=datetime.now(UTC)
    )
    DATASETS.append(dataset)
    return dataset


@router.get("", response_model=list[DatasetOut])
def list_datasets() -> list[DatasetOut]:
    return DATASETS
