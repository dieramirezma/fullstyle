"""Verify a synthetic PostgreSQL backup by restoring into a disposable tmpfs DB."""

import hashlib
import json
import re
import subprocess
import time
from datetime import datetime, timezone
from uuid import uuid4

from check_local_stack import PROJECT
from prepare_copy import TARGET, write_json
from quality import fingerprint, source_hashes
from start_local import preflight


def main():
    preflight()
    before = source_hashes()
    original = PROJECT + "-postgres-1"
    suffix = uuid4().hex
    restore = "phase6-restore-" + suffix
    backup = TARGET / ".quality" / (restore + ".dump")
    label = "fullstyle.phase6.restore=" + suffix
    cleanup = False
    passed = False
    expected = actual = None

    def run(args, **kwargs):
        return subprocess.run(args, check=True, capture_output=True, timeout=90, **kwargs)

    def sql(container, statement):
        return run(
            [
                "docker",
                "exec",
                container,
                "psql",
                "-U",
                "synthetic",
                "-d",
                "fullstyle_synthetic",
                "-At",
                "-v",
                "ON_ERROR_STOP=1",
                "-c",
                statement,
            ],
            text=True,
        ).stdout.strip()

    def manifest(container):
        tables = sql(
            container,
            "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename",
        ).splitlines()
        result = {}
        for table in tables:
            if not re.fullmatch(r"[a-z_]+", table):
                raise ValueError("Unexpected synthetic table identifier")
            result[table] = sql(
                container,
                "SELECT count(*),md5(coalesce(string_agg(row_to_json(t)::text,'|' "
                'ORDER BY row_to_json(t)::text COLLATE "C"),\'\')) FROM public."' + table + '" t',
            )
        return result

    try:
        expected = manifest(original)
        result = run(
            [
                "docker",
                "exec",
                original,
                "pg_dump",
                "-U",
                "synthetic",
                "-d",
                "fullstyle_synthetic",
                "--format=custom",
                "--no-owner",
                "--no-acl",
            ]
        )
        backup.write_bytes(result.stdout)
        run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                restore,
                "--label",
                label,
                "--network",
                "none",
                "--read-only",
                "--tmpfs",
                "/tmp",
                "--tmpfs",
                "/var/run/postgresql",
                "--tmpfs",
                "/var/lib/postgresql/data",
                "-e",
                "POSTGRES_USER=synthetic",
                "-e",
                "POSTGRES_PASSWORD=local-synthetic-only",
                "-e",
                "POSTGRES_DB=fullstyle_synthetic",
                "postgres:16-alpine",
            ]
        )
        for _ in range(45):
            ready = subprocess.run(
                [
                    "docker",
                    "exec",
                    restore,
                    "pg_isready",
                    "-h",
                    "127.0.0.1",
                    "-U",
                    "synthetic",
                    "-d",
                    "fullstyle_synthetic",
                ],
                capture_output=True,
                timeout=5,
            )
            if ready.returncode == 0:
                break
            time.sleep(1)
        else:
            raise RuntimeError("Disposable restore DB did not start")
        run(
            [
                "docker",
                "exec",
                "-i",
                restore,
                "pg_restore",
                "-U",
                "synthetic",
                "-d",
                "fullstyle_synthetic",
                "--exit-on-error",
                "--no-owner",
                "--no-acl",
            ],
            input=backup.read_bytes(),
        )
        actual = manifest(restore)
        if expected != actual or expected != manifest(original):
            raise RuntimeError(
                "Restored data mismatch, or source changed during backup verification"
            )
        passed = True
    finally:
        inspect = subprocess.run(["docker", "inspect", restore], capture_output=True, text=True)
        if inspect.returncode == 0:
            container = json.loads(inspect.stdout)[0]
            if container["Config"]["Labels"].get("fullstyle.phase6.restore") != suffix:
                raise ValueError("Refusing cleanup of an unrelated restore container")
            run(["docker", "rm", "-f", "-v", restore])
        cleanup = not subprocess.check_output(
            ["docker", "ps", "-aq", "--filter", "label=" + label]
        ).strip()
        stable = before == source_hashes()
        write_json(
            "phase-3-backup.json",
            {
                "checked_utc": datetime.now(timezone.utc).isoformat(),
                "passed": passed and cleanup and stable,
                "source_fingerprint": fingerprint(before),
                "source_stable": stable,
                "cleanup_complete": cleanup,
                "tables": expected,
                "restored_tables": actual,
                "backup_sha256": hashlib.sha256(backup.read_bytes()).hexdigest()
                if backup.exists()
                else None,
                "backup_path": str(backup),
                "restore_environment": "network none, tmpfs, no host ports",
                "scope": "independent synthetic local DB only; not a production backup certification",
            },
        )
    if not passed or not cleanup or not stable:
        raise SystemExit(1)
    print(
        "PASS: synthetic backup restored in isolated tmpfs; table counts/content hashes identical"
    )


if __name__ == "__main__":
    main()
