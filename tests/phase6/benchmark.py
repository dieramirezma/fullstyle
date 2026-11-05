"""Compare extracted real schedule functions in separate schemas, never original DBs."""

import json
import os
import statistics
import time
from datetime import date
from pathlib import Path
from uuid import uuid4

from config.db_config import db
from config.server_config import create_app
from migrate_local import EXPECTED, MIGRATIONS, upgrade
from models.worker_model import WorkerModel
from sqlalchemy import event, text
from utils import helpers


def percentile(values, quantile):
    return sorted(values)[max(0, int(len(values) * quantile + 0.999) - 1)]


def seed(connection):
    connection.execute(
        text("""
        INSERT INTO userr(id,name,email,active,auth_provider) VALUES (1,'Synthetic','bench@synthetic.invalid',true,'credentials');
        INSERT INTO manager(id,bankaccount,accounttype,bankentity,subscriptionactive)
            VALUES (1,1,'synthetic','synthetic',false);
        INSERT INTO site(id,name,address,manager_id) VALUES (1,'Synthetic','Synthetic',1);
        INSERT INTO category(id,name) VALUES (1,'Synthetic');
        INSERT INTO service(id,name,category_id) VALUES (1,'Synthetic',1);
        INSERT INTO detail(site_id,service_id,price,duration,active) VALUES (1,1,1000,30,true);
        INSERT INTO worker(id,name,site_id,active) SELECT n,'Synthetic',1,true FROM generate_series(1,500) n;
        INSERT INTO availability(id,worker_id,weekday,starttime,endtime)
            VALUES (1,251,'Tuesday','00:00','23:59');
        INSERT INTO appointment(id,appointmenttime,status,worker_id,site_id,service_id,client_id)
            SELECT n, timestamp '2030-01-01' + ((n-1)/500/20)*interval '1 day'
                + (((n-1)/500)%20)*interval '30 minutes',
                'pending', ((n-1)%500)+1,1,1,1 FROM generate_series(1,100000) n;
        INSERT INTO booking_terms(appointment_id,duration,amount,currency)
            SELECT id,30,1000,'COP' FROM appointment;
        ANALYZE appointment; ANALYZE booking_terms; ANALYZE detail; ANALYZE worker;
    """)
    )


def measure(app, function):
    with app.app_context():
        worker = db.session.get(WorkerModel, 251)
        statements = []

        def record(conn, cursor, statement, parameters, context, executemany):
            statements.append((statement, parameters))

        event.listen(db.engine, "before_cursor_execute", record)
        try:
            for _ in range(3):
                function(worker, date(2030, 1, 1))
            times, counts = [], []
            for _ in range(20):
                statements.clear()
                started = time.perf_counter()
                result = function(worker, date(2030, 1, 1))
                times.append((time.perf_counter() - started) * 1000)
                counts.append(len(statements))
            queries = list(statements)
        finally:
            event.remove(db.engine, "before_cursor_execute", record)
        assert len(result["occupied"]) == 20
        plans = []
        for statement, parameters in queries:
            if "FROM appointment" in statement:
                plans.append(
                    db.session.connection()
                    .exec_driver_sql(
                        "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + statement,
                        parameters,
                    )
                    .scalar_one()
                )
        return {
            "samples": len(times),
            "latency_ms": times,
            "p50_ms": statistics.median(times),
            "p95_ms": percentile(times, 0.95),
            "queries_per_request": sorted(set(counts)),
            "plans": plans,
            "body": result,
        }


def main():
    if os.getenv("DATABASE_URL") != EXPECTED or os.getenv("LOCAL_RUNTIME") != "true":
        raise RuntimeError("Only synthetic DB is allowed")
    admin_app = create_app()
    functions = {}
    for variant in ("original", "phase5"):
        namespace = dict(vars(helpers))
        exec(
            compile(
                Path("/comparison/" + variant + ".py").read_text(), variant, "exec"
            ),
            namespace,
        )
        functions[variant] = namespace["compute_daily_schedule"]
    functions["phase6"] = helpers.compute_daily_schedule
    budgets = json.loads(Path("/tests/local-budgets.json").read_text())["schedule"]
    results = {}
    schemas = []
    applications = []
    cleanup = False
    try:
        for variant, function in functions.items():
            schema = "phase6_" + uuid4().hex
            schemas.append(schema)
            with admin_app.app_context(), db.engine.begin() as connection:
                connection.execute(text("CREATE SCHEMA " + schema))
                connection.execute(text('SET LOCAL search_path TO "' + schema + '"'))
                if variant == "phase6":
                    # Commit schema creation before the migration connection sees it.
                    pass
                else:
                    connection.exec_driver_sql(
                        (MIGRATIONS / "0001_phase5.sql").read_text()
                    )
            app = create_app(
                {
                    "SQLALCHEMY_ENGINE_OPTIONS": {
                        "connect_args": {"options": "-csearch_path=" + schema},
                    }
                }
            )
            applications.append(app)
            with app.app_context():
                if variant == "phase6":
                    upgrade(db.engine, schema)
                with db.engine.begin() as connection:
                    seed(connection)
            results[variant] = measure(app, function)
            # Restore the historical optimizer's cancelled rows/current terms differences.
            if variant == "phase6":
                with app.app_context():
                    db.session.execute(text("UPDATE detail SET duration=90"))
                    db.session.execute(
                        text("UPDATE appointment SET status='cancelled' WHERE id=251")
                    )
                    db.session.commit()
                changed = measure_without_count(app, function)
                assert len(changed["occupied"]) == 19
                assert changed["occupied"][0]["end"] == "01:00:00"
        assert (
            results["original"]["body"]
            == results["phase5"]["body"]
            == results["phase6"]["body"]
        )
        assert results["phase6"]["queries_per_request"] == [
            budgets["max_queries_per_request"]
        ]
        assert results["phase6"]["p95_ms"] <= budgets["max_p95_ms"], results["phase6"][
            "p95_ms"
        ]
        assert results["phase6"]["p95_ms"] < results["phase5"]["p95_ms"]
    finally:
        for app in applications:
            with app.app_context():
                db.session.remove()
                db.engine.dispose()
        with admin_app.app_context(), db.engine.begin() as connection:
            for schema in schemas:
                connection.execute(text("DROP SCHEMA " + schema + " CASCADE"))
        cleanup = True
    print(
        json.dumps(
            {
                "passed": True,
                "rows_per_variant": 100000,
                "results": results,
                "schemas": schemas,
                "cleanup_complete": cleanup,
                "providers_contacted": False,
                "budgets": budgets,
                "conditions": "same PostgreSQL 16, 3 warmups, 20 sequential samples, no Redis/provider",
            }
        )
    )


def measure_without_count(app, function):
    with app.app_context():
        return function(db.session.get(WorkerModel, 251), date(2030, 1, 1))


if __name__ == "__main__":
    main()
