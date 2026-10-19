"""Demo E: count the queries. Run with: uv run python demo/n_plus_one.py

An in-memory database, three datasets with jobs. First the lazy loop (1 + N queries),
then the same loop with selectinload (2 queries). The SQL is printed so the room can count it.
"""

from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Base, Dataset, Job

engine = create_engine("sqlite://")
Base.metadata.create_all(engine)  # fine for a throwaway demo database, production uses Alembic

with Session(engine) as session:
    for n in range(3):
        dataset = Dataset(name=f"run-{n}.csv", owner_oid="lotte", file_key=f"key-{n}", rows=10)
        session.add_all(
            [
                dataset,
                Job(dataset=dataset, owner_oid="demo", status="done"),
                Job(dataset=dataset, owner_oid="demo", status="queued"),
            ]
        )
    session.commit()

queries: list[str] = []
event.listen(engine, "before_cursor_execute", lambda conn, cur, statement, *rest: queries.append(statement))


def show(title: str) -> None:
    print(f"\n=== {title}: {len(queries)} queries")
    for statement in queries:
        print("   ", " ".join(statement.split())[:100])
    queries.clear()


with Session(engine) as session:
    for dataset in session.scalars(select(Dataset)):
        print(dataset.name, len(dataset.jobs))  # touching .jobs fires one query per dataset
    show("lazy loading, the default")

with Session(engine) as session:
    stmt = select(Dataset).options(selectinload(Dataset.jobs))
    for dataset in session.scalars(stmt):
        print(dataset.name, len(dataset.jobs))
    show("eager loading with selectinload")
