"""Workspace helpers shared by the portable demo and its validation scripts.

The module name is retained for compatibility with the modernization tooling.
It never copies repositories or accesses another local checkout.
"""

import hashlib
import json
import os
from pathlib import Path

TARGET = Path(__file__).resolve().parents[1]
DOCS = TARGET / ".quality/reports"
DOCS.mkdir(parents=True, exist_ok=True)
EXCLUDED = {
    ".git",
    "node_modules",
    ".next",
    ".dart_tool",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
    ".gradle",
    ".vercel",
    "ephemeral",
    ".pytest_cache",
    ".mypy_cache",
    "coverage",
    "logs",
    "fullstyle-rewrite",
}


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def evidence_name(name):
    phase = os.environ.get("FULLSTYLE_VALIDATION_PHASE", "7")
    if phase not in {"3", "4", "5", "6", "7"}:
        raise ValueError("Unsupported evidence phase")
    return name.replace("phase-3-", f"phase-{phase}-", 1)


def evidence_path(name):
    return DOCS / evidence_name(name)


def write_json(name, value):
    evidence_path(name).write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
