"""Fresh public-registry advisories for the locked local Python/Node packages."""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone

from prepare_copy import TARGET, digest, write_json
from quality import fingerprint, source_hashes


def main():
    before = source_hashes()
    results = []
    for component in (
        "FullStyle-Backend",
        "FullStyle-Chatbot",
        "FullStyle-Email-Service",
        "tests/security",
    ):
        lock = component + (
            "/requirements.lock" if component == "tests/security" else "/requirements-local.lock"
        )
        command = [
            sys.executable,
            "-m",
            "pip_audit",
            "-r",
            lock,
            "--no-deps",
            "--disable-pip",
            "--desc",
            "off",
            "--format",
            "json",
        ]
        result = subprocess.run(
            command, cwd=TARGET, capture_output=True, text=True, encoding="utf-8", timeout=180
        )
        body = json.loads(result.stdout)
        vulnerabilities = [
            {
                "package": entry["name"],
                "version": entry["version"],
                "vulnerabilities": entry["vulns"],
            }
            for entry in body["dependencies"]
            if entry["vulns"]
        ]
        results.append(
            {
                "component": component,
                "lock_sha256": digest(TARGET / lock),
                "passed": result.returncode == 0 and not vulnerabilities,
                "vulnerabilities": vulnerabilities,
                "packages": len(body["dependencies"]),
            }
        )
    for component, tool, lock in (
        ("FullStyle-Frontend", "npm.cmd", "package-lock.json"),
        ("FullStyle-API-Gateway", "pnpm.cmd", "pnpm-lock.yaml"),
        ("tests/phase7", "npm.cmd", "package-lock.json"),
    ):
        result = subprocess.run(
            [tool if os.name == "nt" else tool.removesuffix(".cmd"), "audit", "--json"],
            cwd=TARGET / component,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
        )
        body = json.loads(result.stdout)
        counts = body["metadata"]["vulnerabilities"]
        results.append(
            {
                "component": component,
                "lock_sha256": digest(TARGET / component / lock),
                "passed": result.returncode == 0
                and sum(counts.get(k, 0) for k in ("critical", "high", "moderate", "low")) == 0,
                "counts": counts,
            }
        )
    passed = all(result["passed"] for result in results) and before == source_hashes()
    write_json(
        "phase-3-dependencies.json",
        {
            "checked_utc": datetime.now(timezone.utc).isoformat(),
            "passed": passed,
            "source_fingerprint": fingerprint(before),
            "checks": results,
            "scope": "public package advisories including dev dependencies; Go reachable-symbol audit in Auth Docker build; no provider credentials or provider APIs",
        },
    )
    for result in results:
        print(f"{'PASS' if result['passed'] else 'FAIL'}: {result['component']}")
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
