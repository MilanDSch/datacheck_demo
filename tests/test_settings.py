import pytest
from pydantic import ValidationError

from app.core.settings import Settings


def test_defaults_are_safe_for_local_development():
    settings = Settings(_env_file=None)
    assert settings.max_upload_mb == 100
    assert settings.feature_csv_export is False


def test_wrong_type_fails_at_startup(monkeypatch):
    monkeypatch.setenv("MAX_UPLOAD_MB", "ten")
    with pytest.raises(ValidationError, match="max_upload_mb"):
        Settings(_env_file=None)
