"""The dataset rules, tested without HTTP and without a database: the repository is a mock."""

from unittest.mock import create_autospec

import pytest

from app.core.auth import User
from app.db.models import Dataset
from app.repositories.datasets import DatasetRepository
from app.repositories.storage import FakeStorage
from app.services.datasets import DatasetService
from app.services.errors import DatasetNotFound, NotAllowed

OWNER = User(oid="oid-owner", name="Owner", roles=("Researcher",))
OTHER = User(oid="oid-other", name="Other", roles=("Researcher",))
ADMIN = User(oid="oid-admin", name="Admin", roles=("Admin",))


@pytest.fixture
def repo():
    return create_autospec(DatasetRepository, instance=True)


@pytest.fixture
def service(repo):
    return DatasetService(repo, FakeStorage(), max_upload_mb=1)


def test_owner_may_delete_their_dataset(service, repo):
    dataset = Dataset(id=1, owner_oid=OWNER.oid)
    repo.get.return_value = dataset
    service.delete(1, OWNER)
    repo.delete.assert_called_once_with(dataset)


def test_admin_may_delete_anyones_dataset(service, repo):
    dataset = Dataset(id=1, owner_oid=OWNER.oid)
    repo.get.return_value = dataset
    service.delete(1, ADMIN)
    repo.delete.assert_called_once_with(dataset)


def test_someone_else_may_not_delete_and_nothing_is_deleted(service, repo):
    repo.get.return_value = Dataset(id=1, owner_oid=OWNER.oid)
    with pytest.raises(NotAllowed):
        service.delete(1, OTHER)
    repo.delete.assert_not_called()


def test_deleting_a_missing_dataset_raises(service, repo):
    repo.get.return_value = None
    with pytest.raises(DatasetNotFound):
        service.delete(1, OWNER)
    repo.delete.assert_not_called()
