"""The dataset rules, tested without HTTP and without a database: the repository is a mock."""

from unittest.mock import create_autospec

import pytest

from app.core.auth import User
from app.db.models import Dataset, Visibility
from app.repositories.datasets import DatasetRepository
from app.repositories.storage import FakeStorage
from app.services.datasets import DatasetService
from app.services.errors import DatasetNotFound, NotAllowed

OWNER = User(oid="oid-owner", name="Owner", roles=("Researcher",))
OTHER = User(oid="oid-other", name="Other", roles=("Researcher",))
VIEWER = User(oid="oid-viewer", name="Viewer", roles=("Viewer",))
ADMIN = User(oid="oid-admin", name="Admin", roles=("Admin",))


def private() -> Dataset:
    return Dataset(id=1, owner_oid=OWNER.oid, visibility=Visibility.PRIVATE)


def public() -> Dataset:
    return Dataset(id=1, owner_oid=OWNER.oid, visibility=Visibility.PUBLIC)


@pytest.fixture
def repo():
    return create_autospec(DatasetRepository, instance=True)


@pytest.fixture
def service(repo):
    return DatasetService(repo, FakeStorage(), max_upload_mb=1)


# ---- upload ----
def test_upload_is_private_unless_asked_otherwise(service, repo):
    service.upload("a.csv", b"time,x\n0,1\n", owner_oid=OWNER.oid)
    assert repo.create.call_args.kwargs["visibility"] == Visibility.PRIVATE


def test_upload_may_be_public(service, repo):
    service.upload("a.csv", b"time,x\n0,1\n", owner_oid=OWNER.oid, visibility=Visibility.PUBLIC)
    assert repo.create.call_args.kwargs["visibility"] == Visibility.PUBLIC


# ---- reading ----
@pytest.mark.parametrize("user", [OWNER, ADMIN])
def test_owner_and_admin_may_read_a_private_dataset(service, repo, user):
    repo.get.return_value = private()
    assert service.get(1, user).id == 1


@pytest.mark.parametrize("user", [OTHER, VIEWER])
def test_strangers_may_not_read_a_private_dataset(service, repo, user):
    repo.get.return_value = private()
    with pytest.raises(DatasetNotFound):
        service.get(1, user)


@pytest.mark.parametrize("user", [OWNER, OTHER, VIEWER, ADMIN])
def test_everyone_may_read_a_public_dataset(service, repo, user):
    repo.get.return_value = public()
    assert service.get(1, user).id == 1


def test_reading_a_missing_dataset_raises(service, repo):
    repo.get.return_value = None
    with pytest.raises(DatasetNotFound):
        service.get(1, OWNER)


# ---- listing ----
def test_admin_lists_everything(service, repo):
    service.list_visible(ADMIN)
    repo.list_all.assert_called_once_with()
    repo.list_readable_by.assert_not_called()


def test_others_list_their_own_and_the_public_ones(service, repo):
    service.list_visible(OTHER)
    repo.list_readable_by.assert_called_once_with(OTHER.oid)
    repo.list_all.assert_not_called()


# ---- deleting ----
@pytest.mark.parametrize("dataset", [private, public])
@pytest.mark.parametrize("user", [OWNER, ADMIN])
def test_owner_and_admin_may_delete_either_kind(service, repo, dataset, user):
    repo.get.return_value = found = dataset()
    service.delete(1, user)
    repo.delete.assert_called_once_with(found)


def test_deleting_someone_elses_public_dataset_is_not_allowed(service, repo):
    repo.get.return_value = public()
    with pytest.raises(NotAllowed):
        service.delete(1, OTHER)
    repo.delete.assert_not_called()


def test_deleting_someone_elses_private_dataset_looks_like_a_missing_one(service, repo):
    repo.get.return_value = private()
    with pytest.raises(DatasetNotFound):
        service.delete(1, OTHER)
    repo.delete.assert_not_called()


def test_deleting_a_missing_dataset_raises(service, repo):
    repo.get.return_value = None
    with pytest.raises(DatasetNotFound):
        service.delete(1, OWNER)
    repo.delete.assert_not_called()


# ---- changing visibility ----
@pytest.mark.parametrize("user", [OWNER, ADMIN])
def test_owner_and_admin_may_change_visibility(service, repo, user):
    repo.get.return_value = found = private()
    service.set_visibility(1, user, Visibility.PUBLIC)
    repo.set_visibility.assert_called_once_with(found, Visibility.PUBLIC)


def test_a_stranger_may_not_publish_someone_elses_public_dataset(service, repo):
    repo.get.return_value = public()
    with pytest.raises(NotAllowed):
        service.set_visibility(1, OTHER, Visibility.PRIVATE)
    repo.set_visibility.assert_not_called()


def test_a_stranger_cannot_even_find_a_private_dataset_to_publish_it(service, repo):
    repo.get.return_value = private()
    with pytest.raises(DatasetNotFound):
        service.set_visibility(1, OTHER, Visibility.PUBLIC)
    repo.set_visibility.assert_not_called()
