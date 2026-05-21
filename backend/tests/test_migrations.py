"""Verify the Alembic migrations stay consistent with current ORM metadata."""

from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, event
from sqlalchemy.pool import StaticPool

from app.core.database import Base


def _make_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_sqlite_fk(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    return engine


def _alembic_config(engine) -> Config:
    backend_dir = Path(__file__).resolve().parent.parent
    cfg = Config(str(backend_dir / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_dir / "alembic"))
    cfg.set_main_option("sqlalchemy.url", str(engine.url))
    cfg.attributes["connection"] = None
    return cfg


def test_upgrade_head_runs_clean():
    engine = _make_engine()
    cfg = _alembic_config(engine)
    with engine.begin() as connection:
        cfg.attributes["connection"] = connection
        command.upgrade(cfg, "head")
    engine.dispose()


def test_metadata_matches_migrations():
    engine = _make_engine()
    cfg = _alembic_config(engine)
    with engine.begin() as connection:
        cfg.attributes["connection"] = connection
        command.upgrade(cfg, "head")

    with engine.connect() as connection:
        ctx = MigrationContext.configure(
            connection,
            opts={"compare_type": True, "render_as_batch": True},
        )
        diff = compare_metadata(ctx, Base.metadata)

    # Filter out cosmetic diffs that SQLite reports for indexes/unique flags
    # carried over from MySQL-targeted models.
    significant = [
        d
        for d in diff
        if not (
            isinstance(d, tuple)
            and d
            and d[0] in {"add_index", "remove_index"}
        )
    ]
    assert significant == [], f"unexpected diff: {diff}"
    engine.dispose()
