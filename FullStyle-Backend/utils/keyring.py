"""Explicit versioned Fernet keyring, with the legacy derived key as fallback."""

import base64
import hashlib
import json
from pathlib import Path

from cryptography.fernet import Fernet, MultiFernet


def load_cipher(secret: str, keyring_file: str | None = None) -> MultiFernet:
    if keyring_file:
        body = json.loads(Path(keyring_file).read_text(encoding="utf-8"))
        if not isinstance(body, dict) or body.get("version") != 1:
            raise ValueError("Unknown keyring format")
        keys = body.get("keys")
        if (
            not isinstance(keys, list)
            or not 1 <= len(keys) <= 4
            or not all(isinstance(key, str) for key in keys)
        ):
            raise ValueError("Keyring must contain 1-4 Fernet keys; first key encrypts")
        return MultiFernet([Fernet(key.encode("ascii")) for key in keys])
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
    return MultiFernet([Fernet(key)])
