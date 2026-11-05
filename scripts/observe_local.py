"""Read local structured logs and SQL queue age without collecting message payloads."""

import json
import math
import subprocess
from collections import Counter
from datetime import datetime, timezone

from check_local_stack import PROJECT, resolve_local, validate
from prepare_copy import TARGET, write_json


def main():
    validate(resolve_local())
    observations = {}
    for service in ("backend", "chatbot", "email", "email-worker"):
        result = subprocess.run(
            ["docker", "logs", "--since", "30m", PROJECT + "-" + service + "-1"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
        records = []
        for line in (result.stdout + result.stderr).splitlines():
            start = line.find('{"component":')
            if start < 0:
                continue
            try:
                records.append(json.loads(line[start:]))
            except ValueError:
                continue
        latencies = sorted(float(row["latency_ms"]) for row in records if "latency_ms" in row)
        observations[service] = {
            "samples": len(records),
            "statuses": dict(Counter(str(row["status"]) for row in records if "status" in row)),
            "errors_5xx": sum(int(row.get("status", 0)) >= 500 for row in records),
            "conflicts_409": sum(row.get("status") == 409 for row in records),
            "outcomes": dict(Counter(row["outcome"] for row in records if "outcome" in row)),
            "latency_p95_ms": latencies[math.ceil(0.95 * len(latencies)) - 1]
            if latencies
            else None,
            "latency_max_ms": max(latencies) if latencies else None,
        }
    code = """
import json,os,psycopg2
assert os.environ['LOCAL_RUNTIME']=='true'
assert os.environ['DATABASE_URL']=='postgresql://synthetic:local-synthetic-only@postgres/fullstyle_synthetic'
c=psycopg2.connect(os.environ['DATABASE_URL'],connect_timeout=3,options='-c statement_timeout=5000')
with c,c.cursor() as q:
 q.execute("SELECT state,count(*),max(attempts),coalesce(max(extract(epoch from now()-created_at)),0) FROM mail_event GROUP BY state")
 print(json.dumps([dict(state=r[0],count=r[1],max_attempts=r[2],oldest_age_seconds=float(r[3])) for r in q.fetchall()]))
c.close()
"""
    queue = json.loads(
        subprocess.check_output(
            ["docker", "exec", PROJECT + "-backend-1", "python", "-c", code],
            text=True,
        )
    )
    budgets = json.loads((TARGET / "tests/phase6/local-budgets.json").read_text(encoding="utf-8"))[
        "mail"
    ]
    pending_age = max(
        (row["oldest_age_seconds"] for row in queue if row["state"] == "pending"), default=0
    )
    mail_alert = (
        "critical"
        if pending_age >= budgets["pending_critical_age_seconds"]
        else "warning"
        if pending_age >= budgets["pending_warning_age_seconds"]
        else "ok"
    )
    write_json(
        "phase-3-observability.json",
        {
            "checked_utc": datetime.now(timezone.utc).isoformat(),
            "passed": True,
            "window": "last 30 minutes of this local stack",
            "services": observations,
            "mail_by_state": queue,
            "pending_mail_age_seconds": pending_age,
            "pending_mail_alert": mail_alert,
            "local_mail_budgets": budgets,
            "payloads_collected": False,
            "limit": "synthetic checks and health probes; not a production SLO or before/after benchmark",
        },
    )
    print("PASS: local latency, errors, conflicts, delivery outcomes and SQL message age recorded")


if __name__ == "__main__":
    main()
