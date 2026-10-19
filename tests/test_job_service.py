"""The job rules, tested without HTTP and without a database: the repositories are mocks."""

from unittest.mock import create_autospec

import pytest

from app.db.models import Job, JobStatus
from app.repositories.datasets import DatasetRepository
from app.repositories.jobs import JobRepository
from app.repositories.storage import FakeStorage
from app.services.errors import DatasetNotFound, JobNotFound, ReportNotReady
from app.services.jobs import JobService


@pytest.fixture
def jobs():
    return create_autospec(JobRepository, instance=True)


@pytest.fixture
def datasets():
    return create_autospec(DatasetRepository, instance=True)


@pytest.fixture
def service(jobs, datasets):
    return JobService(jobs, datasets, FakeStorage())


def test_start_creates_a_job_for_an_existing_dataset(service, jobs, datasets):
    datasets.get.return_value = object()
    service.start(7)
    jobs.create.assert_called_once_with(7)


def test_start_for_a_missing_dataset_raises_and_creates_nothing(service, jobs, datasets):
    datasets.get.return_value = None
    with pytest.raises(DatasetNotFound):
        service.start(7)
    jobs.create.assert_not_called()


def test_get_a_missing_job_raises(service, jobs):
    jobs.get.return_value = None
    with pytest.raises(JobNotFound):
        service.get(1)


@pytest.mark.parametrize("status", [JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.FAILED])
def test_report_is_not_ready_unless_the_job_is_done(service, jobs, status):
    jobs.get.return_value = Job(id=1, status=status)
    with pytest.raises(ReportNotReady) as raised:
        service.get_report(1)
    assert raised.value.status == status


def test_report_is_not_ready_when_done_without_a_score(service, jobs):
    jobs.get.return_value = Job(id=1, status=JobStatus.DONE, quality_score=None)
    with pytest.raises(ReportNotReady):
        service.get_report(1)


def test_report_of_a_done_job_is_its_score(service, jobs):
    jobs.get.return_value = Job(id=1, status=JobStatus.DONE, quality_score=88)
    assert service.get_report(1) == 88
