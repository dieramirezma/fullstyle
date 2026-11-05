"""Quiesced synthetic backup bundle; restore Firebase separately and verify keys."""

import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from check_local_stack import COMPOSE, PROJECT, resolve_local
from cryptography.fernet import Fernet
from prepare_copy import DOCS, TARGET, write_json
from quality import fingerprint, source_hashes
from start_local import preflight


def main():
    preflight()
    before = source_hashes()
    suffix = uuid4().hex
    name = "fullstyle-backup-" + suffix
    destination = TARGET / ".quality" / name
    destination.mkdir()
    network = name + "-network"
    restore = name + "-firebase"
    source = PROJECT + "-firebase-1"
    backend_image = "fullstyle-portfolio-backend:phase3"
    firebase_image = "fullstyle-portfolio-firebase:phase3"
    apps = ["backend", "auth", "chatbot", "email", "email-worker", "gateway", "frontend", "proxy"]
    stopped = []
    cleanup = passed = False
    original_manifest = restored_manifest = None
    escrow_path = encrypted_path = None
    label = "fullstyle.backup=" + suffix

    def run(args, timeout=120, **kwargs):
        return subprocess.run(
            args, cwd=TARGET, check=True, capture_output=True, timeout=timeout, **kwargs
        )

    def probe(mode, network_name=PROJECT + "_sandbox", host="firebase"):
        args = [
            "docker",
            "run",
            "--rm",
            "--network",
            network_name,
            "--read-only",
            "--tmpfs",
            "/tmp",
            "--label",
            label,
            "--mount",
            f"type=bind,source={TARGET / 'tests/phase6'},target=/tests,readonly",
            "-e",
            f"FIREBASE_AUTH_EMULATOR_HOST={host}:9099",
            "-e",
            f"FIRESTORE_EMULATOR_HOST={host}:8085",
            "-e",
            "GCLOUD_PROJECT=demo-fullstyle",
            backend_image,
            "python",
            "/tests/firebase_backup_probe.py",
            mode,
            suffix,
        ]
        return run(args, text=True, encoding="utf-8").stdout.strip()

    try:
        probe("seed")
        running = set(
            run(COMPOSE + ["ps", "--status", "running", "--services"], text=True).stdout.split()
        )
        stopped = sorted(running & set(apps))
        if stopped:
            run(COMPOSE + ["stop", *stopped], timeout=180)
        original_manifest = json.loads(probe("manifest"))
        run([sys.executable, "scripts/backup_local.py"], timeout=180)
        sql_report = json.loads((DOCS / "phase-7-backup.json").read_text(encoding="utf-8"))
        if not sql_report["passed"]:
            raise RuntimeError("SQL backup proof failed")
        run(
            [
                "docker",
                "exec",
                source,
                "firebase",
                "emulators:export",
                "/tmp/" + name,
                "--project",
                "demo-fullstyle",
                "--force",
            ],
            timeout=180,
        )
        # Docker Desktop's archive API cannot reliably see this tmpfs mount.
        # Stream files through exec and validate paths before writing on Windows.
        exported = run(
            ["docker", "exec", source, "tar", "-C", "/tmp/" + name, "-cf", "-", "."]
        ).stdout
        export_root = (destination / "firebase").resolve()
        export_root.mkdir()
        with tarfile.open(fileobj=io.BytesIO(exported), mode="r:") as archive:
            for member in archive.getmembers():
                target = (export_root / member.name).resolve()
                if not target.is_relative_to(export_root) or not (
                    member.isfile() or member.isdir()
                ):
                    raise ValueError("Unsafe emulator export path or file type")
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.extractfile(member).read())
        if not (destination / "firebase/firebase-export-metadata.json").is_file():
            raise RuntimeError("Firebase export metadata missing")
        run(["docker", "network", "create", "--internal", "--label", label, network])
        run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                restore,
                "--label",
                label,
                "--network",
                network,
                "--read-only",
                "--tmpfs",
                "/tmp",
                "--mount",
                f"type=bind,source={destination / 'firebase'},target=/backup,readonly",
                "-e",
                "GCLOUD_PROJECT=demo-fullstyle",
                "-e",
                "XDG_CONFIG_HOME=/tmp/config",
                "-e",
                "FIREBASE_CLI_DISABLE_UPDATE_CHECK=1",
                "-w",
                "/tmp",
                firebase_image,
                "firebase",
                "emulators:start",
                "--config",
                "/emulators/firebase.json",
                "--only",
                "auth,firestore",
                "--project",
                "demo-fullstyle",
                "--import",
                "/backup",
            ]
        )
        for _ in range(45):
            check = subprocess.run(
                [
                    "docker",
                    "exec",
                    restore,
                    "node",
                    "-e",
                    "Promise.all([fetch('http://127.0.0.1:9099/'),fetch('http://127.0.0.1:8085/')]).catch(()=>process.exit(1))",
                ],
                capture_output=True,
                timeout=5,
            )
            if check.returncode == 0:
                break
            time.sleep(1)
        else:
            raise RuntimeError("Restore emulator did not become ready")
        restored_manifest = json.loads(probe("manifest", network, restore))
        if original_manifest != restored_manifest:
            raise RuntimeError("Firebase restore logical content mismatch")
        probe("verify", network, restore)
        config = resolve_local()["services"]
        key_data = {
            key: config[service]["environment"][key]
            for service, key in [
                ("backend", "SECRET_KEY"),
                ("backend", "JWT_SECRET_KEY"),
                ("backend", "INTEGRATION_SECRET"),
                ("frontend", "NEXTAUTH_SECRET"),
            ]
        }
        # Escrow and bundle stay outside Git, in distinct directories. Restore proof
        # checks the encrypted archive, not a separately retained plaintext copy.
        escrow = TARGET / ".quality/key-escrow"
        escrow.mkdir(exist_ok=True)
        escrow_path = escrow / (suffix + ".key")
        key = Fernet.generate_key()
        escrow_path.write_bytes(key)
        if os.name == "nt":
            identity = subprocess.check_output(["whoami"], text=True).strip()
            run(["icacls", str(escrow_path), "/inheritance:r", "/grant:r", identity + ":F"])
        contents = {
            "keys.json": json.dumps(key_data).encode(),
            "postgres.dump": Path(sql_report["backup_path"]).read_bytes(),
        }
        contents.update(
            {
                "firebase/" + p.relative_to(destination / "firebase").as_posix(): p.read_bytes()
                for p in (destination / "firebase").rglob("*")
                if p.is_file()
            }
        )
        archive = io.BytesIO()
        with tarfile.open(fileobj=archive, mode="w:gz") as tar:
            for filename, body in contents.items():
                item = tarfile.TarInfo(filename)
                item.size = len(body)
                tar.addfile(item, io.BytesIO(body))
        encrypted_path = destination / "fullstyle-local-backup.tar.gz.fernet"
        encrypted_path.write_bytes(Fernet(key).encrypt(archive.getvalue()))
        restored = Fernet(escrow_path.read_bytes()).decrypt(encrypted_path.read_bytes())
        with tarfile.open(fileobj=io.BytesIO(restored), mode="r:gz") as tar:
            actual = {member.name: tar.extractfile(member).read() for member in tar.getmembers()}
        if actual != contents:
            raise RuntimeError("Encrypted bundle restoration mismatch")
        # A key restoration must actually decrypt the MFA format, not just equal a JSON value.
        from base64 import urlsafe_b64encode

        original_key = urlsafe_b64encode(hashlib.sha256(key_data["SECRET_KEY"].encode()).digest())
        recovered_key = urlsafe_b64encode(
            hashlib.sha256(json.loads(actual["keys.json"])["SECRET_KEY"].encode()).digest()
        )
        assert (
            Fernet(recovered_key).decrypt(Fernet(original_key).encrypt(b"synthetic-totp-proof"))
            == b"synthetic-totp-proof"
        )
        passed = True
    finally:
        identifiers = subprocess.check_output(
            ["docker", "ps", "-aq", "--filter", "label=" + label], text=True
        ).split()
        if identifiers:
            run(["docker", "rm", "-f", "-v", *identifiers])
        networks = subprocess.check_output(
            ["docker", "network", "ls", "-q", "--filter", "label=" + label], text=True
        ).split()
        if networks:
            run(["docker", "network", "rm", *networks])
        cleanup = not subprocess.check_output(
            ["docker", "ps", "-aq", "--filter", "label=" + label]
        ).strip()
        try:
            probe("cleanup")
        finally:
            if stopped:
                run(
                    COMPOSE
                    + ["up", "-d", "--no-deps", "--wait", "--wait-timeout", "180", *stopped],
                    timeout=240,
                )
        write_json(
            "phase-3-firebase-backup.json",
            {
                "checked_utc": datetime.now(timezone.utc).isoformat(),
                "passed": passed and cleanup and before == source_hashes(),
                "source_fingerprint": fingerprint(before),
                "cleanup_complete": cleanup,
                "original_manifest": original_manifest,
                "restored_manifest": restored_manifest,
                "encrypted_bundle": str(encrypted_path),
                "escrow_path": str(escrow_path),
                "bundle_sha256": hashlib.sha256(encrypted_path.read_bytes()).hexdigest()
                if encrypted_path and encrypted_path.exists()
                else None,
                "scope": "Synthetic Docker only: quiesced PostgreSQL, Firebase Auth/Firestore and runtime keys; not offsite storage or provider backup",
                "providers_contacted": False,
            },
        )
    if not passed or not cleanup or before != source_hashes():
        raise SystemExit(1)
    print(
        "PASS: Firebase restored with identical logical contents; encrypted SQL/Firebase/key bundle verified"
    )


if __name__ == "__main__":
    main()
