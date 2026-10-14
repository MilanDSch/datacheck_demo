from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from app.core.settings import Settings
from app.main import create_app
from app.repositories.storage import FakeStorage

ROOT = Path(__file__).resolve().parent.parent

GOOD_CSV = b"time,temp\n0,20\n5,21\n8,22\n"
CSV_WITH_GAP = b"time,temp\n0,20\n50,21\n100,\n"
CSV_NO_TIME = b"when,temp\n0,20\n"


def migrate(database_url: str, revision: str = "head") -> None:
    """Build the schema the way production does: with Alembic, not with create_all."""
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, revision)


@pytest.fixture
def storage():
    return FakeStorage()


@pytest.fixture
def client(tmp_path, storage):
    url = f"sqlite:///{tmp_path}/test.db"
    migrate(url)
    settings = Settings(database_url=url, max_upload_mb=1)
    app = create_app(settings, storage=storage)
    with TestClient(app) as test_client:
        yield test_client
