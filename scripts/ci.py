"""Single blocking pipeline for the independent, pre-provisioned local workspace."""

import os
import subprocess
import sys
from datetime import datetime, timezone

from check_local_stack import COMPOSE
from prepare_copy import TARGET, write_json
from quality import fingerprint, source_hashes


def main():
    phase = os.environ.get("FULLSTYLE_VALIDATION_PHASE", "7")
    phase4 = phase in {"4", "5", "6", "7"}
    steps = [
        [sys.executable, "scripts/check_local_stack.py"],
        [sys.executable, "scripts/quality.py"],
        [sys.executable, "scripts/prove_contract_regression.py"],
        [*COMPOSE, "build"],
        [
            "docker",
            "build",
            "-t",
            "fullstyle-portfolio-security:phase2",
            "-f",
            "tests/security/Dockerfile",
            ".",
        ],
        [sys.executable, "scripts/start_local.py"],
        [sys.executable, "-m", "unittest", "discover", "-s", "scripts", "-p", "test_*.py"],
        [
            sys.executable,
            "scripts/run_security_tests.py",
            "--report-prefix",
            f"phase-{phase}-security",
        ],
        [sys.executable, "scripts/run_phase3.py"],
        [sys.executable, "scripts/run_go_integration.py"],
        [sys.executable, "scripts/reproduce_clean.py"],
        [sys.executable, "scripts/release_gate.py"],
    ]
    if phase4:
        offset = steps.index([sys.executable, "scripts/run_go_integration.py"])
        steps[offset:offset] = [
            [sys.executable, "scripts/run_phase4.py"],
            [sys.executable, "scripts/run_phase4.py", "--mutation", "worker-lock"],
            [sys.executable, "scripts/run_phase4.py", "--mutation", "cache-status"],
        ]
    if phase in {"5", "6", "7"}:
        steps.insert(
            steps.index([sys.executable, "scripts/release_gate.py"]),
            [sys.executable, "scripts/observe_local.py"],
        )
        offset = steps.index([sys.executable, "scripts/run_go_integration.py"])
        steps[offset:offset] = [
            [sys.executable, "scripts/run_phase5.py"],
            [sys.executable, "scripts/run_phase5.py", "--mutation", "mail-atomic"],
        ]
    if phase in {"6", "7"}:
        steps.insert(
            steps.index([sys.executable, "scripts/start_local.py"]) + 1,
            [sys.executable, "scripts/backup_local.py"],
        )
        offset = steps.index([sys.executable, "scripts/run_go_integration.py"])
        steps[offset:offset] = [
            [sys.executable, "scripts/run_phase6.py"],
            [sys.executable, "scripts/run_phase6.py", "--mutation", "epoch"],
            [sys.executable, "scripts/run_phase6.py", "--suite", "contracts"],
            [sys.executable, "scripts/run_phase6.py", "--suite", "benchmark"],
        ]
    if phase == "7":
        steps.insert(
            steps.index([sys.executable, "scripts/reproduce_clean.py"]),
            [sys.executable, "scripts/run_browser_smoke.py"],
        )
        steps.insert(1, [sys.executable, "scripts/audit_dependencies.py"])
        steps.insert(
            steps.index([sys.executable, "scripts/run_go_integration.py"]),
            [sys.executable, "scripts/run_phase6.py", "--mutation", "recovery"],
        )
        steps.insert(
            steps.index([sys.executable, "scripts/release_gate.py"]),
            [sys.executable, "scripts/backup_firebase_local.py"],
        )
    completed = []
    passed = False
    try:
        for args in steps:
            subprocess.run(args, cwd=TARGET, check=True)
            completed.append(args[1:])
        passed = True
    finally:
        write_json(
            "phase-3-ci.json",
            {
                "checked_utc": datetime.now(timezone.utc).isoformat(),
                "passed": passed,
                "exit_code": 0 if passed else 1,
                "completed_steps": completed,
                "source_fingerprint": fingerprint(source_hashes()),
                "providers_contacted": False,
            },
        )


if __name__ == "__main__":
    main()
