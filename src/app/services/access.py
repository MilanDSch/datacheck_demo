"""The ownership rule, in one place: owners and Admins may touch a resource, nobody else."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.auth import User


def owns_or_admin(user: "User", owner_oid: str) -> bool:
    return "Admin" in user.roles or user.oid == owner_oid
