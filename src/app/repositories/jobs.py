from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import Job, JobStatus


class JobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, dataset_id: int) -> Job:
        job = Job(dataset_id=dataset_id)
        self.session.add(job)
        self.session.commit()
        return job

    def get(self, job_id: int) -> Job | None:
        return self.session.get(Job, job_id)

    def claim_next(self) -> Job | None:
        """Take the oldest queued job. On Postgres, skip_locked stops two workers claiming the same row."""
        stmt = (
            select(Job)
            .where(Job.status == JobStatus.QUEUED)
            .order_by(Job.id)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        job = self.session.scalars(stmt).first()
        if job is not None:
            job.status = JobStatus.RUNNING
            self.session.commit()
        return job

    def mark_done(self, job: Job, quality_score: int) -> None:
        job.quality_score = quality_score
        job.status = JobStatus.DONE
        self.session.commit()

    def mark_failed(self, job: Job, error: str) -> None:
        job.status = JobStatus.FAILED
        job.error = error[:500]
        self.session.commit()
