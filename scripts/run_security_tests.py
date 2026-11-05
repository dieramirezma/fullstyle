"""Run selected regressions in Docker with only synthetic PostgreSQL available."""

import argparse
import json
import subprocess
from datetime import datetime, timezone

from check_isolation import resolve, validate
from prepare_copy import DOCS, TARGET, digest, evidence_name, write_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report-prefix",
        choices=[
            "phase-2-tests",
            "phase-3-security",
            "phase-4-security",
            "phase-5-security",
            "phase-6-security",
            "phase-7-security",
        ],
        default=evidence_name("phase-3-security"),
    )
    prefix = parser.parse_args().report_prefix
    project = "fullstyle-portfolio"
    validate(resolve(), project)
    network = json.loads(
        subprocess.check_output(["docker", "network", "inspect", project + "_sandbox"])
    )[0]
    if not network["Internal"] or network["Labels"].get("com.docker.compose.project") != project:
        raise ValueError("Tests require the isolated local sandbox")
    args = [
        "docker",
        "run",
        "--rm",
        "--name",
        project + "-security",
        "--network",
        project + "_sandbox",
        "--read-only",
        "--tmpfs",
        "/tmp",
        "-e",
        "PYTHONPATH=/work/chatbot:/work/backend",
    ]
    for source, destination in [
        ("FullStyle-Backend", "/work/backend"),
        ("FullStyle-Chatbot/app", "/work/chatbot/app"),
        ("tests/security", "/work/tests"),
    ]:
        args += [
            "--mount",
            f"type=bind,source={TARGET / source},target={destination},readonly",
        ]
    args += ["fullstyle-portfolio-security:phase2"]
    source_hashes = {
        p.relative_to(TARGET).as_posix(): digest(p)
        for directory in (
            TARGET / "FullStyle-Backend/services",
            TARGET / "FullStyle-Backend/utils",
            TARGET / "FullStyle-Chatbot/app/core",
            TARGET / "tests/security",
        )
        for p in directory.glob("*.py")
    }
    image_id = subprocess.check_output(
        [
            "docker",
            "image",
            "inspect",
            "fullstyle-portfolio-security:phase2",
            "--format",
            "{{.Id}}",
        ],
        text=True,
    ).strip()
    result = subprocess.run(args, cwd=TARGET, capture_output=True, text=True, timeout=180)
    output = result.stdout + result.stderr
    (DOCS / (prefix + ".log")).write_text(output, encoding="utf-8")
    write_json(
        prefix + ".json",
        {
            "checked_utc": datetime.now(timezone.utc).isoformat(),
            "passed": result.returncode == 0,
            "exit_code": result.returncode,
            "network": project + "_sandbox",
            "report": prefix + ".log",
            "database": "synthetic PostgreSQL; unique schema per run, dropped on completion",
            "providers_contacted": False,
            "image_id": image_id,
            "source_sha256": source_hashes,
        },
    )
    print(output)
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
