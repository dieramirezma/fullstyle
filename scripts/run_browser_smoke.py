"""Real local browser proof of enrollment, offline recovery and operation pages."""

import json
import os
import shutil
import subprocess

from prepare_copy import DOCS, TARGET
from quality import fingerprint, source_hashes
from start_local import preflight


def main():
    preflight()
    before = source_hashes()
    location = TARGET / ".quality/ui-tools"
    location.mkdir(exist_ok=True)
    for name in ("package.json", "package-lock.json"):
        shutil.copy2(TARGET / "tests/phase7" / name, location / name)
    env = dict(
        os.environ,
        NODE_PATH=str(location / "node_modules"),
        TEMP=str(TARGET / ".quality/tmp"),
        TMP=str(TARGET / ".quality/tmp"),
    )
    subprocess.run(
        [
            "npm.cmd" if os.name == "nt" else "npm",
            "ci",
            "--ignore-scripts",
            "--no-audit",
            "--no-fund",
        ],
        cwd=location,
        env=env,
        check=True,
        timeout=180,
        stdout=subprocess.DEVNULL,
    )
    report = DOCS / "additional-browser.json"
    if os.name != "nt" and not env.get("PLAYWRIGHT_EXECUTABLE_PATH"):
        env["PLAYWRIGHT_BUNDLED_BROWSER"] = "1"
        subprocess.run(
            ["npx", "playwright", "install", "--with-deps", "chromium"],
            cwd=location,
            env=env,
            check=True,
            timeout=300,
        )
    result = subprocess.run(
        ["node", "tests/phase7/browser.cjs"],
        cwd=TARGET,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=240,
    )
    print(result.stdout + result.stderr)
    body = json.loads(report.read_text(encoding="utf-8"))
    body["source_fingerprint"] = fingerprint(before)
    body["source_stable"] = before == source_hashes()
    image_cache = subprocess.run(
        [
            "docker",
            "exec",
            "fullstyle-portfolio-frontend-1",
            "node",
            "-e",
            "const fs=require('fs');const p='/app/.next/standalone/.next/cache';process.exit(fs.realpathSync(p)==='/tmp' && fs.readdirSync('/tmp/images').length>0 ? 0 : 1)",
        ],
        capture_output=True,
        timeout=10,
    )
    body["image_cache_in_tmpfs"] = image_cache.returncode == 0
    body["passed"] = (
        body["passed"]
        and body["source_stable"]
        and result.returncode == 0
        and body["image_cache_in_tmpfs"]
    )
    report.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    if not body["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
