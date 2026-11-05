"""Run a pinned, checksum-verified Gitleaks without printing credential values."""

import argparse
import hashlib
import io
import os
import platform
import subprocess
import tarfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "8.30.1"


def scanner():
    folder = ROOT / ".quality/tools/gitleaks"
    folder.mkdir(parents=True, exist_ok=True)
    system = {"Windows": "windows", "Linux": "linux", "Darwin": "darwin"}[platform.system()]
    arch = "arm64" if platform.machine().lower() in {"arm64", "aarch64"} else "x64"
    extension = "zip" if system == "windows" else "tar.gz"
    name = f"gitleaks_{VERSION}_{system}_{arch}.{extension}"
    base = f"https://github.com/gitleaks/gitleaks/releases/download/v{VERSION}/"
    executable = folder / ("gitleaks.exe" if system == "windows" else "gitleaks")
    # Verify the downloaded archive on every invocation. Execute only its binary;
    # never extract arbitrary archive paths into the workspace.
    archive = folder / name
    if not archive.exists():
        with urllib.request.urlopen(base + name, timeout=60) as response:
            archive.write_bytes(response.read())
    with urllib.request.urlopen(base + f"gitleaks_{VERSION}_checksums.txt", timeout=30) as response:
        checksums = response.read().decode()
    expected = next(line.split()[0] for line in checksums.splitlines() if line.endswith(name))
    if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
        raise ValueError("Gitleaks archive checksum mismatch")
    if extension == "zip":
        with zipfile.ZipFile(archive) as bundle:
            binary = bundle.read(executable.name)
    else:
        with tarfile.open(fileobj=io.BytesIO(archive.read_bytes()), mode="r:gz") as bundle:
            member = bundle.extractfile("gitleaks")
            if member is None:
                raise ValueError("Gitleaks binary missing")
            binary = member.read()
    executable.write_bytes(binary)
    if os.name != "nt":
        executable.chmod(0o700)
    return executable


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", action="store_true")
    options = parser.parse_args()
    args = [str(scanner()), "git" if options.history else "dir", ".", "--redact", "--no-banner"]
    if options.history:
        args += ["--log-opts=--all"]
    subprocess.run(args, cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
