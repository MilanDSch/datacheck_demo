"""The migrations and the models must always say the same thing."""

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, inspect

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
