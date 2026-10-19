from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import Dataset, Visibility


class DatasetRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        name: str,
        owner_oid: str,
        file_key: str,
        rows: int,
        visibility: Visibility = Visibility.PRIVATE,
    ) -> Dataset:
        dataset = Dataset(
            name=name, owner_oid=owner_oid, file_key=file_key, rows=rows, visibility=visibility.value
        )
        self.session.add(dataset)
        self.session.commit()
        return dataset

    def get(self, dataset_id: int) -> Dataset | None:
        return self.session.get(Dataset, dataset_id)

    def list_all(self) -> list[Dataset]:
        return list(self.session.scalars(select(Dataset).order_by(Dataset.id)))

    def list_readable_by(self, owner_oid: str) -> list[Dataset]:
        """The datasets this owner may read: their own plus every public one."""
        stmt = (
            select(Dataset)
            .where((Dataset.owner_oid == owner_oid) | (Dataset.visibility == Visibility.PUBLIC.value))
            .order_by(Dataset.id)
        )
        return list(self.session.scalars(stmt))

    def set_visibility(self, dataset: Dataset, visibility: Visibility) -> None:
        dataset.visibility = visibility.value
        self.session.commit()

    def delete(self, dataset: Dataset) -> None:
        self.session.delete(dataset)
        self.session.commit()
