from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session


def make_engine(database_url: str) -> Engine:
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args, pool_pre_ping=True)


def new_session(engine: Engine) -> Session:
    """expire_on_commit=False: objects stay readable after the commit, so we can answer with them."""
    return Session(engine, expire_on_commit=False)
