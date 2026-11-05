"""Lifecycle consequences on real SQL; no commercial provider is contacted."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from flask_jwt_extended import create_access_token
from sqlalchemy import text

from config.db_config import db
from models.completion_model import PaymentAction
from models.consistency_model import PaymentIntent, ProviderTransaction


def auth(token):
    return {"Authorization": "Bearer " + token}


@pytest.fixture
def finance(app, client, token, setup_user):
    with app.app_context():
        db.session.execute(
            text(
                "INSERT INTO userr(id,email,name,password,active,auth_provider) VALUES(20,'owner@synthetic.invalid','owner','unused',true,'credentials'),(21,'foreign@synthetic.invalid','foreign','unused',true,'credentials')"
            )
        )
        db.session.execute(
            text(
                "INSERT INTO manager(id,bankaccount,accounttype,bankentity,subscriptionactive) VALUES(20,1,'test','test',false)"
            )
        )
        db.session.execute(
            text("INSERT INTO site(id,name,address,manager_id) VALUES(1,'test','test',20)")
        )
        db.session.execute(
            text("INSERT INTO worker(id,name,site_id,active) VALUES(1,'test',1,true)")
        )
        db.session.execute(text("INSERT INTO category(id,name) VALUES(1,'test')"))
        db.session.execute(text("INSERT INTO service(id,name,category_id) VALUES(1,'test',1)"))
        db.session.execute(
            text(
                "INSERT INTO detail(site_id,service_id,price,duration,active) VALUES(1,1,100,30,true)"
            )
        )
        db.session.execute(
            text(
                "INSERT INTO appointment(id,appointmenttime,status,worker_id,site_id,service_id,client_id) SELECT 1,'2027-01-04 10:00:00','pending',1,1,1,id FROM userr WHERE email=:email"
            ),
            {"email": setup_user["email"]},
        )
        db.session.commit()
        owner = create_access_token(identity="20")
        foreign = create_access_token(identity="21")
    created = client.post(
        "/api/payment",
        headers=auth(token),
        json={"appointment_id": 1, "amount": 100, "paymentmethod": "wompi"},
    )
    assert created.status_code == 201, created.json
    return {
        "token": token,
        "owner": owner,
        "foreign": foreign,
        "reference": created.json["reference"],
    }


def approve(client, data, operation="approve"):
    return client.post(
        "/api/local/payments/simulate",
        headers=auth(data["token"]),
        json={"reference": data["reference"], "operation_id": operation},
    )


def test_cancel_late_approval_and_refund_are_audited_without_reviving_booking(app, client, finance):
    ref = finance["reference"]
    assert (
        client.delete("/api/payment/intents/" + ref, headers=auth(finance["foreign"])).status_code
        == 404
    )
    assert (
        client.delete("/api/payment/intents/" + ref, headers=auth(finance["token"])).status_code
        == 200
    )
    event = approve(client, finance)
    assert event.status_code == 202 and event.json["reconciliation_required"]
    assert not event.json["payment_applied"]
    assert approve(client, finance).json["duplicate"]
    assert (
        client.get("/api/appointment?id=1", headers=auth(finance["token"])).json[0]["status"]
        == "cancelled"
    )
    path = "/api/payment/refunds/" + event.json["transaction_id"]
    body = {"operation_id": "refund-1", "reason": "Local late approval"}
    assert client.post(path, headers=auth(finance["token"]), json=body).status_code == 403
    assert client.post(path, headers=auth(finance["owner"]), json=body).json["duplicate"] is False
    assert client.post(path, headers=auth(finance["owner"]), json=body).json["duplicate"] is True
    assert (
        client.get(
            "/api/payment/reconciliation?site_id=1", headers=auth(finance["foreign"])
        ).status_code
        == 403
    )
    assert (
        client.get("/api/payment/reconciliation?site_id=1", headers=auth(finance["owner"])).json[
            "transactions"
        ][0]["resolution"]
        == "refunded"
    )
    with app.app_context():
        assert PaymentAction.query.count() == 1
        assert ProviderTransaction.query.one().applied_payment_id is None


def test_expired_intent_releases_schedule_and_settled_refund_is_idempotent(app, client, finance):
    with app.app_context():
        db.session.execute(text("UPDATE payment_intent SET expires_at=now()-interval '1 minute'"))
        db.session.commit()
    result = client.get(
        "/api/payment/intents/" + finance["reference"], headers=auth(finance["token"])
    )
    assert result.status_code == 200 and result.json["state"] == "expired"
    assert approve(client, finance).json["reconciliation_required"]
    with app.app_context():
        assert (
            db.session.execute(text("SELECT status FROM appointment WHERE id=1")).scalar_one()
            == "cancelled"
        )


def test_two_refunds_only_one_effect_and_no_unauthorized_settlement(app, client, finance):
    event = approve(client, finance)
    assert event.status_code == 202 and event.json["payment_applied"]
    path = "/api/payment/refunds/" + event.json["transaction_id"]
    barrier = Barrier(2)

    def attempt(index):
        with app.test_client() as peer:
            barrier.wait(timeout=10)
            response = peer.post(
                path,
                headers=auth(finance["owner"]),
                json={"operation_id": f"refund-{index}", "reason": "Synthetic refund"},
            )
            assert response.status_code == 200, response.json
            return response.json["duplicate"]

    with ThreadPoolExecutor(2) as pool:
        assert sorted(pool.map(attempt, range(2))) == [False, True]
    with app.app_context():
        assert PaymentAction.query.count() == 1
        assert db.session.execute(text("SELECT status FROM payment")).scalar_one() == "refunded"
        assert (
            db.session.execute(text("SELECT status FROM appointment")).scalar_one() == "cancelled"
        )


def test_synthetic_subscription_price_and_activation_come_from_server(app, client, finance):
    assert (
        client.post(
            "/api/subscriptions", headers=auth(finance["token"]), json={"plan": "synthetic-30-days"}
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/subscriptions",
            headers=auth(finance["owner"]),
            json={"plan": "synthetic-30-days", "amount_in_cents": 1},
        ).status_code
        == 400
    )
    result = client.post(
        "/api/subscriptions", headers=auth(finance["owner"]), json={"plan": "synthetic-30-days"}
    )
    assert result.status_code == 201 and result.json["synthetic"]
    data = {"token": finance["owner"], "reference": result.json["reference"]}
    assert result.json["state"] == "pending"
    with app.app_context():
        assert not db.session.execute(
            text("SELECT subscriptionactive FROM manager WHERE id=20")
        ).scalar_one()
    assert approve(client, data).json["subscription_applied"]
    assert approve(client, data).json["duplicate"]
    with app.app_context():
        assert db.session.execute(
            text("SELECT subscriptionactive FROM manager WHERE id=20")
        ).scalar_one()
        assert ProviderTransaction.query.count() == 1
    assert (
        client.get("/api/subscriptions", headers=auth(finance["owner"])).json["subscriptions"][0][
            "state"
        ]
        == "active"
    )


def test_simulated_provider_is_fail_closed_outside_local(client, finance, monkeypatch):
    monkeypatch.setenv("LOCAL_RUNTIME", "false")
    assert approve(client, finance).status_code == 503


def test_quote_preserves_server_snapshot_and_rejects_foreign_identity(app, client, finance):
    with app.app_context():
        db.session.execute(text("UPDATE detail SET price=999"))
        db.session.commit()
    quote = client.get("/api/payment/quote/1", headers=auth(finance["token"]))
    assert quote.status_code == 200 and quote.json["amount"] == 100
    assert client.get("/api/payment/quote/1", headers=auth(finance["foreign"])).status_code == 404
    assert (
        client.post(
            "/api/payment",
            headers=auth(finance["token"]),
            json={"appointment_id": 1, "amount": 999, "paymentmethod": "wompi"},
        ).status_code
        == 400
    )


def test_cancel_racing_approval_never_resurrects_closed_booking(app, client, finance):
    barrier = Barrier(2)

    def cancel():
        with app.test_client() as peer:
            barrier.wait(timeout=10)
            return peer.delete(
                "/api/payment/intents/" + finance["reference"], headers=auth(finance["token"])
            )

    def settle():
        with app.test_client() as peer:
            barrier.wait(timeout=10)
            return approve(peer, finance)

    with ThreadPoolExecutor(2) as pool:
        cancelled = pool.submit(cancel)
        settled = pool.submit(settle)
        cancellation, approval = cancelled.result(), settled.result()
    assert approval.status_code == 202, approval.json
    with app.app_context():
        booking = db.session.execute(text("SELECT status FROM appointment WHERE id=1")).scalar_one()
        intent = PaymentIntent.query.one()
        ledger = ProviderTransaction.query.one()
        if booking == "paid":
            assert (
                cancellation.status_code == 409
                and intent.state == "settled"
                and ledger.resolution == "settled"
            )
        else:
            assert (
                booking == "cancelled"
                and cancellation.status_code == 200
                and intent.state == "cancelled"
                and ledger.resolution == "review"
            )


def test_maintenance_expires_intents_and_subscriptions_without_caller_privileges(
    app, client, finance
):
    from maintenance_local import maintain

    with app.app_context():
        db.session.execute(text("UPDATE payment_intent SET expires_at=now()-interval '1 minute'"))
        db.session.execute(
            text(
                "UPDATE manager SET subscriptionactive=true,subscriptionfinishdate=now()-interval '1 minute' WHERE id=20"
            )
        )
        db.session.commit()
        assert maintain() == 1
        assert maintain() == 0
        assert (
            db.session.execute(text("SELECT status FROM appointment WHERE id=1")).scalar_one()
            == "cancelled"
        )
        assert not db.session.execute(
            text("SELECT subscriptionactive FROM manager WHERE id=20")
        ).scalar_one()
    assert approve(client, finance).json["reconciliation_required"]
