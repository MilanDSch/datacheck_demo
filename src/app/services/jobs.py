from typing import TYPE_CHECKING

from quality import check_quality

from ..db.models import Job, JobStatus
from ..repositories.datasets import DatasetRepository
from ..repositories.jobs import JobRepository
from ..repositories.storage import Storage
from .errors import DatasetNotFound, JobNotFound, ReportNotReady

if TYPE_CHECKING:
    from ..core.auth import User


class JobService:
    def __init__(self, jobs: JobRepository, datasets: DatasetRepository, storage: Storage) -> None:
        self.jobs = jobs
        self.datasets = datasets
        self.storage = storage

    def start(self, dataset_id: int, user: "User") -> Job:
        if self.datasets.get(dataset_id) is None:
            raise DatasetNotFound
        return self.jobs.create(dataset_id, owner_oid=user.oid)

    def get(self, job_id: int) -> Job:
        job = self.jobs.get(job_id)
        if job is None:
            raise JobNotFound
        return job

    def get_report(self, job_id: int) -> int:
        """The quality score of a finished job. Raises ReportNotReady until then."""
        job = self.get(job_id)
        if job.status != JobStatus.DONE or job.quality_score is None:
            raise ReportNotReady(job.status)
        return job.quality_score

    def run_next(self) -> bool:
        """The worker calls this. Returns False when there is nothing to do."""
        job = self.jobs.claim_next()
        if job is None:
            return False
        try:
            dataset = self.datasets.get(job.dataset_id)
            if dataset is None:
                raise ValueError("dataset no longer exists")
            report = check_quality(self.storage.load(dataset.file_key).decode("utf-8"))
            self.jobs.mark_done(job, report.quality_score)
        except Exception as exc:  # a failed job must never crash the worker
            self.jobs.mark_failed(job, str(exc))
        return True
