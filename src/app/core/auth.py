"""Authentication (who are you?) and authorization (what may you do?)."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .settings import SettingsDep

bearer = HTTPBearer(auto_error=False)  # we raise our own 401, so the answer is ours


@dataclass(frozen=True)
class User:
    oid: str
    name: str
    roles: tuple[str, ...]


class TokenValidator:
    """Checks signature, audience, issuer and expiry of an Entra ID access token."""

    def __init__(self, audience: str, issuer: str, key_resolver: Callable[[str], Any]) -> None:
        self.audience = audience
        self.issuer = issuer
        self.key_resolver = key_resolver  # token -> public key; Entra: the tenant's JWKS

    def validate(self, token: str) -> User:
        try:
            key = self.key_resolver(token)
            claims = jwt.decode(
                token,
                key,
                algorithms=["RS256"],  # never read the algorithm from the token itself
                audience=self.audience,
                issuer=self.issuer,
                options={"require": ["exp", "aud", "iss"]},
            )
        except jwt.PyJWTError as exc:
            raise HTTPException(status_code=401, detail="invalid token") from exc
        return User(
            oid=claims["oid"],
            name=claims.get("name", ""),
            roles=tuple(claims.get("roles", [])),
        )


def entra_validator(tenant_id: str, api_client_id: str) -> TokenValidator:
    jwks = jwt.PyJWKClient(f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys")
    return TokenValidator(
        audience=api_client_id,
        issuer=f"https://login.microsoftonline.com/{tenant_id}/v2.0",
        key_resolver=lambda token: jwks.get_signing_key_from_jwt(token).key,
    )


LOCAL_DEV_USER = User(oid="local-lotte", name="Lotte Researcher", roles=("Researcher",))


def get_current_user(
    request: Request,
    settings: SettingsDep,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> User:
    if settings.auth_mode == "off":
        return LOCAL_DEV_USER  # local development only: everyone is Lotte
    if credentials is None:
        raise HTTPException(status_code=401, detail="missing token")
    return request.app.state.validator.validate(credentials.credentials)


def require_role(*allowed: str) -> Callable[[User], User]:
    def check(user: User = Depends(get_current_user)) -> User:
        if not set(user.roles) & set(allowed):
            raise HTTPException(status_code=403, detail="you may not do this")
        return user

    return check
