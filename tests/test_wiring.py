"""The payoff of injection: swap one provider in a test."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.core.settings import Settings
from app.db.models import Dataset
from app.main import create_app
from app.routers.deps import get_dataset_repo


class FakeRepo:
    def list_all(self):
        now = datetime.now(UTC)
        return [Dataset(id=1, name="bench-run", owner_oid="x", file_key="x.csv", rows=10, created_at=now)]


def test_list_datasets_with_a_fake_repository():
    app = create_app(Settings())
    app.dependency_overrides[get_dataset_repo] = FakeRepo
    client = TestClient(app)

    response = client.get("/api/v1/datasets")

    assert response.status_code == 200
    assert response.json()[0]["name"] == "bench-run"
