"""Check the actual Git index, not ignored files on the author's workstation."""

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    entries = subprocess.check_output(["git", "ls-files", "--stage", "-z"], cwd=ROOT).decode()
    paths = []
    for entry in entries.split("\0"):
        if not entry:
            continue
        meta, relative = entry.split("\t", 1)
        if meta.startswith("160000"):
            raise ValueError("Embedded repository instead of tracked code: " + relative)
        path = Path(relative)
        if (
            (path.name.startswith(".env") and path.name != ".env.example")
            or path.suffix.lower() in {".key", ".pem", ".dump", ".pfx", ".p12", ".jks", ".exe"}
            or any(
                part in {".git", ".quality", "node_modules", ".venv", ".next", "build", "dist"}
                for part in path.parts
            )
        ):
            raise ValueError("Private or generated file in Git index: " + relative)
        paths.append(relative)
    for directory in [
        "FullStyle-API-Gateway",
        "FullStyle-App",
        "FullStyle-Backend",
        "FullStyle-Backend-Go",
        "FullStyle-Chatbot",
        "FullStyle-Email-Service",
        "FullStyle-Frontend",
        "FullStyle-ReverseProxy",
    ]:
        if not any(path.startswith(directory + "/") for path in paths):
            raise ValueError("Component missing from monorepo: " + directory)
    for name in [
        "FullStyle-Frontend/package-lock.json",
        "FullStyle-API-Gateway/pnpm-lock.yaml",
        "FullStyle-App/fullstyle_aplication/pubspec.lock",
        "tests/phase7/package-lock.json",
    ]:
        if name not in paths:
            raise ValueError("Reproducibility lock missing: " + name)
    for path in [ROOT / "README.md", *sorted((ROOT / "docs").rglob("*.md"))]:
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if "://" in target or target.startswith("#"):
                continue
            if not (path.parent / target.split("#")[0].strip("<>")).exists():
                raise ValueError("Broken documentation link: " + str(path.relative_to(ROOT)))
    print(
        json.dumps(
            {
                "passed": True,
                "tracked_files": len(paths),
                "components": 8,
                "gitlinks": 0,
                "private_artifacts": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
