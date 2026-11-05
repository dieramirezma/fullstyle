CREATE TABLE account_security (
    user_id INTEGER PRIMARY KEY REFERENCES userr(id) ON DELETE CASCADE,
    epoch INTEGER NOT NULL DEFAULT 0,
    enabled BOOLEAN NOT NULL DEFAULT false,
    secret TEXT,
    pending_until BIGINT NOT NULL DEFAULT 0,
    last_step BIGINT NOT NULL DEFAULT -1,
    failures INTEGER NOT NULL DEFAULT 0,
    locked_until BIGINT NOT NULL DEFAULT 0
);
