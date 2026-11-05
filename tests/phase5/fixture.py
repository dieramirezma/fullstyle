"""Create only this run's schema, or serve its isolated backend over real HTTP."""

import os
import sys

import psycopg2

DSN = "postgresql://synthetic:local-synthetic-only@postgres/fullstyle_synthetic"
SCHEMA = os.environ["RELIABILITY_SCHEMA"]
assert os.environ["LOCAL_RUNTIME"] == "true" and os.environ["DATABASE_URL"] == DSN
assert SCHEMA.startswith("phase5_") and SCHEMA.isidentifier()
MODE = sys.argv[1]
if MODE in {"init", "cleanup"}:
    conn = psycopg2.connect(DSN, connect_timeout=3)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(
            ("CREATE SCHEMA " if MODE == "init" else "DROP SCHEMA ")
            + SCHEMA
            + (" CASCADE" if MODE == "cleanup" else "")
        )
    conn.close()
if MODE != "cleanup":
    from config.db_config import db
    from config.server_config import create_app

    app = create_app(
        {
            "SQLALCHEMY_ENGINE_OPTIONS": {
                "pool_pre_ping": True,
                "connect_args": {
                    "connect_timeout": 3,
                    "options": f"-c search_path={SCHEMA} -c statement_timeout=5000 -c lock_timeout=2000",
                },
            }
        }
    )
    if MODE == "init":
        from flask_jwt_extended import create_access_token
        from migrate_local import upgrade
        from models.user_model import UserModel

        with app.app_context():
            upgrade(db.engine, SCHEMA)
            for user_id in (1, 2):
                user = UserModel(
                    email=f"user{user_id}@synthetic.invalid",
                    name=f"Synthetic {user_id}",
                    password=None,
                )
                user.id = user_id
                user.active = True
                db.session.add(user)
            db.session.commit()
            import json

            print(
                json.dumps(
                    {"tokens": [create_access_token(identity=str(i)) for i in (1, 2)]}
                )
            )
    elif MODE == "serve":
        app.run(host="0.0.0.0", port=5000, threaded=True)
