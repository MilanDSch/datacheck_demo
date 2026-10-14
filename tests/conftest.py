import time
from pathlib import Path

import jwt
import pytest
from alembic import command
from alembic.config import Config
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.core.auth import TokenValidator
from app.core.settings import Settings
from app.main import create_app
from app.repositories.storage import FakeStorage

ROOT = Path(__file__).resolve().parent.parent
TENANT = "tenant-1"
API_ID = "api-client-id"
ISSUER = f"https://login.microsoftonline.com/{TENANT}/v2.0"

GOOD_CSV = b"time,temp\n0,20\n5,21\n8,22\n"
CSV_WITH_GAP = b"time,temp\n0,20\n50,21\n100,\n"
CSV_NO_TIME = b"when,temp\n0,20\n"


def migrate(database_url: str, revision: str = "head") -> None:
    """Build the schema the way production does: with Alembic, not with create_all."""
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, revision)


@pytest.fixture(scope="session")
def private_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def make_token(private_key, *, roles=("Researcher",), oid="oid-lotte", aud=API_ID, iss=ISSUER, exp_in=3600):
    claims = {
        "oid": oid,
        "name": "Test User",
        "roles": list(roles),
        "aud": aud,
        "iss": iss,
        "exp": int(time.time()) + exp_in,
    }
    return jwt.encode(claims, private_key, algorithm="RS256")


@pytest.fixture
def storage():
    return FakeStorage()


@pytest.fixture
def client(tmp_path, private_key, storage):
    url = f"sqlite:///{tmp_path}/test.db"
    migrate(url)
    settings = Settings(
        database_url=url,
        auth_mode="entra",
        tenant_id=TENANT,
        api_client_id=API_ID,
        max_upload_mb=1,
    )
    validator = TokenValidator(API_ID, ISSUER, key_resolver=lambda token: private_key.public_key())
    app = create_app(settings, storage=storage, validator=validator)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def lotte(private_key):
    return {"Authorization": f"Bearer {make_token(private_key)}"}


@pytest.fixture
def pieter(private_key):
    return {"Authorization": f"Bearer {make_token(private_key, roles=('Viewer',), oid='oid-pieter')}"}
