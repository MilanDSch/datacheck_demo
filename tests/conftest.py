import pytest
from fastapi.testclient import TestClient

from app.core.settings import Settings
from app.main import create_app
from app.repositories.storage import FakeStorage

GOOD_CSV = b"time,temp\n0,20\n5,21\n8,22\n"
CSV_NO_TIME = b"when,temp\n0,20\n"


@pytest.fixture
def storage():
    return FakeStorage()


@pytest.fixture
def client(storage):
    settings = Settings(max_upload_mb=1)
    app = create_app(settings, storage=storage)
    with TestClient(app) as test_client:
        yield test_client
