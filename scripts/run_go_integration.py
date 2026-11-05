"""Run the repaired Go harness against private temporary PostgreSQL schemas."""

import subprocess
import sys
from datetime import datetime, timezone

from check_local_stack import PROJECT
from prepare_copy import TARGET, evidence_name, evidence_path, write_json
from start_local import preflight


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    preflight()
    subprocess.run(
        [
            "docker",
            "build",
            "--target",
            "checks",
            "-t",
            PROJECT + "-auth-tests:phase3",
            "-f",
            "docker/Auth.Dockerfile",
            ".",
        ],
        cwd=TARGET,
        check=True,
    )
    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--network",
            PROJECT + "_sandbox",
            "--read-only",
            "--tmpfs",
            "/tmp",
            "-e",
            "DATABASE_URL_TEST=postgresql://synthetic:local-synthetic-only@postgres/fullstyle_synthetic",
            PROJECT + "-auth-tests:phase3",
        ],
        cwd=TARGET,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    output = result.stdout + result.stderr
    evidence_path("phase-3-go-tests.log").write_text(output, encoding="utf-8")
    write_json(
        "phase-3-go-tests.json",
        {
            "checked_utc": datetime.now(timezone.utc).isoformat(),
            "passed": result.returncode == 0,
            "exit_code": result.returncode,
            "report": evidence_name("phase-3-go-tests.log"),
            "database": "Private go_test_<uuid> schemas, removed by test cleanup",
        },
    )
    print(output)
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
