from quality import check_quality

from ..repositories.datasets import DatasetRepository
from ..repositories.jobs import JobRepository
from ..repositories.storage import Storage


class JobService:
    def __init__(self, jobs: JobRepository, datasets: DatasetRepository, storage: Storage) -> None:
        self.jobs = jobs
        self.datasets = datasets
        self.storage = storage

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
            job.quality_score = report.quality_score
            job.status = "done"
        except Exception as exc:  # a failed job must never crash the worker
            job.status = "failed"
            job.error = str(exc)[:500]
        self.jobs.session.commit()
        return True
