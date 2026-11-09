from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.settings import Settings
from app.db.models import Base, Dataset, Job
from app.main import create_app
from app.repositories.storage import FakeStorage

from .conftest import migrate


def make_session() -> Session:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = Session(engine)
    a = Dataset(name="a.csv", owner_oid="x", file_key="k1", rows=3)
    b = Dataset(name="b.csv", owner_oid="y", file_key="k2", rows=5)
    session.add_all(
        [a, b, Job(dataset=a, owner_oid="o", status="done"), Job(dataset=a, owner_oid="o", status="failed")]
    )
    session.commit()
    return session


def test_filter_and_order():
    stmt = select(Dataset).where(Dataset.rows > 3).order_by(Dataset.name)
    assert [d.name for d in make_session().scalars(stmt)] == ["b.csv"]


def test_join_and_count_in_one_query():
    stmt = (
        select(Dataset.name, func.count(Job.id))
        .join(Job, isouter=True)
        .group_by(Dataset.id)
        .order_by(Dataset.name)
    )
    assert list(make_session().execute(stmt)) == [("a.csv", 2), ("b.csv", 0)]


def test_selectinload_loads_related_rows_in_one_extra_query():
    session = make_session()
    queries = []
    from sqlalchemy import event

    event.listen(session.get_bind(), "before_cursor_execute", lambda *a: queries.append(a[2]))
    datasets = session.scalars(select(Dataset).options(selectinload(Dataset.jobs))).all()
    assert sum(len(d.jobs) for d in datasets) == 2
    assert len(queries) == 2  # one for datasets, one for all their jobs


def test_lazy_loading_is_the_n_plus_one_trap():
    session = make_session()
    queries = []
    from sqlalchemy import event

    event.listen(session.get_bind(), "before_cursor_execute", lambda *a: queries.append(a[2]))
    for dataset in session.scalars(select(Dataset)).all():
        len(dataset.jobs)  # one extra query per dataset
    assert len(queries) == 3  # 1 + N (N = 2 datasets)


def make_client(tmp_path, flag: bool):
    url = f"sqlite:///{tmp_path}/f.db"
    migrate(url)
    settings = Settings(database_url=url, feature_csv_export=flag)
    return TestClient(create_app(settings, storage=FakeStorage()))


def test_feature_flag_off_endpoint_does_not_exist(tmp_path):
    assert make_client(tmp_path, False).get("/api/v1/datasets/export.csv").status_code == 404


def test_feature_flag_on_endpoint_works(tmp_path):
    client = make_client(tmp_path, True)
    client.post("/api/v1/datasets", files={"file": ("a.csv", b"time,x\n1,2\n", "text/csv")})
    response = client.get("/api/v1/datasets/export.csv")
    assert response.status_code == 200
    assert response.text.splitlines() == ["id,name,rows", "1,a.csv,1"]
