import pytest
from pydantic import ValidationError

from app.core.settings import Settings


def test_defaults_are_safe_for_local_development():
    settings = Settings(_env_file=None)
    assert settings.auth_mode == "off"
    assert settings.feature_csv_export is False


def test_wrong_type_fails_at_startup(monkeypatch):
    monkeypatch.setenv("MAX_UPLOAD_MB", "ten")
    with pytest.raises(ValidationError, match="max_upload_mb"):
        Settings(_env_file=None)


def test_unknown_auth_mode_fails_at_startup(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "maybe")
    with pytest.raises(ValidationError, match="auth_mode"):
        Settings(_env_file=None)


def test_entra_without_ids_fails_at_startup(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "entra")
    with pytest.raises(ValidationError, match="TENANT_ID and API_CLIENT_ID"):
        Settings(_env_file=None)


def test_entra_with_ids_is_fine(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "entra")
    monkeypatch.setenv("TENANT_ID", "t")
    monkeypatch.setenv("API_CLIENT_ID", "a")
    assert Settings(_env_file=None).auth_mode == "entra"
