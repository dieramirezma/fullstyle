"""Validate local release evidence against current code and running images."""

import json
import subprocess

from prepare_copy import DOCS, TARGET, digest, evidence_name, evidence_path
from quality import fingerprint, source_hashes


def main():
    quality = json.loads(evidence_path("phase-3-quality.json").read_text(encoding="utf-8"))
    if not quality["passed"] or quality["source_fingerprint"] != fingerprint(source_hashes()):
        raise ValueError("Quality evidence is missing, failed or stale")
    for name in ("phase-3-runtime", "phase-3-security", "phase-3-go-tests", "phase-3-clean"):
        report = json.loads(evidence_path(name + ".json").read_text(encoding="utf-8"))
        if not report["passed"]:
            raise ValueError("Failed validation: " + name)
    runtime = json.loads(evidence_path("phase-3-runtime.json").read_text(encoding="utf-8"))
    for container in runtime["containers"]:
        service = container["service"]
        name = "email" if service == "email-worker" else service
        image = "fullstyle-portfolio-" + name + ":phase3"
        if service in {"postgres", "redis", "rabbitmq"}:
            image = {
                "postgres": "postgres:16-alpine",
                "redis": "redis:7-alpine",
                "rabbitmq": "rabbitmq:3-management",
            }[service]
        current = subprocess.check_output(
            ["docker", "image", "inspect", image, "--format", "{{.Id}}"], text=True
        ).strip()
        if current != container["image_id"]:
            raise ValueError("Image changed after contracts: " + service)
    clean = json.loads(evidence_path("phase-3-clean.json").read_text(encoding="utf-8"))
    if not clean["cleanup_complete"]:
        raise ValueError("Disposable project cleanup incomplete")
    for relative, expected in clean["source_sha256"].items():
        path = TARGET / relative
        if not path.is_file() or digest(path) != expected:
            raise ValueError("Clean reproduction is stale: " + relative)
    if evidence_name("phase-3-x") in {"phase-4-x", "phase-5-x", "phase-6-x", "phase-7-x"}:
        for name in (
            evidence_name("phase-3-consistency"),
            evidence_name("phase-3-mutation-worker-lock"),
            evidence_name("phase-3-mutation-cache-status"),
        ):
            report = json.loads(evidence_path(name + ".json").read_text(encoding="utf-8"))
            if not report["passed"] or report["source_fingerprint"] != fingerprint(source_hashes()):
                raise ValueError("Missing, failed or stale consistency evidence: " + name)
    if evidence_name("phase-3-x") in {"phase-5-x", "phase-6-x", "phase-7-x"}:
        for name in (
            evidence_name("phase-3-reliability"),
            evidence_name("phase-3-mutation-mail-atomic"),
        ):
            report = json.loads(evidence_path(name + ".json").read_text(encoding="utf-8"))
            if not report["passed"] or report["source_fingerprint"] != fingerprint(source_hashes()):
                raise ValueError("Missing, failed or stale reliability evidence: " + name)
    if evidence_name("phase-3-x") in {"phase-6-x", "phase-7-x"}:
        for name in (
            "phase-3-backup",
            "phase-3-pytest",
            "phase-3-mutation-epoch",
            "phase-3-contracts",
            "phase-3-benchmark",
        ):
            report = json.loads(evidence_path(name + ".json").read_text(encoding="utf-8"))
            if not report["passed"] or report["source_fingerprint"] != fingerprint(source_hashes()):
                raise ValueError("Missing, failed or stale phase-6 evidence: " + name)
    if evidence_name("phase-3-x") == "phase-7-x":
        browser = json.loads((DOCS / "additional-browser.json").read_text(encoding="utf-8"))
        if not browser["passed"] or browser["source_fingerprint"] != fingerprint(source_hashes()):
            raise ValueError("Browser recovery proof missing or stale")
        dependencies = json.loads(
            evidence_path("phase-3-dependencies.json").read_text(encoding="utf-8")
        )
        if not dependencies["passed"] or dependencies["source_fingerprint"] != fingerprint(
            source_hashes()
        ):
            raise ValueError("Dependency checks missing or stale")
        mutation = json.loads(
            evidence_path("phase-3-mutation-recovery.json").read_text(encoding="utf-8")
        )
        if not mutation["passed"] or mutation["source_fingerprint"] != fingerprint(source_hashes()):
            raise ValueError("Recovery guard regression proof missing or stale")
        report = json.loads(
            evidence_path("phase-3-firebase-backup.json").read_text(encoding="utf-8")
        )
        if not report["passed"] or report["source_fingerprint"] != fingerprint(source_hashes()):
            raise ValueError("Missing, failed or stale full backup evidence")
    print("PASS: local quality, source snapshots and images match validated evidence")


if __name__ == "__main__":
    main()
