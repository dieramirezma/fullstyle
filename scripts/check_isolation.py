"""Validate resolved Compose offline without starting containers."""

import json
import subprocess

from prepare_copy import TARGET, write_json


def validate(config, project):
    """Reject access to original/external resources before starting services."""

    def require(condition, reason):
        if not condition:
            raise ValueError(reason)

    expected = {
        "postgres": (
            "postgres:16-alpine",
            {(35432, 5432)},
            {
                "POSTGRES_DB": "fullstyle_synthetic",
                "POSTGRES_USER": "synthetic",
                "POSTGRES_PASSWORD": "local-synthetic-only",
            },
        ),
        "redis": ("redis:7-alpine", {(36379, 6379)}, {}),
        "rabbitmq": (
            "rabbitmq:3-management",
            {(35672, 5672), (35673, 15672)},
            {"RABBITMQ_DEFAULT_USER": "synthetic", "RABBITMQ_DEFAULT_PASS": "local-synthetic-only"},
        ),
    }
    require(config.get("name") == project, "Unexpected project")
    require(set(config.get("services", {})) == set(expected), "Unexpected services")
    require(not config.get("secrets") and not config.get("configs"), "External configuration")
    require(set(config.get("networks", {})) == {"sandbox"}, "Unexpected network")
    network = config["networks"]["sandbox"]
    require(network.get("internal") is True and not network.get("external"), "Network not isolated")
    require(network.get("name") == project + "_sandbox", "Network name not scoped")
    require(not network.get("driver_opts"), "Network driver options forbidden")
    volumes = config.get("volumes", {})
    require(
        set(volumes) == {"postgres_synthetic", "redis_synthetic", "rabbitmq_synthetic"},
        "Unexpected volumes",
    )
    for key, volume in volumes.items():
        require(
            not volume.get("external") and not volume.get("driver_opts"), "External/host volume"
        )
        require(volume.get("name") == project + "_" + key, "Volume name not scoped")
    for name, service in config["services"].items():
        require(
            set(service)
            <= {
                "image",
                "environment",
                "ports",
                "volumes",
                "networks",
                "healthcheck",
                "restart",
                "labels",
                "command",
                "entrypoint",
            },
            "Unexpected service option",
        )
        require(
            service.get("command") is None and service.get("entrypoint") is None,
            "Command override forbidden",
        )
        image, ports, environment = expected[name]
        require(service.get("image") == image, "Unexpected image")
        require(service.get("environment", {}) == environment, "Non-synthetic environment")
        require(set(service.get("networks", {})) == {"sandbox"}, "Service not isolated")
        require(
            all(
                p.get("host_ip") == "127.0.0.1" and p.get("protocol", "tcp") == "tcp"
                for p in service["ports"]
            ),
            "Public port",
        )
        require(
            {(int(p["published"]), int(p["target"])) for p in service["ports"]} == ports,
            "Unexpected ports",
        )
        mounts = service.get("volumes", [])
        require(all(v.get("type") == "volume" for v in mounts), "Host mount forbidden")
        expected_mounts = {
            "postgres": {("postgres_synthetic", "/var/lib/postgresql/data")},
            "redis": {("redis_synthetic", "/data")},
            "rabbitmq": {("rabbitmq_synthetic", "/var/lib/rabbitmq")},
        }
        require(
            {(v["source"], v["target"]) for v in mounts} == expected_mounts[name],
            "Unexpected mount",
        )


def resolve():
    result = subprocess.run(
        [
            "docker",
            "compose",
            "--project-directory",
            str(TARGET),
            "-f",
            str(TARGET / "compose.yaml"),
            "config",
            "--format",
            "json",
        ],
        cwd=TARGET,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    config = json.loads(result.stdout)
    config["services"] = {
        k: v for k, v in config["services"].items() if k in {"postgres", "redis", "rabbitmq"}
    }
    config["networks"] = {"sandbox": config["networks"]["sandbox"]}
    return config


if __name__ == "__main__":
    validate(resolve(), "fullstyle-portfolio")
    write_json(
        "isolation-verification.json",
        {
            "compose_valid": True,
            "static_isolation_checks_passed": True,
            "runtime_verified": False,
            "reason": "Static validation only; runtime evidence is separate.",
        },
    )
    print("PASS: resolved Compose restricted to isolated synthetic dependencies.")
