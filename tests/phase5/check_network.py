"""Assertions on actual disposable replicas. Docker lifecycle stays in the host runner."""

import json
import os
import sys
import time

import psycopg2
import requests

SCHEMA = os.environ["RELIABILITY_SCHEMA"]
assert SCHEMA.startswith("phase5_") and SCHEMA.isidentifier()
MODE = sys.argv[1]
CONN = (
    None
    if MODE in {"sql-down", "backend-down"}
    else psycopg2.connect(
        os.environ["DATABASE_URL"],
        connect_timeout=3,
        options=f"-c search_path={SCHEMA} -c statement_timeout=5000",
    )
)
TOKENS = json.loads(os.environ["PHASE5_TOKENS"])
A = "http://" + os.environ["CHAT_A"] + ":8080/api/v1/chat"
B = "http://" + os.environ["CHAT_B"] + ":8080/api/v1/chat"
MODE = sys.argv[1]


def call(base, message, operation, token=TOKENS[0], expected=200):
    response = requests.post(
        base + "/send",
        json={"session_id": "shared", "message": message},
        headers={"Authorization": "Bearer " + token, "X-Operation-ID": operation},
        timeout=20,
    )
    assert response.status_code == expected, (response.status_code, response.text)
    return response.json()


def history(base, token=TOKENS[0], expected=200):
    response = requests.get(
        base + "/history/shared",
        headers={"Authorization": "Bearer " + token},
        timeout=15,
    )
    assert response.status_code == expected, (response.status_code, response.text)
    return response.json()


if MODE == "replicas":
    first = call(A, "hello phase5", "turn-1")
    second = call(B, "historial", "turn-2")
    context = json.loads(second["reply"])
    assert context == [["human", "hello phase5"], ["ai", first["reply"]]], context
    assert call(B, "hello phase5", "turn-1") == first
    assert len(history(A)["turns"]) == 2
    assert history(B)["turns"] == history(A)["turns"]
    assert history(B, TOKENS[1])["turns"] == []
    call(B, "different", "turn-1", expected=409)
    with CONN, CONN.cursor() as cur:
        cur.execute("SELECT pg_advisory_lock(hashtextextended('chat:1:shared',0))")
        call(A, "held", "turn-locked", expected=409)
        cur.execute("SELECT pg_advisory_unlock(hashtextextended('chat:1:shared',0))")
    assert len(history(A)["turns"]) == 2
elif MODE == "restart":
    assert len(history(A)["turns"]) == 2
    assert history(A)["turns"] == history(B)["turns"]
    call(A, "historial", "turn-3")
    assert len(history(B)["turns"]) == 3
elif MODE == "crash-start":
    try:
        call(A, "__phase5_slow__", "crashed-operation")
    except requests.RequestException:
        pass
    else:
        raise AssertionError(
            "Replica was expected to terminate while operation was pending"
        )
elif MODE == "wait-pending":
    for _ in range(100):
        with CONN, CONN.cursor() as cur:
            cur.execute(
                "SELECT count(*) FROM chat_turn WHERE operation_id='crashed-operation' AND state='pending'"
            )
            if cur.fetchone()[0] == 1:
                break
        time.sleep(0.1)
    else:
        raise AssertionError("Pending operation not persisted before replica kill")
elif MODE == "after-crash":
    call(A, "__phase5_slow__", "crashed-operation", expected=409)
    turns = history(B)["turns"]
    assert len(turns) == 4 and turns[-1]["reply"] is None
    call(B, "historial", "turn-after-crash")
    assert history(A)["turns"][-2]["state"] == "uncertain"
elif MODE == "backend-down":
    history(A, expected=503)
elif MODE == "mail-pending":
    # HTTP acceptance survives broker unavailability and is idempotent for this user/op.
    backend = "http://" + os.environ["TEST_BACKEND"] + ":5000/api/email/contact"
    headers = {
        "Authorization": "Bearer " + TOKENS[0],
        "X-Operation-ID": "broker-down-mail",
    }
    data = {"message": "recover after broker outage"}
    response = requests.post(backend, json=data, headers=headers, timeout=10)
    assert response.status_code == 202, response.text
    again = requests.post(backend, json=data, headers=headers, timeout=10)
    assert (
        again.status_code == 202
        and again.json()["event_id"] == response.json()["event_id"]
    )
    conflict = requests.post(
        backend, json={"message": "changed content"}, headers=headers, timeout=10
    )
    assert conflict.status_code == 409, conflict.text
    with CONN, CONN.cursor() as cur:
        cur.execute(
            "SELECT state FROM mail_event WHERE id=%s", (response.json()["event_id"],)
        )
        assert cur.fetchone()[0] == "pending"
elif MODE == "mail-recovered":
    recovery_deadline = time.monotonic() + 60
    while time.monotonic() < recovery_deadline:
        with CONN, CONN.cursor() as cur:
            cur.execute(
                "SELECT state,id FROM mail_event WHERE payload->'data'->>'message'='recover after broker outage'"
            )
            row = cur.fetchone()
            if row and row[0] == "delivered":
                cur.execute(
                    "SELECT count(*) FROM mail_delivery WHERE event_id=%s", (row[1],)
                )
                assert cur.fetchone()[0] == 2
                break
        time.sleep(0.3)
    else:
        raise AssertionError(
            "Durable mail did not recover within 60 seconds after broker/worker restart"
        )
elif MODE == "sql-down":
    # Terminate just the dedicated replicas' SQL connections by detaching their network
    # in the host runner. No shared database or volume is stopped.
    history(A, expected=503)
else:
    raise AssertionError("Unknown scenario")
if CONN is not None:
    CONN.close()
print("PASS: " + MODE)
