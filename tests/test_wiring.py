"""The payoff of injection: swap one provider in a test, no database and no storage needed."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.core.settings import Settings
from app.db.models import Dataset
from app.main import create_app
from app.routers.deps import get_dataset_repo


class FakeRepo:
    def list_all(self):
        return [Dataset(id=1, name="bench-run", rows=10, created_at=datetime.now(UTC))]


def test_list_datasets_with_a_fake_repository():
    # no migration was run and no table exists: the real repository is never built
    app = create_app(Settings(database_url="sqlite://", auth_mode="off"))
    app.dependency_overrides[get_dataset_repo] = FakeRepo
    client = TestClient(app)

    response = client.get("/api/v1/datasets")

    assert response.status_code == 200
    assert response.json()[0]["name"] == "bench-run"


def test_the_session_is_closed_after_the_request(tmp_path):
    from .conftest import migrate

    url = f"sqlite:///{tmp_path}/s.db"
    migrate(url)
    app = create_app(Settings(database_url=url, auth_mode="off"))
    pool = app.state.engine.pool
    with TestClient(app) as client:
        assert client.get("/api/v1/datasets").status_code == 200
    assert pool.checkedout() == 0  # nothing left open: the yield dependency cleaned up


def test_job_routes_translate_service_errors_without_a_database():
    from app.routers.deps import get_job_service
    from app.services.errors import JobNotFound, ReportNotReady

    class FakeJobService:
        def get(self, job_id, user):
            raise JobNotFound

        def get_report(self, job_id, user):
            raise ReportNotReady("running")

    app = create_app(Settings(database_url="sqlite://"))
    app.dependency_overrides[get_job_service] = FakeJobService
    client = TestClient(app)

    assert client.get("/api/v1/jobs/1").status_code == 404
    response = client.get("/api/v1/jobs/1/report")
    assert response.status_code == 409
    assert response.json()["detail"] == "report not ready, job is running"
