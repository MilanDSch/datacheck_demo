from fastapi import APIRouter, Depends, HTTPException

from ..core.auth import User, get_current_user, require_role
from ..schemas.jobs import JobCreate, JobOut, ReportOut
from ..services.errors import DatasetNotFound, JobNotFound, ReportNotReady
from .deps import JobServiceDep

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobOut, status_code=202)
def start_job(
    body: JobCreate,
    service: JobServiceDep,
    _: User = Depends(require_role("Researcher", "Admin")),
) -> JobOut:
    try:
        return JobOut.model_validate(service.start(body.dataset_id))
    except DatasetNotFound:
        raise HTTPException(status_code=404, detail="dataset not found") from None


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, service: JobServiceDep, _: User = Depends(get_current_user)) -> JobOut:
    try:
        return JobOut.model_validate(service.get(job_id))
    except JobNotFound:
        raise HTTPException(status_code=404, detail="job not found") from None


@router.get("/{job_id}/report", response_model=ReportOut)
def get_report(job_id: int, service: JobServiceDep, _: User = Depends(get_current_user)) -> ReportOut:
    try:
        score = service.get_report(job_id)
    except JobNotFound:
        raise HTTPException(status_code=404, detail="job not found") from None
    except ReportNotReady as exc:
        raise HTTPException(status_code=409, detail=f"report not ready, job is {exc.status}") from None
    return ReportOut(job_id=job_id, quality_score=score)
