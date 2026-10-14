from fastapi import HTTPException

from .settings import SettingsDep


def require_flag(name: str):
    """A feature flag as a dependency: while the flag is off, the endpoint does not exist (404)."""

    def check(settings: SettingsDep) -> None:
        if not getattr(settings, f"feature_{name}", False):
            raise HTTPException(status_code=404, detail="not found")

    return check
