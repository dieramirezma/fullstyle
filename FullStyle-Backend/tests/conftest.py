"""Every pytest case owns a PostgreSQL schema, with no fallback or shared deletion."""

import os
from uuid import uuid4

import psycopg2
import pytest
from sqlalchemy import text
from werkzeug.security import generate_password_hash

from config.db_config import db
from config.server_config import create_app
from migrate_local import EXPECTED, upgrade


@pytest.fixture
def app():
    if os.getenv("LOCAL_RUNTIME") != "true" or os.getenv("DATABASE_URL") != EXPECTED:
        raise RuntimeError("pytest requires the exact local synthetic PostgreSQL DSN")
    schema = "phase6_" + uuid4().hex
    admin = psycopg2.connect(EXPECTED, connect_timeout=3)
    admin.autocommit = True
    with admin.cursor() as cursor:
        cursor.execute("CREATE SCHEMA " + schema)
    application = None
    try:
        application = create_app(
            {
                "TESTING": True,
                "SQLALCHEMY_ENGINE_OPTIONS": {
                    "connect_args": {"options": "-csearch_path=" + schema},
                },
            }
        )
        with application.app_context():
            upgrade(db.engine, schema)
        application.config["TEST_SCHEMA"] = schema
        yield application
    finally:
        if application:
            with application.app_context():
                db.session.remove()
                db.engine.dispose()
        with admin.cursor() as cursor:
            cursor.execute("DROP SCHEMA " + schema + " CASCADE")
        admin.close()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def setup_user(client):
    data = {"name": "LoginTest", "email": "logintest@synthetic.invalid", "password": "Password123"}
    response = client.post("/api/register", json=data)
    assert response.status_code == 200, response.json
    return data


@pytest.fixture
def token(client, setup_user):
    response = client.post("/api/login", json=setup_user)
    assert response.status_code == 200, response.json
    return response.json["access_token"]


@pytest.fixture
def catalog(app):
    with app.app_context():
        db.session.execute(text("INSERT INTO category(id,name) VALUES (1,'Synthetic')"))
        db.session.execute(
            text("INSERT INTO service(id,category_id,name) VALUES (1,1,'Synthetic')")
        )
        db.session.commit()


@pytest.fixture
def legacy_user(app):
    from models.user_model import UserModel

    with app.app_context():
        user = UserModel(
            email="legacy@synthetic.invalid",
            name="legacy",
            password=generate_password_hash("Password123", method="pbkdf2:sha256:1000"),
        )
        db.session.add(user)
        db.session.commit()
        return user.id
