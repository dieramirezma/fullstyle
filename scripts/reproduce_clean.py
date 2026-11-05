"""Rebuild tracked source without dependencies; boot fresh synthetic volumes.

The disposable project has unique names, a separate ingress port and no original
mounts. Only its validated volumes/containers are removed in finally.
"""

import copy
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from check_local_stack import APPS, PROJECT, resolve_local, validate
from prepare_copy import EXCLUDED, TARGET, digest, evidence_name, evidence_path, write_json
from start_local import preflight


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    preflight()
    suffix = uuid4().hex[:8]
    project = PROJECT + "-clean-" + suffix
    source = TARGET / ".quality" / ("clean-source-" + suffix)
    source.mkdir(parents=True, exist_ok=False)
    hashes = {}
    excluded = EXCLUDED | {".quality", ".ruff_cache", ".github"}
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=TARGET).decode().split("\0")
    for name in tracked:
        if not name:
            continue
        relative = Path(name)
        if relative.parts[0] == "docs" or any(part in excluded for part in relative.parts):
            continue
        path = TARGET / relative
        if path.is_symlink():
            raise ValueError("Symlink not allowed in clean source")
        destination = source / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        if digest(path) != digest(destination):
            raise ValueError("Source snapshot mismatch")
        hashes[relative.as_posix()] = digest(destination)
    config = copy.deepcopy(resolve_local())
    config["name"] = project
    for group in ("networks", "volumes"):
        for name, entry in config[group].items():
            entry["name"] = project + "_" + name
    for name in APPS:
        service = config["services"][name]
        service["image"] = service["image"].replace(":phase3", ":phase3-clean-" + suffix)
        service["build"]["context"] = str(source)
    config["services"]["proxy"]["ports"][0]["published"] = "38081"
    for name in ("backend", "db-init"):
        config["services"][name]["environment"]["APP_WEB_URL"] = "http://localhost:38081/"
    config["services"]["frontend"]["environment"]["NEXTAUTH_URL"] = "http://localhost:38081"
    validate(config, project=project, source_root=source)
    compose_file = source.parent / ("clean-compose-" + suffix + ".json")
    compose_file.write_text(json.dumps(config, indent=2), encoding="utf-8")
    compose = [
        "docker",
        "compose",
        "--project-directory",
        str(TARGET),
        "-p",
        project,
        "-f",
        str(compose_file),
    ]
    if subprocess.check_output(
        ["docker", "ps", "-aq", "--filter", "label=com.docker.compose.project=" + project]
    ).strip():
        raise ValueError("Fresh project unexpectedly exists")
    passed = False
    image_ids = {}
    cleanup_ok = False
    log_path = evidence_path("phase-3-clean.log")
    with log_path.open("w", encoding="utf-8") as log:

        def run(args, timeout):
            log.write("COMMAND " + " ".join(args[:7]) + "\n")
            log.flush()
            return subprocess.run(
                args, cwd=TARGET, stdout=log, stderr=subprocess.STDOUT, timeout=timeout
            )

        try:
            print("Rebuilding clean source in " + project, flush=True)
            result = run(compose + ["build"], 1800)
            if result.returncode:
                raise RuntimeError("Clean build failed; see phase-3-clean.log")
            print("Starting independent empty data volumes", flush=True)
            result = run(compose + ["up", "-d", "--wait", "--wait-timeout", "240"], 300)
            if result.returncode:
                raise RuntimeError("Clean startup failed; see phase-3-clean.log")
            args = [
                "docker",
                "run",
                "--rm",
                "--name",
                project + "-contracts",
                "--network",
                project + "_sandbox",
                "--read-only",
                "--tmpfs",
                "/tmp",
                "--mount",
                f"type=bind,source={source / 'tests/phase3'},target=/tests,readonly",
                "-e",
                "PYTHONPATH=/app",
            ]
            for key, value in config["services"]["backend"]["environment"].items():
                args += ["-e", f"{key}={value}"]
            args += [
                config["services"]["backend"]["image"],
                "python",
                "-m",
                "unittest",
                "discover",
                "-s",
                "/tests",
                "-v",
            ]
            print("Running contracts against clean images and data", flush=True)
            result = run(args, 240)
            passed = result.returncode == 0
            for name in APPS:
                image_ids[name] = subprocess.check_output(
                    [
                        "docker",
                        "image",
                        "inspect",
                        config["services"][name]["image"],
                        "--format",
                        "{{.Id}}",
                    ],
                    text=True,
                ).strip()
        finally:
            # Validate exact project and volume names again before deleting test data.
            validate(config, project=project, source_root=source)
            cleanup_ok = (
                run(compose + ["down", "--volumes", "--remove-orphans"], 180).returncode == 0
            )
            leftovers = subprocess.check_output(
                [
                    "docker",
                    "volume",
                    "ls",
                    "-q",
                    "--filter",
                    "label=com.docker.compose.project=" + project,
                ]
            ).strip()
            cleanup_ok = cleanup_ok and not leftovers
            write_json(
                "phase-3-clean.json",
                {
                    "checked_utc": datetime.now(timezone.utc).isoformat(),
                    "passed": passed and cleanup_ok,
                    "project": project,
                    "source_snapshot": str(source),
                    "source_sha256": hashes,
                    "image_ids": image_ids,
                    "fresh_volumes": True,
                    "providers_contacted": False,
                    "cleanup_complete": bool(cleanup_ok),
                    "report": evidence_name("phase-3-clean.log"),
                },
            )
    if not passed or not cleanup_ok:
        raise SystemExit("Clean reproduction failed; inspect phase-3-clean.log")
    print("PASS: clean build/start/contracts; disposable volumes removed")


if __name__ == "__main__":
    main()
