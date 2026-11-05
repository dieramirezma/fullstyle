"""Explicit, checksummed migrations. Only the independent synthetic database."""

import hashlib
import json
import os
import re
from pathlib import Path

from sqlalchemy import inspect, text

from config.db_config import db
from config.server_config import create_app

EXPECTED = "postgresql://synthetic:local-synthetic-only@postgres/fullstyle_synthetic"
MIGRATIONS = Path(__file__).parent / "migrations"


def validate_baseline(connection):
    """Adopt only a structurally compatible phase-5 schema; never blindly stamp."""
    expected = json.loads((MIGRATIONS / "0001_phase5.json").read_text())
    inspector = inspect(connection)
    present = set(inspector.get_table_names()) - {"schema_migration"}
    if not present:
        return False
    if present != set(expected):
        raise RuntimeError("Existing schema is not the complete phase-5 baseline")
    for table, spec in expected.items():
        actual = {
            c["name"]: {
                "type": str(c["type"].compile(dialect=connection.dialect)),
                "nullable": c["nullable"],
            }
            for c in inspector.get_columns(table)
        }
        if actual != spec["columns"] or (
            inspector.get_pk_constraint(table)["constrained_columns"] != spec["primary_key"]
        ):
            raise RuntimeError("Baseline schema mismatch: " + table)
        foreign_keys = [
            {
                key: item[key]
                for key in ("constrained_columns", "referred_table", "referred_columns", "options")
            }
            for item in inspector.get_foreign_keys(table)
        ]
        uniques = [item["column_names"] for item in inspector.get_unique_constraints(table)]
        checks = [item["sqltext"] for item in inspector.get_check_constraints(table)]

        def canonical(items):
            return sorted(json.dumps(item, sort_keys=True) for item in items)

        if (
            canonical(foreign_keys) != canonical(spec["foreign_keys"])
            or canonical(uniques) != canonical(spec["unique_constraints"])
            or sorted(checks) != sorted(spec["checks"])
        ):
            raise RuntimeError("Baseline constraint mismatch: " + table)
    return True


def upgrade(engine, schema="public"):
    if os.getenv("LOCAL_RUNTIME") != "true" or os.getenv("DATABASE_URL") != EXPECTED:
        raise RuntimeError("Migrations require the exact isolated synthetic database")
    if schema != "public" and not re.fullmatch(
        r"(?:phase6_[a-f0-9]{32}|phase5_[a-f0-9]{12})", schema
    ):
        raise ValueError("Unexpected migration schema")
    with engine.begin() as connection:
        connection.execute(text("SELECT pg_advisory_xact_lock(64196006)"))
        connection.execute(text('SET LOCAL search_path TO "' + schema + '"'))
        connection.execute(text("SET LOCAL lock_timeout = '5s'"))
        connection.execute(
            text(
                "CREATE TABLE IF NOT EXISTS schema_migration "
                "(version TEXT PRIMARY KEY, sha256 TEXT NOT NULL, applied_at TIMESTAMPTZ "
                "NOT NULL DEFAULT now())"
            )
        )
        applied = dict(
            connection.execute(text("SELECT version, sha256 FROM schema_migration")).all()
        )
        paths = sorted(MIGRATIONS.glob("[0-9]*.sql"))
        if set(applied) - {p.stem for p in paths}:
            raise RuntimeError("Unknown applied migration; upgrade the runner")
        for path in paths:
            specification = path.with_suffix(".json")
            checksum = hashlib.sha256(
                path.read_bytes() + (specification.read_bytes() if specification.exists() else b"")
            ).hexdigest()
            if path.stem in applied:
                if applied[path.stem] != checksum:
                    raise RuntimeError("Applied migration checksum changed: " + path.stem)
                continue
            adopt = path.stem == "0001_phase5" and validate_baseline(connection)
            if not adopt:
                connection.exec_driver_sql(path.read_text(encoding="utf-8"))
            connection.execute(
                text("INSERT INTO schema_migration(version,sha256) VALUES (:v,:h)"),
                {"v": path.stem, "h": checksum},
            )
            print("Adopted" if adopt else "Applied", path.stem)
    return [p.stem for p in paths]


if __name__ == "__main__":
    with create_app().app_context():
        upgrade(db.engine)
