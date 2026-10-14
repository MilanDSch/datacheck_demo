"""Demo material: SQL injection, on purpose. Never copy the unsafe function.

It lives in tests/ so the unsafe code never ships in the image.
"""

from sqlalchemy import text
from sqlalchemy.engine import Connection


def find_datasets_unsafe(conn: Connection, name: str) -> list[tuple]:
    # NEVER: the input becomes part of the SQL text
    return list(conn.execute(text(f"SELECT id, name FROM datasets WHERE name = '{name}'")))


def find_datasets_safe(conn: Connection, name: str) -> list[tuple]:
    # ALWAYS: the input travels separately, as a parameter
    return list(conn.execute(text("SELECT id, name FROM datasets WHERE name = :name"), {"name": name}))
