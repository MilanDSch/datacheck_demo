"""Who may do what with a dataset or a job.

Reading is wider than changing: a public dataset may be read by every signed-in user, but only its owner
and an Admin may change or delete it. Every ownership rule lives here, so there is one place to read and test.
"""

from typing import TYPE_CHECKING

from ..db.models import Visibility

if TYPE_CHECKING:
    from ..core.auth import User


def is_admin(user: "User") -> bool:
    return "Admin" in user.roles


def owns_or_admin(user: "User", owner_oid: str) -> bool:
    """The rule for changing things: owners and Admins only."""
    return is_admin(user) or user.oid == owner_oid


def can_read(user: "User", owner_oid: str, visibility: str) -> bool:
    """The rule for looking at things: public, or owners and Admins."""
    return visibility == Visibility.PUBLIC or owns_or_admin(user, owner_oid)
