CREATE TABLE mfa_recovery_code (
    user_id INTEGER NOT NULL REFERENCES userr(id) ON DELETE CASCADE,
    digest VARCHAR(64) NOT NULL,
    PRIMARY KEY (user_id, digest)
);
CREATE TABLE refresh_exchange (
    jti VARCHAR(64) PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES userr(id) ON DELETE CASCADE,
    key_hash VARCHAR(64) NOT NULL,
    encrypted_pair TEXT NOT NULL,
    expires_at BIGINT NOT NULL
);
ALTER TABLE payment_intent ADD COLUMN state VARCHAR(24) NOT NULL DEFAULT 'open';
ALTER TABLE payment_intent ADD COLUMN expires_at TIMESTAMPTZ NOT NULL DEFAULT (now() + interval '15 minutes');
UPDATE payment_intent SET state='settled' WHERE payment_id IN (SELECT id FROM payment WHERE status='paid');
ALTER TABLE provider_transaction ADD COLUMN resolution VARCHAR(24) NOT NULL DEFAULT 'none';
UPDATE provider_transaction SET resolution='settled' WHERE applied_payment_id IS NOT NULL;
CREATE TABLE payment_action (
    operation_id VARCHAR(80) PRIMARY KEY,
    payment_id INTEGER NOT NULL REFERENCES payment(id) ON DELETE RESTRICT,
    actor_id INTEGER NOT NULL REFERENCES userr(id) ON DELETE RESTRICT,
    action VARCHAR(24) NOT NULL,
    reason VARCHAR(500) NOT NULL,
    transaction_id VARCHAR(150),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE local_subscription (
    reference VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES userr(id) ON DELETE CASCADE,
    plan VARCHAR(40) NOT NULL,
    amount_in_cents BIGINT NOT NULL CHECK (amount_in_cents > 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'COP',
    state VARCHAR(24) NOT NULL DEFAULT 'pending',
    expires_at TIMESTAMPTZ,
    provider_transaction_id VARCHAR(150) UNIQUE
);
ALTER TABLE chat_turn ADD COLUMN reviewed_at TIMESTAMPTZ;
ALTER TABLE chat_turn ADD COLUMN message_hash VARCHAR(64);
UPDATE chat_turn SET message_hash=encode(sha256(convert_to(message,'UTF8')),'hex');
ALTER TABLE chat_turn ALTER COLUMN message_hash SET NOT NULL;
ALTER TABLE chat_turn ADD COLUMN review_note VARCHAR(500);
ALTER TABLE chat_turn ADD COLUMN content_expires_at TIMESTAMPTZ NOT NULL DEFAULT (now() + interval '30 days');
CREATE INDEX ix_chat_retention ON chat_turn(content_expires_at) WHERE state = 'completed';
CREATE TABLE mail_review (
    operation_id VARCHAR(80) PRIMARY KEY,
    event_id VARCHAR(64) NOT NULL REFERENCES mail_event(id) ON DELETE CASCADE,
    actor_id INTEGER NOT NULL REFERENCES userr(id) ON DELETE RESTRICT,
    reason VARCHAR(500) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
