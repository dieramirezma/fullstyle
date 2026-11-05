"""Run meaningful pytest regressions on per-case schemas of the guarded local DB."""

import argparse
import json
import subprocess
from datetime import datetime, timezone
from uuid import uuid4

from check_local_stack import PROJECT, resolve_local, validate
from prepare_copy import DOCS, TARGET, digest, evidence_name, write_json
from quality import fingerprint, source_hashes
from start_local import preflight


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", choices=["pytest", "benchmark", "contracts"], default="pytest")
    parser.add_argument("--mutation", choices=["epoch", "recovery"])
    options = parser.parse_args()
    if options.mutation and options.suite != "pytest":
        parser.error("epoch mutation applies only to pytest")
    preflight()
    config = resolve_local()
    validate(config)
    before = source_hashes()
    name = "phase6-pytest-" + uuid4().hex
    report = evidence_name("phase-3-") + (
        "mutation-" + options.mutation if options.mutation else options.suite
    )
    args = [
        "docker",
        "run",
        "--rm",
        "--name",
        name,
        "--network",
        PROJECT + "_sandbox",
        "--read-only",
        "--tmpfs",
        "/tmp",
        "--mount",
        f"type=bind,source={TARGET / 'FullStyle-Backend'},target=/app,readonly",
        "--mount",
        f"type=bind,source={TARGET / 'FullStyle-Chatbot'},target=/chatbot,readonly",
        "-e",
        "PYTHONPATH=/app",
        "-e",
        "PYTHONDONTWRITEBYTECODE=1",
        "--mount",
        f"type=bind,source={TARGET / 'tests/phase6'},target=/tests,readonly",
    ]
    for key, value in config["services"]["backend"]["environment"].items():
        args += ["-e", f"{key}={value}"]
    provenance = None
    if options.suite == "benchmark":
        snapshots = TARGET / ".quality" / name
        snapshots.mkdir()
        fixtures = TARGET / "tests/fixtures/schedule"
        expected = json.loads((fixtures / "manifest.json").read_text(encoding="utf-8"))
        for name, expected_hash in expected.items():
            if digest(fixtures / name) != expected_hash:
                raise ValueError("Historical benchmark fixture changed: " + name)
            (snapshots / name).write_bytes((fixtures / name).read_bytes())
        provenance = {"extracted_functions_sha256": expected, "source": "tests/fixtures/schedule"}
        args += ["--mount", f"type=bind,source={snapshots},target=/comparison,readonly"]
    args += ["fullstyle-portfolio-backend:phase3", "python"]
    if options.suite == "pytest":
        pytest_args = ["-p", "no:cacheprovider", "-v", "--tb=short"]
        if options.mutation == "recovery":
            pytest_args += ["tests/test_completion.py::test_recovery_lockout_persists"]
            code = (
                "import services.completion_service as s; s.consume_code=lambda *args: True; import pytest; raise SystemExit(pytest.main("
                + repr(pytest_args)
                + "))"
            )
            args += ["-c", code]
        elif options.mutation:
            pytest_args += [
                "tests/test_security_policy.py::test_mfa_activation_revokes_legacy_tokens_and_otp_replay"
            ]
            code = (
                "import utils.sessions as s; s.session_valid=lambda *args: True; import pytest; raise SystemExit(pytest.main("
                + repr(pytest_args)
                + "))"
            )
            args += ["-c", code]
        else:
            args += ["-m", "pytest", *pytest_args]
    else:
        args += ["/tests/" + ("benchmark.py" if options.suite == "benchmark" else "contracts.py")]
    result = None
    try:
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
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)
    output = result.stdout + result.stderr
    (DOCS / (report + ".log")).write_text(output, encoding="utf-8")
    stable = source_hashes() == before
    detected = bool(
        options.mutation
        and result.returncode == 1
        and "1 failed" in output
        and "assert 200 == 401" in output
        and "ERROR" not in output
    )
    passed = (detected if options.mutation else result.returncode == 0) and stable
    details = None
    if result.returncode == 0 and options.suite != "pytest":
        details = json.loads(result.stdout.splitlines()[-1])
    write_json(
        report + ".json",
        {
            "checked_utc": datetime.now(timezone.utc).isoformat(),
            "passed": passed,
            "exit_code": result.returncode,
            "source_fingerprint": fingerprint(before),
            "source_stable": stable,
            "report": report + ".log",
            "regression_detected": detected,
            "provenance": provenance,
            "details": details,
            "providers_contacted": False,
        },
    )
    print(output)
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
