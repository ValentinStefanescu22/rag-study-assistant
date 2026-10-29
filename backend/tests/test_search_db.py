# Integration test: runs the real search SQL in Postgres, using a separate `rag_test`
# database so it never touches the documents you uploaded. Skipped if Postgres isn't running.

import math
import os

import psycopg
import pytest
from psycopg import sql

from app import db

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://rag:rag@localhost:5433/rag_test")


# 768 zeros with a single 1: a vector pointing straight along one axis.
def unit_vector(axis: int) -> list[float]:
    vector = [0.0] * 768
    vector[axis] = 1.0
    return vector


@pytest.fixture
def test_db(monkeypatch):
    server_url, name = TEST_DATABASE_URL.rsplit("/", 1)
    try:
        # CREATE DATABASE can't run inside a transaction, hence autocommit.
        with psycopg.connect(f"{server_url}/postgres", autocommit=True) as conn:
            if not conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,)).fetchone():
                conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    except psycopg.OperationalError:
        pytest.skip("Postgres isn't running (docker compose up -d db)")

    monkeypatch.setattr(db, "DATABASE_URL", TEST_DATABASE_URL)
    db.init_schema()
    with db.connect() as conn:
        conn.execute("TRUNCATE documents CASCADE")  # start every test from an empty database


def test_search_ranks_by_cosine_similarity(test_db):
    halfway = unit_vector(0)
    halfway[1] = 1.0  # [1, 1, 0, ...] points 45° away from axis 0
    db.save_document("test.pdf", 3, [
        (1, "same direction", unit_vector(0)),
        (2, "45 degrees away", halfway),
        (3, "perpendicular", unit_vector(1)),
    ])

    results = db.search_chunks(unit_vector(0), k=3)

    assert [r["content"] for r in results] == ["same direction", "45 degrees away", "perpendicular"]
    assert results[0]["similarity"] == pytest.approx(1.0, abs=1e-6)
    assert results[1]["similarity"] == pytest.approx(math.cos(math.radians(45)), abs=1e-6)  # ≈ 0.707
    assert results[2]["similarity"] == pytest.approx(0.0, abs=1e-6)
    assert (results[0]["filename"], results[0]["page_number"]) == ("test.pdf", 1)


def test_k_limits_the_number_of_results(test_db):
    db.save_document("test.pdf", 3, [(page, "text", unit_vector(page)) for page in (1, 2, 3)])

    assert len(db.search_chunks(unit_vector(1), k=2)) == 2
