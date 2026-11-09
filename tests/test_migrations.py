"""The migrations and the models must always say the same thing."""

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text

from app.db.models import Base

from .conftest import ROOT, migrate


def config_for(url: str) -> Config:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", url)
    return config


def test_upgrade_creates_every_model_table(tmp_path):
    url = f"sqlite:///{tmp_path}/m.db"
    migrate(url)
    tables = set(inspect(create_engine(url)).get_table_names())
    assert {"datasets", "jobs"} <= tables


def test_migrations_match_the_models(tmp_path):
    """If you change a model and forget the migration, this test fails."""
    url = f"sqlite:///{tmp_path}/m.db"
    migrate(url)
    with create_engine(url).connect() as connection:
        diff = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    assert diff == []


def test_downgrade_removes_the_tables_and_upgrade_brings_them_back(tmp_path):
    url = f"sqlite:///{tmp_path}/m.db"
    migrate(url)
    command.downgrade(config_for(url), "base")
    assert {"datasets", "jobs"}.isdisjoint(inspect(create_engine(url)).get_table_names())
    migrate(url)
    assert {"datasets", "jobs"} <= set(inspect(create_engine(url)).get_table_names())


def test_existing_jobs_get_the_owner_of_their_dataset(tmp_path):
    url = f"sqlite:///{tmp_path}/m.db"
    migrate(url, "0001")
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO datasets (id, name, owner_oid, file_key, rows, created_at) "
                "VALUES (1, 'a.csv', 'oid-lotte', 'k', 3, '2026-01-01')"
            )
        )
        connection.execute(
            text("INSERT INTO jobs (id, dataset_id, status, created_at) VALUES (1, 1, 'done', '2026-01-01')")
        )
    migrate(url)
    with engine.connect() as connection:
        assert connection.execute(text("SELECT owner_oid FROM jobs WHERE id = 1")).scalar_one() == "oid-lotte"


def test_existing_datasets_become_private(tmp_path):
    url = f"sqlite:///{tmp_path}/m.db"
    migrate(url, "0002")
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO datasets (id, name, owner_oid, file_key, rows, created_at) "
                "VALUES (1, 'a.csv', 'oid-lotte', 'k', 3, '2026-01-01')"
            )
        )
    migrate(url)
    with engine.connect() as connection:
        assert (
            connection.execute(text("SELECT visibility FROM datasets WHERE id = 1")).scalar_one() == "private"
        )
