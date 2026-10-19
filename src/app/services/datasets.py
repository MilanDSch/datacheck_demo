import csv
import io
import uuid
from typing import TYPE_CHECKING

from ..db.models import Dataset, Visibility
from ..repositories.datasets import DatasetRepository
from ..repositories.storage import Storage
from .access import can_read, is_admin, owns_or_admin
from .errors import DatasetNotFound, NotAllowed

if TYPE_CHECKING:
    from ..core.auth import User


class InvalidUpload(Exception):
    """The caller sent something we refuse. The router turns this into a 400."""


class TooLarge(Exception):
    """The file is over the limit. The router turns this into a 413."""


class DatasetService:
    def __init__(self, repo: DatasetRepository, storage: Storage, max_upload_mb: int) -> None:
        self.repo = repo
        self.storage = storage
        self.max_bytes = max_upload_mb * 1024 * 1024

    def upload(
        self,
        filename: str,
        data: bytes,
        owner_oid: str,
        visibility: Visibility = Visibility.PRIVATE,
    ) -> Dataset:
        if len(data) > self.max_bytes:
            raise TooLarge
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise InvalidUpload("not a text CSV file") from exc
        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames or "time" not in reader.fieldnames:
            raise InvalidUpload("no 'time' column")
        rows = sum(1 for _ in reader)
        file_key = f"{uuid.uuid4().hex}.csv"  # our own name, never the caller's filename
        self.storage.save(file_key, data)
        return self.repo.create(
            name=filename, owner_oid=owner_oid, file_key=file_key, rows=rows, visibility=visibility
        )

    def list_visible(self, user: "User") -> list[Dataset]:
        """Admins see everything; everyone else sees their own datasets and the public ones."""
        if is_admin(user):
            return self.repo.list_all()
        return self.repo.list_readable_by(user.oid)

    def get(self, dataset_id: int, user: "User") -> Dataset:
        """A dataset you may not read looks exactly like a missing one, so private ids do not leak."""
        dataset = self.repo.get(dataset_id)
        if dataset is None or not can_read(user, dataset.owner_oid, dataset.visibility):
            raise DatasetNotFound
        return dataset

    def set_visibility(self, dataset_id: int, user: "User", visibility: Visibility) -> Dataset:
        dataset = self._get_for_change(dataset_id, user)
        self.repo.set_visibility(dataset, visibility)
        return dataset

    def delete(self, dataset_id: int, user: "User") -> None:
        self.repo.delete(self._get_for_change(dataset_id, user))

    def _get_for_change(self, dataset_id: int, user: "User") -> Dataset:
        """Not readable: DatasetNotFound. Readable (public) but not yours: NotAllowed."""
        dataset = self.get(dataset_id, user)
        if not owns_or_admin(user, dataset.owner_oid):
            raise NotAllowed
        return dataset
