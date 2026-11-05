"""Reliability fault tests on a separate internal network and disposable databases."""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from uuid import uuid4

from check_local_stack import resolve_local, validate
from prepare_copy import DOCS, TARGET, evidence_name, write_json
from quality import fingerprint, source_hashes
from start_local import preflight


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--mutation", choices=["mail-atomic"])
    mutation = parser.parse_args().mutation
    preflight()
    config = resolve_local()
    validate(config)
    before = source_hashes()
    suffix = uuid4().hex[:12]
    project = "fullstyle-portfolio-phase5-" + suffix
    network = project + "_sandbox"
    volumes = {"postgres": project + "_pgdata"}
    schema = "phase5_" + suffix
    names = {
        name: project + "-" + name
        for name in (
            "postgres",
            "redis",
            "rabbitmq",
            "backend",
            "chat-a",
            "chat-b",
            "worker",
            "runner",
        )
    }
    report_name = evidence_name("phase-3-") + (
        "mutation-" + mutation if mutation else "reliability"
    )
    log = (DOCS / (report_name + ".log")).open("w", encoding="utf-8")
    completed = []
    passed = False
    cleanup = False
    environment = dict(
        config["services"]["backend"]["environment"],
        RELIABILITY_SCHEMA=schema,
        PYTHONPATH="/app:/tests",
    )

    def run(args, timeout=120, check=True):
        result = subprocess.run(
            args,
            cwd=TARGET,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        log.write(
            "\n".join(
                line
                for line in (result.stdout + result.stderr).splitlines()
                if not line.startswith('{"tokens"')
            )
            + "\n"
        )
        log.flush()
        if check and result.returncode:
            raise RuntimeError(
                "Reliability command failed: "
                + " ".join(args[:5])
                + " (see "
                + report_name
                + ".log)"
            )
        return result

    def docker_args(name, image, env=None, detached=False, alias=None):
        args = [
            "docker",
            "run",
            "-d" if detached else "--rm",
            "--name",
            names[name],
            "--network",
            network,
            "--read-only",
            "--tmpfs",
            "/tmp",
            "--label",
            "fullstyle.phase5=" + suffix,
        ]
        if alias:
            args += ["--network-alias", alias]
        for key, value in (env or {}).items():
            args += ["-e", f"{key}={value}"]
        args += [
            "--mount",
            f"type=bind,source={TARGET / 'tests/phase5'},target=/tests,readonly",
            image,
        ]
        return args

    def ready(name, port, path="/health", attempts=60):
        code = f"import urllib.request;urllib.request.urlopen('http://127.0.0.1:{port}{path}',timeout=2)"
        for _ in range(attempts):
            result = run(
                ["docker", "exec", names[name], "python", "-c", code], timeout=5, check=False
            )
            if result.returncode == 0:
                return
            time.sleep(0.5)
        raise RuntimeError("Replica did not become ready: " + name)

    tokens = None

    def network_check(mode):
        env = dict(
            environment,
            PHASE5_TOKENS=json.dumps(tokens),
            CHAT_A=names["chat-a"],
            CHAT_B=names["chat-b"],
            TEST_BACKEND=names["backend"],
        )
        result = run(
            docker_args("runner", "fullstyle-portfolio-backend:phase3", env)
            + ["python", "/tests/check_network.py", mode],
            timeout=90,
        )
        print(result.stdout.strip(), flush=True)
        completed.append(mode)

    try:
        run(
            [
                "docker",
                "network",
                "create",
                "--internal",
                "--label",
                "fullstyle.phase5=" + suffix,
                network,
            ]
        )
        info = json.loads(run(["docker", "network", "inspect", network]).stdout)[0]
        assert info["Internal"] and info["Labels"]["fullstyle.phase5"] == suffix
        for volume in volumes.values():
            run(["docker", "volume", "create", "--label", "fullstyle.phase5=" + suffix, volume])
        run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                names["postgres"],
                "--network",
                network,
                "--network-alias",
                "postgres",
                "--label",
                "fullstyle.phase5=" + suffix,
                "--mount",
                f"type=volume,source={volumes['postgres']},target=/var/lib/postgresql/data",
                "-e",
                "POSTGRES_USER=synthetic",
                "-e",
                "POSTGRES_PASSWORD=local-synthetic-only",
                "-e",
                "POSTGRES_DB=fullstyle_synthetic",
                "postgres:16-alpine",
            ]
        )
        run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                names["redis"],
                "--network",
                network,
                "--network-alias",
                "redis",
                "--label",
                "fullstyle.phase5=" + suffix,
                "redis:7-alpine",
            ]
        )
        run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                names["rabbitmq"],
                "--network",
                network,
                "--network-alias",
                "rabbitmq",
                "--tmpfs",
                "/var/lib/rabbitmq",
                "--label",
                "fullstyle.phase5=" + suffix,
                "-e",
                "RABBITMQ_DEFAULT_USER=synthetic",
                "-e",
                "RABBITMQ_DEFAULT_PASS=local-synthetic-only",
                "-e",
                "RABBITMQ_ERLANG_COOKIE=synthetic-phase5-cookie",
                "rabbitmq:3-management",
            ]
        )
        for _ in range(60):
            pg = run(
                [
                    "docker",
                    "exec",
                    names["postgres"],
                    "pg_isready",
                    "-U",
                    "synthetic",
                    "-d",
                    "fullstyle_synthetic",
                ],
                check=False,
            )
            mq = run(
                [
                    "docker",
                    "exec",
                    "--user",
                    "rabbitmq",
                    names["rabbitmq"],
                    "rabbitmq-diagnostics",
                    "-q",
                    "--timeout",
                    "3",
                    "check_running",
                ],
                check=False,
            )
            if pg.returncode == mq.returncode == 0:
                break
            time.sleep(0.5)
        else:
            raise RuntimeError("Disposable infrastructure not ready")
        init = run(
            docker_args("runner", "fullstyle-portfolio-backend:phase3", environment)
            + ["python", "/tests/fixture.py", "init"]
        )
        tokens = json.loads(
            next(line for line in init.stdout.splitlines() if line.startswith('{"tokens"'))
        )["tokens"]
        # Never persist synthetic session tokens to reports.
        mail_env = dict(
            environment,
            DELIVERY_MODE="local",
            RABBITMQ_URL="amqp://synthetic:local-synthetic-only@rabbitmq:5672/%2F",
            MAIL_QUEUE="phase5_mail",
            MAIL_DEAD_QUEUE="phase5_dead",
            PYTHONPATH="/app:/tests",
        )
        if mutation:
            mail_env["PHASE5_MUTATION"] = mutation
            result = run(
                docker_args("runner", "fullstyle-portfolio-email:phase3", mail_env)
                + [
                    "python",
                    "-m",
                    "unittest",
                    "-v",
                    "test_mail.MailTests.test_02_failure_between_contact_deliveries_rolls_back_and_recovers",
                ],
                check=False,
            )
            output = result.stdout + result.stderr
            passed = (
                result.returncode == 1
                and "FAILED (failures=1)" in output
                and "ERROR:" not in output
            )
            assert passed, "Atomicity mutation was not detected by the receipt assertion"
            completed.append("mail-atomic-mutation-detected")
        else:
            result = run(
                docker_args("runner", "fullstyle-portfolio-email:phase3", mail_env)
                + [
                    "python",
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "/tests",
                    "-p",
                    "test_mail.py",
                    "-v",
                ]
            )
            print("PASS: mail integration suite", flush=True)
            completed.append("mail-integration")
            run(
                docker_args(
                    "runner",
                    "fullstyle-portfolio-chatbot:phase3",
                    dict(environment, PYTHONPATH="/app:/tests"),
                )
                + [
                    "python",
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "/tests",
                    "-p",
                    "test_http_retry.py",
                    "-v",
                ]
            )
            print("PASS: bounded HTTP retries over TCP", flush=True)
            completed.append("http-retries")
            run(
                docker_args(
                    "backend",
                    "fullstyle-portfolio-backend:phase3",
                    environment,
                    True,
                    "backend",
                )
                + ["python", "/tests/fixture.py", "serve"]
            )
            ready("backend", 5000)
            chat_env = dict(environment, CHAT_MODE="local", API_BASE_URL="http://backend:5000")
            for name in ("chat-a", "chat-b"):
                run(
                    docker_args(name, "fullstyle-portfolio-chatbot:phase3", chat_env, True)
                    + ["python", "/tests/chat_replica.py"]
                )
                ready(name, 8080)
            network_check("replicas")
            run(["docker", "restart", names["chat-a"]])
            ready("chat-a", 8080)
            network_check("restart")
            # Kill an actual replica after the durable pending receipt exists.
            crash_env = dict(
                environment,
                PHASE5_TOKENS=json.dumps(tokens),
                CHAT_A=names["chat-a"],
                CHAT_B=names["chat-b"],
                TEST_BACKEND=names["backend"],
            )
            crash_name = project + "-crash-client"
            crash_args = docker_args("runner", "fullstyle-portfolio-backend:phase3", crash_env)
            crash_args[crash_args.index(names["runner"])] = crash_name
            crash = subprocess.Popen(
                crash_args + ["python", "/tests/check_network.py", "crash-start"],
                cwd=TARGET,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            network_check("wait-pending")
            run(["docker", "kill", names["chat-a"]])
            stdout, stderr = crash.communicate(timeout=30)
            log.write((stdout + stderr).decode(errors="replace"))
            assert crash.returncode == 0
            run(["docker", "start", names["chat-a"]])
            ready("chat-a", 8080)
            network_check("after-crash")
            run(["docker", "stop", names["backend"]])
            network_check("backend-down")
            run(["docker", "start", names["backend"]])
            ready("backend", 5000)
            run(["docker", "stop", names["rabbitmq"]])
            network_check("mail-pending")
            run(
                docker_args("worker", "fullstyle-portfolio-email:phase3", mail_env, True)
                + ["python", "workers/email_worker.py"]
            )
            time.sleep(2)
            run(["docker", "start", names["rabbitmq"]])
            for _ in range(40):
                if (
                    run(
                        [
                            "docker",
                            "exec",
                            "--user",
                            "rabbitmq",
                            names["rabbitmq"],
                            "rabbitmq-diagnostics",
                            "-q",
                            "--timeout",
                            "3",
                            "check_running",
                        ],
                        check=False,
                    ).returncode
                    == 0
                ):
                    break
                time.sleep(0.5)
            network_check("mail-recovered")
            run(["docker", "restart", names["worker"]])
            network_check("mail-recovered")
            run(["docker", "stop", names["redis"]])
            # Redis remains optional: shared history and authoritative mail receipts survive.
            network_check("mail-recovered")
            run(["docker", "start", names["redis"]])
            run(["docker", "stop", names["postgres"]])
            network_check("sql-down")
            run(["docker", "start", names["postgres"]])
            ready("backend", 5000, "/ready")
            # Capture state/age/errors from this run's actual SQL before cleanup.
            metrics_code = "import json,psycopg2,os;c=psycopg2.connect(os.environ['DATABASE_URL'],connect_timeout=3,options='-c search_path='+os.environ['RELIABILITY_SCHEMA']);q=c.cursor();q.execute(\"SELECT state,count(*),coalesce(max(extract(epoch from now()-created_at)),0) FROM mail_event GROUP BY state\");print(json.dumps(q.fetchall(),default=str));c.close()"
            metrics = run(
                docker_args("runner", "fullstyle-portfolio-backend:phase3", environment)
                + ["python", "-c", metrics_code]
            )
            (DOCS / evidence_name("phase-3-mail-metrics.json")).write_text(
                metrics.stdout, encoding="utf-8"
            )
            passed = True
    finally:
        # This label was generated here. Never remove a shared/original project.
        ids = run(
            ["docker", "ps", "-aq", "--filter", "label=fullstyle.phase5=" + suffix], check=False
        ).stdout.split()
        for container in ids:
            info = json.loads(run(["docker", "inspect", container]).stdout)[0]
            assert info["Config"]["Labels"]["fullstyle.phase5"] == suffix
            logs = run(["docker", "logs", "--tail", "150", container], check=False)
            log.write(logs.stdout + logs.stderr)
        if ids:
            run(["docker", "rm", "-f", *ids], check=False)
        run(["docker", "network", "rm", network], check=False)
        for volume in volumes.values():
            volume_info = run(["docker", "volume", "inspect", volume], check=False)
            if volume_info.returncode == 0:
                assert json.loads(volume_info.stdout)[0]["Labels"]["fullstyle.phase5"] == suffix
                run(["docker", "volume", "rm", volume], check=False)
        cleanup = (
            not run(
                ["docker", "ps", "-aq", "--filter", "label=fullstyle.phase5=" + suffix]
            ).stdout.strip()
            and all(
                run(["docker", "volume", "inspect", volume], check=False).returncode != 0
                for volume in volumes.values()
            )
            and run(["docker", "network", "inspect", network], check=False).returncode != 0
        )
        log.close()
        stable = before == source_hashes()
        write_json(
            report_name + ".json",
            {
                "checked_utc": datetime.now(timezone.utc).isoformat(),
                "passed": passed and cleanup and stable,
                "completed_scenarios": completed,
                "cleanup_complete": cleanup,
                "source_stable": stable,
                "source_fingerprint": fingerprint(before),
                "project": project,
                "report": report_name + ".log",
                "providers_contacted": False,
                "databases": "dedicated PostgreSQL, Redis and RabbitMQ; no shared data modified",
            },
        )
    raise SystemExit(0 if passed and cleanup and stable else 1)


if __name__ == "__main__":
    main()
