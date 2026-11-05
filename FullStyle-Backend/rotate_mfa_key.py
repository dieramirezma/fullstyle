"""Offline atomic recipher; deploy a dual-read keyring before changing ciphertext."""

import argparse
import os

from cryptography.fernet import MultiFernet

from config.db_config import db
from config.server_config import create_app
from migrate_local import EXPECTED
from models.account_security_model import AccountSecurity
from models.completion_model import RefreshExchange
from utils.keyring import load_cipher


def recipher(old: MultiFernet, new: MultiFernet) -> int:
    count = 0
    # Stable order matches account operations. Any invalid token aborts the whole batch.
    for row in AccountSecurity.query.order_by(AccountSecurity.user_id).with_for_update().all():
        if row.secret:
            plain = old.decrypt(row.secret.encode())
            row.secret = new.encrypt(plain).decode()
            if new.decrypt(row.secret.encode()) != plain:
                raise ValueError("Recipher verification failed")
            count += 1
    for exchange in RefreshExchange.query.order_by(RefreshExchange.jti).with_for_update().all():
        plain = old.decrypt(exchange.encrypted_pair.encode())
        exchange.encrypted_pair = new.encrypt(plain).decode()
        count += 1
    return count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--old-keyring")
    parser.add_argument("--new-keyring", required=True)
    options = parser.parse_args()
    if os.getenv("LOCAL_RUNTIME") != "true" or os.getenv("DATABASE_URL") != EXPECTED:
        raise RuntimeError("Only the exact local synthetic database may be reciphered")
    app = create_app()
    with app.app_context():
        try:
            count = recipher(
                load_cipher(app.config["SECRET_KEY"], options.old_keyring),
                load_cipher(app.config["SECRET_KEY"], options.new_keyring),
            )
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
    print(f"PASS: {count} ciphertexts reciphered atomically; no key material logged")


if __name__ == "__main__":
    main()
