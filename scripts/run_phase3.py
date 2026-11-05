"""Run real network/data contracts and save evidence without exposing credentials."""

import json
import subprocess
import sys
from datetime import datetime, timezone

from check_local_stack import COMPOSE, PROJECT, resolve_local, validate
from prepare_copy import TARGET, evidence_name, evidence_path, write_json
from start_local import preflight


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    preflight()
    config = resolve_local()
    validate(config)
    network = json.loads(
        subprocess.check_output(["docker", "network", "inspect", PROJECT + "_sandbox"])
    )[0]
    if not network["Internal"]:
        raise ValueError("Runtime tests require the internal network")
    ready_ids = subprocess.check_output(COMPOSE + ["ps", "-q"], text=True).split()
    if len(ready_ids) != 12:
        raise ValueError("Start all twelve long-running containers before contracts")
    for info in json.loads(subprocess.check_output(["docker", "inspect", *ready_ids])):
        if info["State"].get("Health", {}).get("Status") not in (None, "healthy"):
            raise ValueError("Wait for stack health before contracts")
    args = [
        "docker",
        "run",
        "--rm",
        "--name",
        PROJECT + "-contracts",
        "--network",
        PROJECT + "_sandbox",
        "--read-only",
        "--tmpfs",
        "/tmp",
        "--mount",
        f"type=bind,source={TARGET / 'tests/phase3'},target=/tests,readonly",
    ]
    for key, value in config["services"]["backend"]["environment"].items():
        args += ["-e", f"{key}={value}"]
    args += [
        "-e",
        "PYTHONPATH=/app",
        "fullstyle-portfolio-backend:phase3",
        "python",
        "-m",
        "unittest",
        "discover",
        "-s",
        "/tests",
        "-v",
    ]
    result = subprocess.run(
        args,
        cwd=TARGET,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=240,
    )
    log = result.stdout + result.stderr
    # Phase 6 also has a separate MFA contracts suite; keep both logs intact.
    log_name = (
        "phase-3-http-contracts.log"
        if evidence_name("phase-3-x") in {"phase-6-x", "phase-7-x"}
        else "phase-3-contracts.log"
    )
    evidence_path(log_name).write_text(log, encoding="utf-8")
    containers = []
    ids = subprocess.check_output(COMPOSE + ["ps", "-q"], text=True).split()
    for container in json.loads(subprocess.check_output(["docker", "inspect", *ids])):
        service = container["Config"]["Labels"]["com.docker.compose.service"]
        networks = set(container["NetworkSettings"]["Networks"])
        expected = (
            {PROJECT + "_sandbox", PROJECT + "_ingress"}
            if service == "proxy"
            else {PROJECT + "_sandbox"}
        )
        if networks != expected:
            raise ValueError("Unexpected runtime networks")
        containers.append(
            {
                "service": service,
                "image_id": container["Image"],
                "state": container["State"]["Status"],
                "health": container["State"].get("Health", {}).get("Status"),
                "networks": sorted(networks),
            }
        )
    write_json(
        "phase-3-runtime.json",
        {
            "checked_utc": datetime.now(timezone.utc).isoformat(),
            "passed": result.returncode == 0,
            "exit_code": result.returncode,
            "report": evidence_name(log_name),
            "providers_contacted": False,
            "containers": containers,
        },
    )
    print(log)
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
