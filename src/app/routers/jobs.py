from fastapi import APIRouter, HTTPException

from ..schemas.jobs import JobCreate, JobOut, ReportOut
from .deps import DatasetRepoDep, JobRepoDep

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobOut, status_code=202)
def start_job(body: JobCreate, datasets: DatasetRepoDep, jobs: JobRepoDep) -> JobOut:
    if datasets.get(body.dataset_id) is None:
        raise HTTPException(status_code=404, detail="dataset not found")
    return JobOut.model_validate(jobs.create(body.dataset_id))


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, jobs: JobRepoDep) -> JobOut:
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return JobOut.model_validate(job)


@router.get("/{job_id}/report", response_model=ReportOut)
def get_report(job_id: int, jobs: JobRepoDep) -> ReportOut:
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    if job.status != "done" or job.quality_score is None:
        raise HTTPException(status_code=409, detail=f"report not ready, job is {job.status}")
    return ReportOut(job_id=job.id, quality_score=job.quality_score)
