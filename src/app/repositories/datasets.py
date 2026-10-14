from ..db.models import Dataset


class DatasetRepository:
    """For now the data lives in a list. Chapter 8 swaps this for a database, with the same methods."""

    def __init__(self) -> None:
        self.items: list[Dataset] = []

    def create(self, name: str, owner_oid: str, file_key: str, rows: int) -> Dataset:
        new_id = len(self.items) + 1
        dataset = Dataset(id=new_id, name=name, owner_oid=owner_oid, file_key=file_key, rows=rows)
        self.items.append(dataset)
        return dataset

    def get(self, dataset_id: int) -> Dataset | None:
        return next((d for d in self.items if d.id == dataset_id), None)

    def list_all(self) -> list[Dataset]:
        return list(self.items)
