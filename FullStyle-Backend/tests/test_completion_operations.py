"""Mail replay, data retention and key rotation assert durable effects and rollback."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from sqlalchemy import text

from config.db_config import db
from models.account_security_model import AccountSecurity
from models.reliability_model import MailEvent
from models.user_model import UserModel
from rotate_mfa_key import recipher
from utils.keyring import load_cipher


def auth(token):
    return {"Authorization": "Bearer " + token}


def test_mail_retry_is_owner_scoped_idempotent_and_never_replays_delivery(
    app, client, token, setup_user
):
    with app.app_context():
        db.session.add(
            MailEvent(
                id="owned",
                payload={
                    "email_type": "contact",
                    "data": {"email": setup_user["email"], "name": "test", "message": "test"},
                },
                payload_hash="a" * 64,
                state="dead",
            )
        )
        db.session.add(
            MailEvent(
                id="foreign",
                payload={"email_type": "contact", "data": {"email": "other@synthetic.invalid"}},
                payload_hash="b" * 64,
                state="dead",
            )
        )
        db.session.commit()
    assert [
        e["event_id"] for e in client.get("/api/mail/events", headers=auth(token)).json["events"]
    ] == ["owned"]
    body = {"operation_id": "retry-1", "reason": "Review local transport"}
    assert (
        client.post("/api/mail/events/foreign/retry", headers=auth(token), json=body).status_code
        == 404
    )
    path = "/api/mail/events/owned/retry"
    assert client.post(path, headers=auth(token), json=body).json["duplicate"] is False
    assert client.post(path, headers=auth(token), json=body).json["duplicate"] is True
    assert (
        client.post(path, headers=auth(token), json={**body, "reason": "different"}).status_code
        == 409
    )
    with app.app_context():
        assert db.session.execute(text("SELECT count(*) FROM mail_review")).scalar_one() == 1
        db.session.get(MailEvent, "owned").state = "delivered"
        db.session.commit()
    assert (
        client.post(path, headers=auth(token), json={**body, "operation_id": "retry-2"}).status_code
        == 409
    )


def test_key_rotation_preserves_plaintext_and_rolls_back_whole_batch(app, legacy_user):
    old, new = (
        MultiFernet([Fernet(Fernet.generate_key())]),
        MultiFernet([Fernet(Fernet.generate_key())]),
    )
    with app.app_context():
        db.session.add(
            AccountSecurity(user_id=legacy_user, secret=old.encrypt(b"totp-seed").decode())
        )
        db.session.commit()
        assert recipher(old, new) == 1
        db.session.commit()
        row = db.session.get(AccountSecurity, legacy_user)
        assert new.decrypt(row.secret.encode()) == b"totp-seed"
        with pytest.raises(InvalidToken):
            old.decrypt(row.secret.encode())
        # Reversing with the retained key restores a decryptable ciphertext.
        assert recipher(new, old) == 1
        db.session.commit()
        row = db.session.get(AccountSecurity, legacy_user)
        original = row.secret
        other = UserModel(email="keytest@synthetic.invalid", name="test", password="unused")
        db.session.add(other)
        db.session.flush()
        db.session.add(AccountSecurity(user_id=other.id, secret="corrupted"))
        db.session.commit()
        with pytest.raises(InvalidToken):
            recipher(old, new)
        db.session.rollback()
        assert db.session.get(AccountSecurity, legacy_user).secret == original


def test_keyring_accepts_dual_read_and_rejects_invalid_format(tmp_path):
    a, b = Fernet.generate_key(), Fernet.generate_key()
    path = tmp_path / "keys.json"
    path.write_text(json.dumps({"version": 1, "keys": [b.decode(), a.decode()]}))
    ring = load_cipher("unused", str(path))
    assert ring.decrypt(Fernet(a).encrypt(b"old")) == b"old"
    assert Fernet(b).decrypt(ring.encrypt(b"new")) == b"new"
    path.write_text('{"version":2,"keys":[]}')
    with pytest.raises(ValueError):
        load_cipher("unused", str(path))


def test_chat_review_is_scoped_preserves_tombstone_and_retention_skips_uncertain(
    app, setup_user, monkeypatch
):
    # Load only the repository. No model, LLM, or provider startup is imported.
    location = Path("/chatbot/app/repositories/chat_store.py")
    spec = importlib.util.spec_from_file_location("completion_chat_store", location)
    store = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(store)
    monkeypatch.setenv("RELIABILITY_SCHEMA", app.config["TEST_SCHEMA"])
    with app.app_context():
        user_id = UserModel.query.one().id
        message = "cancelar 1"
        digest = hashlib.sha256(message.encode()).hexdigest()
        for operation, state in [
            ("review-me", "uncertain"),
            ("keep-me", "pending"),
            ("expired", "completed"),
        ]:
            db.session.execute(
                text(
                    "INSERT INTO chat_turn(user_id,session_id,operation_id,message,message_hash,reply,state,content_expires_at) VALUES(:u,'test',:o,:m,:h,'reply',:s,now()-interval '1 day')"
                ),
                {"u": user_id, "o": operation, "m": message, "h": digest, "s": state},
            )
        db.session.commit()
    with pytest.raises(Exception) as error:
        store.review(user_id + 1, "test", "review-me", "checked")
    assert error.value.status_code == 404
    assert store.review(user_id, "test", "review-me", "Booking is cancelled")["reexecuted"] is False
    assert store.redact_expired() == 2
    rows = {r["operation_id"]: r for r in store.history(user_id, "test")}
    assert rows["review-me"]["message"] == "" and rows["review-me"]["state"] == "reviewed"
    assert rows["keep-me"]["message"] == message
    replay = store.Conversation(user_id, "test", "expired", message)
    try:
        assert replay.begin()[0] == "Contenido expirado por retención"
        assert replay.replayed
    finally:
        replay.close()
    denied = store.Conversation(user_id, "test", "review-me", message)
    try:
        with pytest.raises(Exception) as error:
            denied.begin()
        assert error.value.status_code == 409
    finally:
        denied.close()
