from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import Job


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
            .where(Job.status == "queued")
            .order_by(Job.id)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        job = self.session.scalars(stmt).first()
        if job is not None:
            job.status = "running"
            self.session.commit()
        return job
