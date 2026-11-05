"""Install locked development tools without copying another workspace's caches."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(args, directory=ROOT):
    executable = shutil.which(str(args[0])) or str(args[0])
    command = [executable, *args[1:]]
    if os.name == "nt" and executable.lower().endswith((".cmd", ".bat")):
        command = ["cmd", "/d", "/c", *command]
    subprocess.run(command, cwd=directory, check=True)


def main():
    environment = ROOT / ".venv"
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.exists():
        run([sys.executable, "-m", "venv", str(environment)])
    (ROOT / ".quality/tmp").mkdir(parents=True, exist_ok=True)
    os.environ.update(TEMP=str(ROOT / ".quality/tmp"), TMP=str(ROOT / ".quality/tmp"))
    run([str(python), "-m", "pip", "install", "-r", "requirements-quality.txt"])
    npm = "npm.cmd" if os.name == "nt" else "npm"
    pnpm = "pnpm.cmd" if os.name == "nt" else "pnpm"
    if not shutil.which(pnpm):
        raise SystemExit("Install pnpm 10.8.1, then rerun bootstrap.py")
    run([npm, "ci", "--ignore-scripts", "--no-audit", "--no-fund"], ROOT / "FullStyle-Frontend")
    run([pnpm, "install", "--frozen-lockfile", "--ignore-scripts"], ROOT / "FullStyle-API-Gateway")
    run([npm, "ci", "--ignore-scripts", "--no-audit", "--no-fund"], ROOT / "tests/phase7")
    run(
        ["flutter.bat" if os.name == "nt" else "flutter", "pub", "get", "--enforce-lockfile"],
        ROOT / "FullStyle-App/fullstyle_aplication",
    )
    print("Development tools ready. Run .venv Python with scripts/ci.py for full validation.")


if __name__ == "__main__":
    main()
