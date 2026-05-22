"""Tests for app.core.database module — coverage gap fill."""

from sqlalchemy import create_engine, event, text
from sqlalchemy.pool import StaticPool

from app.core.database import Base, engine, get_db


def test_sqlite_foreign_keys_enabled():
    """Cover the _enable_sqlite_fk listener path that sets PRAGMA foreign_keys=ON.

    Connects to the module-level *engine* to trigger the listener registered at
    import time (line 15 of database.py).
    """
    with engine.connect() as conn:
        fk_status = conn.execute(text("PRAGMA foreign_keys")).scalar()
        assert fk_status == 1, "foreign_keys should be enabled (=1)"


def test_get_db_yields_and_closes():
    """Cover get_db(): yields a session, closes on generator teardown."""
    gen = get_db()
    session = next(gen)
    assert hasattr(session, "close"), "session must have close method"
    session.close()
    gen.close()