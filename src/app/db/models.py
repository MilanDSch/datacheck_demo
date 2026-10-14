from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(UTC)


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    owner_oid: Mapped[str] = mapped_column(String(64))
    file_key: Mapped[str] = mapped_column(String(200))  # pointer to the file in storage
    rows: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    jobs: Mapped[list["Job"]] = relationship(back_populates="dataset")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"))
    status: Mapped[str] = mapped_column(String(20), default="queued")  # queued, running, done, failed
    quality_score: Mapped[int | None] = mapped_column(default=None)
    error: Mapped[str | None] = mapped_column(String(500), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    dataset: Mapped[Dataset] = relationship(back_populates="jobs")
