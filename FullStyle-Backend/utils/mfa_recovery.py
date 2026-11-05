"""High entropy offline codes; only digests persist, recovery revokes every session."""

import hashlib
import secrets
import time

from config.db_config import db
from models.completion_model import RecoveryCode
from utils.account_security import bump_epoch


def code_digest(code):
    return hashlib.sha256(str(code).strip().replace("-", "").lower().encode()).hexdigest()


def issue_codes(user_id):
    RecoveryCode.query.filter_by(user_id=user_id).delete()
    codes = [secrets.token_hex(16) for _ in range(10)]
    db.session.add_all(RecoveryCode(user_id=user_id, digest=code_digest(c)) for c in codes)
    return codes


def consume_code(state, code):
    now = int(time.time())
    if state.locked_until > now:
        return False
    row = db.session.get(RecoveryCode, (state.user_id, code_digest(code)))
    if row is None:
        state.failures += 1
        if state.failures >= 5:
            state.failures = 0
            state.locked_until = now + 300
        return False
    # Policy row is locked by the caller, so two requests cannot consume a code.
    RecoveryCode.query.filter_by(user_id=state.user_id).delete()
    state.enabled = False
    state.secret = None
    state.pending_until = 0
    state.last_step = -1
    state.failures = 0
    state.locked_until = 0
    bump_epoch(state)
    return True
