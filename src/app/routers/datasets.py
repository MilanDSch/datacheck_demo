from fastapi import APIRouter, UploadFile

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("")
def upload_dataset(file: UploadFile):
    data = file.file.read()
    return {"filename": file.filename, "size": len(data)}
