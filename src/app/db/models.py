from dataclasses import dataclass, field
from datetime import UTC, datetime


def utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass
class Dataset:
    """What we keep about one upload. In chapter 8 this becomes a database table."""

    id: int
    name: str
    owner_oid: str
    file_key: str  # pointer to the file in storage
    rows: int
    created_at: datetime = field(default_factory=utcnow)
