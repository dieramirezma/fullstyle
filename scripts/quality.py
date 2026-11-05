"""Blocking local/CI quality checks. Reports are tied to the current source tree."""

import ast
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from prepare_copy import DOCS, EXCLUDED, TARGET, digest, evidence_name, write_json


def source_hashes():
    result = {}
    excluded = EXCLUDED | {".quality", ".ruff_cache"}
    extensions = {
        ".py",
        ".sql",
        ".ini",
        ".ts",
        ".tsx",
        ".js",
        ".cjs",
        ".mjs",
        ".go",
        ".dart",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".graphql",
        ".lock",
        ".conf",
        ".rules",
        ".css",
        ".html",
    }
    for directory, children, files in os.walk(TARGET):
        children[:] = [
            name
            for name in children
            if name not in excluded and not (Path(directory) == TARGET and name == "docs")
        ]
        for filename in files:
            path = Path(directory) / filename
            if (
                path.suffix in extensions
                or filename in {"go.mod", "go.sum", ".dockerignore", ".gitignore", ".prettierrc"}
                or filename.endswith("Dockerfile")
                or filename.startswith("requirements")
            ):
                result[path.relative_to(TARGET).as_posix()] = digest(path)
    return result


def fingerprint(hashes):
    return hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    before = source_hashes()
    checks = []
    artifact_dir = DOCS / evidence_name("quality-phase-3").replace("quality-phase-3", "quality")
    if evidence_name("phase-3-x") != "phase-3-x":
        artifact_dir = DOCS / ("quality-" + evidence_name("phase-3-x").removesuffix("-x"))
    artifact_dir.mkdir(exist_ok=True)
    # Keep compiler/tool temporaries on the independent workspace's drive.
    # Windows TEMP may be on a full system drive even when D: has ample space.
    tool_temp = TARGET / ".quality" / "tmp"
    tool_temp.mkdir(parents=True, exist_ok=True)
    tool_env = dict(os.environ, TEMP=str(tool_temp), TMP=str(tool_temp))
    ruff = TARGET / ".venv/Scripts/ruff.exe" if os.name == "nt" else TARGET / ".venv/bin/ruff"

    def run(name, args, repo=".", timeout=600):
        executable = shutil.which(str(args[0])) or str(args[0])
        command = [executable, *map(str, args[1:])]
        if os.name == "nt" and executable.lower().endswith((".cmd", ".bat")):
            command = ["cmd", "/d", "/c", *command]
        result = subprocess.run(
            command,
            cwd=TARGET / repo,
            env=tool_env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        (artifact_dir / (name + ".log")).write_text(result.stdout + result.stderr, encoding="utf-8")
        checks.append(
            {
                "check": name,
                "passed": result.returncode == 0,
                "exit_code": result.returncode,
                "report": artifact_dir.name + "/" + name + ".log",
            }
        )
        print(f"{'PASS' if result.returncode == 0 else 'FAIL'}: {name}", flush=True)
        if result.returncode:
            print((result.stdout + result.stderr)[-5000:])
            return False
        return True

    for name, repo in (
        ("python-tools", "."),
        ("python-business", "FullStyle-Backend"),
        ("python-chat", "FullStyle-Chatbot"),
        ("python-mail", "FullStyle-Email-Service"),
    ):
        run(name + "-lint", [ruff, "check", "scripts" if repo == "." else "."], repo)
        run(name + "-format", [ruff, "format", "--check", "scripts" if repo == "." else "."], repo)
    run(
        "python-tests-lint",
        [
            ruff,
            "check",
            "--isolated",
            "--select",
            "E4,E7,E9,F,I",
            "tests/security",
            "tests/phase3",
            "tests/phase4",
            "tests/phase5",
            "tests/phase6",
        ],
    )
    run(
        "python-tests-format",
        [
            ruff,
            "format",
            "--isolated",
            "--check",
            "tests/security",
            "tests/phase3",
            "tests/phase4",
            "tests/phase5",
            "tests/phase6",
        ],
    )
    run(
        "python-global-correctness",
        [
            ruff,
            "check",
            "--isolated",
            "--select",
            "E4,E7,E9,F",
            "FullStyle-Backend",
            "FullStyle-Chatbot",
            "FullStyle-Email-Service",
        ],
    )
    parsed = 0
    for relative in before:
        if relative.endswith(".py"):
            ast.parse((TARGET / relative).read_text(encoding="utf-8-sig"), filename=relative)
            parsed += 1
    checks.append({"check": "all-python-syntax", "passed": True, "files": parsed})
    run(
        "python-keyring-types",
        [
            sys.executable,
            "-m",
            "mypy",
            "--strict",
            "--follow-imports=skip",
            "--cache-dir",
            str(TARGET / ".quality/mypy-cache"),
            "FullStyle-Backend/utils/keyring.py",
        ],
    )
    for repo, prefix in (("FullStyle-Frontend", "frontend"), ("FullStyle-API-Gateway", "gateway")):
        for command in ("lint", "format:check", "typecheck"):
            run(
                prefix + "-" + command.replace(":", "-"),
                ["npm.cmd" if os.name == "nt" else "npm", "run", command],
                repo,
            )
    run(
        "gateway-build",
        ["npm.cmd" if os.name == "nt" else "npm", "run", "build"],
        "FullStyle-API-Gateway",
    )
    run("gateway-tests", ["npm.cmd" if os.name == "nt" else "npm", "test"], "FullStyle-API-Gateway")
    # Build includes gofmt, go vet, unit tests and compile with Go 1.24.3.
    run(
        "go-quality-and-build",
        [
            "docker",
            "build",
            "-t",
            "fullstyle-portfolio-auth:phase3",
            "-f",
            "docker/Auth.Dockerfile",
            ".",
        ],
        timeout=1800,
    )
    run("frontend-tests", ["npm.cmd" if os.name == "nt" else "npm", "test"], "FullStyle-Frontend")
    frontend_bin = TARGET / "FullStyle-Frontend/node_modules/.bin"
    suffix = ".cmd" if os.name == "nt" else ""
    run(
        "frontend-tools-lint",
        [
            frontend_bin / ("eslint" + suffix),
            "--no-eslintrc",
            "--config",
            ".eslintrc-tools.cjs",
            "scripts",
            "tests",
            "../tests/phase7",
            "--ext",
            ".cjs",
        ],
        "FullStyle-Frontend",
    )
    run(
        "frontend-tools-format",
        [
            frontend_bin / ("prettier" + suffix),
            "--check",
            "scripts",
            "tests",
            "../tests/phase7",
            "next.config.ts",
            ".eslintrc.json",
            ".prettierrc",
            ".eslintrc-tools.cjs",
            "package.json",
        ],
        "FullStyle-Frontend",
    )
    mobile = "FullStyle-App/fullstyle_aplication"
    run(
        "dart-format",
        [
            "dart.bat" if os.name == "nt" else "dart",
            "format",
            "--output=none",
            "--set-exit-if-changed",
            "lib",
            "test",
        ],
        mobile,
    )
    for name, args in (
        ("flutter-analysis", ["analyze", "--no-pub"]),
        ("flutter-tests", ["test", "--no-pub"]),
        (
            "flutter-web-build",
            [
                "build",
                "web",
                "--no-pub",
                "--no-web-resources-cdn",
                "--dart-define=FS_LOCAL_ONLY=true",
            ],
        ),
    ):
        run(name, ["flutter.bat" if os.name == "nt" else "flutter", *args], mobile)
    after = source_hashes()
    checks.append({"check": "source-stable-during-validation", "passed": before == after})
    passed = all(check["passed"] for check in checks)
    write_json(
        "phase-3-quality.json",
        {
            "checked_utc": datetime.now(timezone.utc).isoformat(),
            "passed": passed,
            "checks": checks,
            "source_fingerprint": fingerprint(after),
        },
    )
    write_json("phase-3-quality-sources.json", after)
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
