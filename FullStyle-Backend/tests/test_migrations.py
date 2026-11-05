"""Fresh/adopted schema, checksum tamper, transaction rollback and no startup DDL."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from uuid import uuid4

import pytest
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DataError

import migrate_local
from config.db_config import db
from config.server_config import create_app


@pytest.fixture
def empty_schema(app):
    schema = "phase6_" + uuid4().hex
    with app.app_context():
        with db.engine.begin() as connection:
            connection.execute(text("CREATE SCHEMA " + schema))
        yield db.engine, schema
        with db.engine.begin() as connection:
            connection.execute(text("DROP SCHEMA " + schema + " CASCADE"))


def test_migrations_idempotent_serialized_preserve_data(app, empty_schema):
    engine, schema = empty_schema
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: migrate_local.upgrade(engine, schema), range(2)))
    assert results[0] == results[1]
    with engine.begin() as connection:
        connection.execute(text('SET LOCAL search_path TO "' + schema + '"'))
        connection.execute(text("INSERT INTO category(name) VALUES ('keep')"))
    migrate_local.upgrade(engine, schema)
    with engine.connect() as connection:
        assert (
            connection.execute(text('SELECT name FROM "' + schema + '".category')).scalar_one()
            == "keep"
        )
        assert connection.execute(
            text('SELECT count(*) FROM "' + schema + '".schema_migration')
        ).scalar_one() == len(results[0])


def test_adopts_complete_phase5_without_overwriting_rows(empty_schema):
    engine, schema = empty_schema
    with engine.begin() as connection:
        connection.execute(text('SET LOCAL search_path TO "' + schema + '"'))
        connection.exec_driver_sql((migrate_local.MIGRATIONS / "0001_phase5.sql").read_text())
        connection.execute(text("INSERT INTO category(name) VALUES ('legacy')"))
    migrate_local.upgrade(engine, schema)
    with engine.connect() as connection:
        assert (
            connection.execute(text('SELECT name FROM "' + schema + '".category')).scalar_one()
            == "legacy"
        )


def test_partial_schema_rejected_without_stamping(empty_schema):
    engine, schema = empty_schema
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE "' + schema + '".category(id INTEGER)'))
    with pytest.raises(RuntimeError, match="complete phase-5"):
        migrate_local.upgrade(engine, schema)
    with engine.connect() as connection:
        assert (
            connection.execute(
                text("SELECT to_regclass(:name)"), {"name": schema + ".schema_migration"}
            ).scalar_one()
            is None
        )


def test_adoption_rejects_missing_business_constraint(empty_schema):
    engine, schema = empty_schema
    with engine.begin() as connection:
        connection.execute(text('SET LOCAL search_path TO "' + schema + '"'))
        connection.exec_driver_sql((migrate_local.MIGRATIONS / "0001_phase5.sql").read_text())
        connection.execute(text("ALTER TABLE booking_terms DROP CONSTRAINT valid_booking_terms"))
    with pytest.raises(RuntimeError, match="constraint mismatch"):
        migrate_local.upgrade(engine, schema)


def test_migration_refuses_non_synthetic_database_before_any_sql(app, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://unapproved.invalid/forbidden")
    with app.app_context(), pytest.raises(RuntimeError, match="exact isolated"):
        migrate_local.upgrade(db.engine, app.config["TEST_SCHEMA"])


def test_checksum_mismatch_and_failed_ddl_roll_back(app):
    with app.app_context(), TemporaryDirectory() as temp:
        root = Path(temp)
        for path in migrate_local.MIGRATIONS.iterdir():
            (root / path.name).write_bytes(path.read_bytes())
        schema = app.config["TEST_SCHEMA"]
        baseline = root / "0001_phase5.sql"
        baseline.write_text(baseline.read_text() + "\n-- tampered\n")
        with (
            patch.object(migrate_local, "MIGRATIONS", root),
            pytest.raises(RuntimeError, match="checksum"),
        ):
            migrate_local.upgrade(db.engine, schema)
        baseline.write_bytes((migrate_local.MIGRATIONS / baseline.name).read_bytes())
        (root / "9999_failure.sql").write_text(
            "CREATE TABLE partial_write(id INTEGER); SELECT 1/0;"
        )
        with patch.object(migrate_local, "MIGRATIONS", root), pytest.raises(DataError):
            migrate_local.upgrade(db.engine, schema)
        assert db.session.execute(text("SELECT to_regclass('partial_write')")).scalar_one() is None
        assert (
            db.session.execute(
                text("SELECT count(*) FROM schema_migration WHERE version='9999_failure'")
            ).scalar_one()
            == 0
        )


def test_startup_never_creates_schema_even_with_legacy_flag(monkeypatch):
    monkeypatch.setenv("AUTO_CREATE_SCHEMA", "true")
    schema = "phase6_" + uuid4().hex
    # No schema exists, so accidental create_all would fail. Factory makes no SQL calls.
    statements = []

    def record(*args):
        statements.append(args[2])

    event.listen(Engine, "before_cursor_execute", record)
    try:
        with patch.object(db, "create_all", side_effect=AssertionError("startup DDL")):
            application = create_app(
                {
                    "SQLALCHEMY_ENGINE_OPTIONS": {
                        "connect_args": {"options": "-csearch_path=" + schema}
                    }
                }
            )
        with application.app_context():
            db.engine.dispose()
    finally:
        event.remove(Engine, "before_cursor_execute", record)
    assert statements == []
