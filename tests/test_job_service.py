"""The job rules, tested without HTTP and without a database: the repositories are mocks."""

from unittest.mock import create_autospec

import pytest

from app.core.auth import User
from app.db.models import Dataset, Job, JobStatus, Visibility
from app.repositories.datasets import DatasetRepository
from app.repositories.jobs import JobRepository
from app.repositories.storage import FakeStorage
from app.services.errors import DatasetNotFound, JobNotFound, ReportNotReady
from app.services.jobs import JobService

LOTTE = User(oid="oid-lotte", name="Lotte", roles=("Researcher",))
PIETER = User(oid="oid-pieter", name="Pieter", roles=("Viewer",))
ADMIN = User(oid="oid-admin", name="Admin", roles=("Admin",))


def dataset(visibility=Visibility.PRIVATE) -> Dataset:
    return Dataset(id=7, owner_oid=LOTTE.oid, visibility=visibility)


@pytest.fixture
def jobs():
    return create_autospec(JobRepository, instance=True)


@pytest.fixture
def datasets():
    repo = create_autospec(DatasetRepository, instance=True)
    repo.get.return_value = dataset()  # Lotte's private dataset, unless a test says otherwise
    return repo


@pytest.fixture
def service(jobs, datasets):
    return JobService(jobs, datasets, FakeStorage())


# ---- start ----
def test_owner_starts_a_job_on_their_dataset(service, jobs):
    service.start(7, LOTTE)
    jobs.create.assert_called_once_with(7, owner_oid=LOTTE.oid)


def test_anyone_may_start_a_job_on_a_public_dataset_and_owns_that_job(service, jobs, datasets):
    datasets.get.return_value = dataset(Visibility.PUBLIC)
    service.start(7, PIETER)
    jobs.create.assert_called_once_with(7, owner_oid=PIETER.oid)


def test_admin_may_start_a_job_on_a_private_dataset(service, jobs):
    service.start(7, ADMIN)
    jobs.create.assert_called_once_with(7, owner_oid=ADMIN.oid)


def test_start_on_someone_elses_private_dataset_looks_like_a_missing_dataset(service, jobs):
    with pytest.raises(DatasetNotFound):
        service.start(7, PIETER)
    jobs.create.assert_not_called()


def test_start_for_a_missing_dataset_raises_and_creates_nothing(service, jobs, datasets):
    datasets.get.return_value = None
    with pytest.raises(DatasetNotFound):
        service.start(7, LOTTE)
    jobs.create.assert_not_called()


# ---- get ----
def test_get_a_missing_job_raises(service, jobs):
    jobs.get.return_value = None
    with pytest.raises(JobNotFound):
        service.get(1, LOTTE)


@pytest.mark.parametrize("user", [LOTTE, ADMIN])
def test_owner_and_admin_may_read_a_job_on_a_private_dataset(service, jobs, user):
    job = Job(id=1, dataset_id=7, owner_oid=LOTTE.oid)
    jobs.get.return_value = job
    assert service.get(1, user) is job


def test_someone_elses_job_on_a_private_dataset_looks_like_a_missing_job(service, jobs):
    jobs.get.return_value = Job(id=1, dataset_id=7, owner_oid=LOTTE.oid)
    with pytest.raises(JobNotFound):
        service.get(1, PIETER)


def test_anyone_may_read_a_job_on_a_public_dataset(service, jobs, datasets):
    datasets.get.return_value = dataset(Visibility.PUBLIC)
    job = Job(id=1, dataset_id=7, owner_oid=LOTTE.oid)
    jobs.get.return_value = job
    assert service.get(1, PIETER) is job


def test_making_the_dataset_private_again_hides_the_job_from_others_but_not_its_owner(
    service, jobs, datasets
):
    jobs.get.return_value = Job(id=1, dataset_id=7, owner_oid=PIETER.oid)  # Pieter ran it on Lotte's dataset
    datasets.get.return_value = dataset(Visibility.PRIVATE)
    assert service.get(1, PIETER).id == 1
    stranger = User(oid="oid-x", name="X", roles=("Researcher",))
    with pytest.raises(JobNotFound):
        service.get(1, stranger)


def test_a_job_whose_dataset_is_gone_is_treated_as_private(service, jobs, datasets):
    datasets.get.return_value = None
    jobs.get.return_value = Job(id=1, dataset_id=7, owner_oid=LOTTE.oid)
    with pytest.raises(JobNotFound):
        service.get(1, PIETER)
    assert service.get(1, LOTTE).id == 1


# ---- report ----
@pytest.mark.parametrize("status", [JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.FAILED])
def test_report_is_not_ready_unless_the_job_is_done(service, jobs, status):
    jobs.get.return_value = Job(id=1, dataset_id=7, owner_oid=LOTTE.oid, status=status)
    with pytest.raises(ReportNotReady) as raised:
        service.get_report(1, LOTTE)
    assert raised.value.status == status


def test_report_is_not_ready_when_done_without_a_score(service, jobs):
    jobs.get.return_value = Job(
        id=1, dataset_id=7, owner_oid=LOTTE.oid, status=JobStatus.DONE, quality_score=None
    )
    with pytest.raises(ReportNotReady):
        service.get_report(1, LOTTE)


def test_report_of_a_done_job_is_its_score(service, jobs):
    jobs.get.return_value = Job(
        id=1, dataset_id=7, owner_oid=LOTTE.oid, status=JobStatus.DONE, quality_score=88
    )
    assert service.get_report(1, LOTTE) == 88


def test_admin_may_read_a_private_report(service, jobs):
    jobs.get.return_value = Job(
        id=1, dataset_id=7, owner_oid=LOTTE.oid, status=JobStatus.DONE, quality_score=88
    )
    assert service.get_report(1, ADMIN) == 88


def test_a_stranger_cannot_read_a_private_report(service, jobs):
    jobs.get.return_value = Job(
        id=1, dataset_id=7, owner_oid=LOTTE.oid, status=JobStatus.DONE, quality_score=88
    )
    with pytest.raises(JobNotFound):
        service.get_report(1, PIETER)


def test_anyone_may_read_a_report_on_a_public_dataset(service, jobs, datasets):
    datasets.get.return_value = dataset(Visibility.PUBLIC)
    jobs.get.return_value = Job(
        id=1, dataset_id=7, owner_oid=LOTTE.oid, status=JobStatus.DONE, quality_score=88
    )
    assert service.get_report(1, PIETER) == 88
