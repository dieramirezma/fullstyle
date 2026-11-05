"""Consistency regressions and controlled mutations in a disposable SQL schema/Redis."""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from uuid import uuid4

from check_local_stack import PROJECT, resolve_local, validate
from prepare_copy import DOCS, TARGET, evidence_name, write_json
from quality import fingerprint, source_hashes
from start_local import preflight


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--mutation", choices=["worker-lock", "cache-status"])
    mutation = parser.parse_args().mutation
    preflight()
    config = resolve_local()
    validate(config)
    network = json.loads(
        subprocess.check_output(["docker", "network", "inspect", PROJECT + "_sandbox"])
    )[0]
    if not network["Internal"] or network["Labels"].get("com.docker.compose.project") != PROJECT:
        raise ValueError("Independent internal network required")
    suffix = uuid4().hex
    redis_name = "phase4-redis-" + suffix
    runner_name = "phase4-consistency-" + suffix
    before = source_hashes()
    prefix = evidence_name("phase-3-") + ("mutation-" + mutation if mutation else "consistency")
    cleanup = False
    result = None
    try:
        subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                redis_name,
                "--network",
                PROJECT + "_sandbox",
                "--read-only",
                "--tmpfs",
                "/data",
                "--label",
                "fullstyle.phase4=" + suffix,
                "redis:7-alpine",
                "redis-server",
                "--save",
                "",
                "--appendonly",
                "no",
            ],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["docker", "exec", redis_name, "redis-cli", "PING"], check=True, capture_output=True
        )
        args = [
            "docker",
            "run",
            "--rm",
            "--name",
            runner_name,
            "--network",
            PROJECT + "_sandbox",
            "--read-only",
            "--tmpfs",
            "/tmp",
            "--label",
            "fullstyle.phase4=" + suffix,
            "--mount",
            f"type=bind,source={TARGET / 'tests/phase4'},target=/tests,readonly",
            "--mount",
            f"type=bind,source={TARGET / 'FullStyle-Backend'},target=/app,readonly",
            "-e",
            "PYTHONPATH=/app:/tests",
            "-e",
            "PHASE4_REDIS=" + redis_name,
        ]
        for key, value in config["services"]["backend"]["environment"].items():
            args += ["-e", f"{key}={value}"]
        if mutation:
            args += ["-e", "PHASE4_MUTATION=" + mutation]
        args += ["fullstyle-portfolio-backend:phase3", "python", "-m", "unittest"]
        if mutation:
            method = {
                "worker-lock": "test_01_concurrent_creates_one_winner_independent_connections",
                "cache-status": "test_05_cache_hit_miss_exact_body_status_scope_and_invalidation",
            }[mutation]
            args += ["-v", "test_consistency.ConsistencyTests." + method]
        else:
            args += ["discover", "-s", "/tests", "-v"]
        result = subprocess.run(
            args,
            cwd=TARGET,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600,
        )
    finally:
        # Exact random names generated here, never compose down or shared Redis shutdown.
        subprocess.run(["docker", "rm", "-f", runner_name, redis_name], capture_output=True)
        cleanup = not subprocess.check_output(
            ["docker", "ps", "-aq", "--filter", "label=fullstyle.phase4=" + suffix]
        ).strip()
    output = result.stdout + result.stderr
    (DOCS / (prefix + ".log")).write_text(output, encoding="utf-8")
    passed = result.returncode == 0
    detected = bool(
        mutation
        and result.returncode == 1
        and "FAILED (failures=1)" in output
        and "ERROR:" not in output
    )
    stable = before == source_hashes()
    write_json(
        prefix + ".json",
        {
            "checked_utc": datetime.now(timezone.utc).isoformat(),
            "passed": (detected if mutation else passed) and cleanup and stable,
            "exit_code": result.returncode,
            "controlled_mutation": mutation,
            "regression_detected": detected,
            "source_fingerprint": fingerprint(before),
            "source_stable": stable,
            "cleanup_complete": cleanup,
            "database": "unique phase4 schema, dropped after run",
            "redis": "disposable instance; shutdown tested without affecting shared cache",
            "providers_contacted": False,
            "report": prefix + ".log",
        },
    )
    print(output)
    raise SystemExit(0 if (detected if mutation else passed) and cleanup and stable else 1)


if __name__ == "__main__":
    main()
