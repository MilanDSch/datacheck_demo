from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import Dataset


class DatasetRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, name: str, owner_oid: str, file_key: str, rows: int) -> Dataset:
        dataset = Dataset(name=name, owner_oid=owner_oid, file_key=file_key, rows=rows)
        self.session.add(dataset)
        self.session.commit()
        return dataset

    def get(self, dataset_id: int) -> Dataset | None:
        return self.session.get(Dataset, dataset_id)

    def list_all(self) -> list[Dataset]:
        return list(self.session.scalars(select(Dataset).order_by(Dataset.id)))

    def delete(self, dataset: Dataset) -> None:
        self.session.delete(dataset)
        self.session.commit()
