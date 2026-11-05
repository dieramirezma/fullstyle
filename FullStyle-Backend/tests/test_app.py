"""Migrated legacy assertions with explicit catalog data and persistence checks."""

import pytest
from sqlalchemy import text

from config.db_config import db


def test_get_service_by_category(client, token, catalog):
    response = client.get(
        "/api/service?category_id=1", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert [(s["id"], s["category_id"]) for s in response.json] == [(1, 1)]


def test_get_categories(client, token, catalog):
    response = client.get("/api/category", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json == [{"id": 1, "name": "Synthetic"}]


@pytest.mark.parametrize("resource", ["site", "worker", "worker_has_service", "site_has_category"])
def test_empty_collections(client, token, resource):
    response = client.get("/api/" + resource, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404
    assert isinstance(response.json.get("message"), str)


@pytest.mark.parametrize(
    "resource,payload,table",
    [
        (
            "site",
            {"id": 9999, "manager_id": 9999, "name": "Foreign", "address": "Synthetic"},
            "site",
        ),
        ("worker", {"id": 9999, "site_id": 9999, "name": "Foreign"}, "worker"),
    ],
)
def test_reject_foreign_writes(client, app, token, resource, payload, table):
    response = client.post(
        "/api/" + resource, json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
    with app.app_context():
        assert db.session.execute(text("SELECT count(*) FROM " + table)).scalar_one() == 0
