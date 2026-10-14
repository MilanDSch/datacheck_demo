from sqlalchemy import create_engine, text

from .injection_demo import find_datasets_safe, find_datasets_unsafe


def make_conn():
    engine = create_engine("sqlite://")
    conn = engine.connect()
    conn.execute(text("CREATE TABLE datasets (id INTEGER PRIMARY KEY, name TEXT)"))
    conn.execute(text("INSERT INTO datasets (name) VALUES ('mine'), ('secret-of-someone-else')"))
    return conn


ATTACK = "' OR '1'='1"


def test_unsafe_query_returns_every_row():
    assert len(find_datasets_unsafe(make_conn(), ATTACK)) == 2


def test_safe_query_treats_the_attack_as_plain_text():
    assert find_datasets_safe(make_conn(), ATTACK) == []


def test_safe_query_still_works_for_normal_input():
    assert len(find_datasets_safe(make_conn(), "mine")) == 1
