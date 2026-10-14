from pathlib import Path
from typing import Protocol


class Storage(Protocol):
    def save(self, key: str, data: bytes) -> None: ...
    def load(self, key: str) -> bytes: ...


class LocalStorage:
    def __init__(self, root: str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, key: str, data: bytes) -> None:
        (self.root / key).write_bytes(data)

    def load(self, key: str) -> bytes:
        return (self.root / key).read_bytes()


class FakeStorage:
    """For tests: a dict that keeps the promise of Storage."""

    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}

    def save(self, key: str, data: bytes) -> None:
        self.files[key] = data

    def load(self, key: str) -> bytes:
        return self.files[key]
