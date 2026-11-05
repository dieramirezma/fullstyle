"""Validate the complete local stack without touching original or external data."""

import copy
import json
import re
import subprocess
from pathlib import Path

from check_isolation import validate as validate_dependencies
from prepare_copy import TARGET

PROJECT = "fullstyle-portfolio"
COMPOSE = [
    "docker",
    "compose",
    "--project-directory",
    str(TARGET),
    "-p",
    PROJECT,
    "-f",
    str(TARGET / "compose.yaml"),
]
APPS = {
    "db-init",
    "backend",
    "auth",
    "chatbot",
    "email",
    "email-worker",
    "gateway",
    "frontend",
    "firebase",
    "proxy",
}


def resolve_local():
    return json.loads(subprocess.check_output(COMPOSE + ["config", "--format", "json"], cwd=TARGET))


def validate(config, project=PROJECT, source_root=TARGET):
    def require(condition, reason):
        if not condition:
            raise ValueError(reason)

    suffix = project.removeprefix(PROJECT + "-clean-")
    clean = bool(re.fullmatch(re.escape(PROJECT) + r"-clean-[a-f0-9]{8}", project))
    require(project == PROJECT or clean, "Unexpected project")
    expected_source = TARGET / ".quality" / ("clean-source-" + suffix) if clean else TARGET
    require(source_root.resolve() == expected_source.resolve(), "Unexpected source snapshot")
    tag = "phase3-clean-" + suffix if clean else "phase3"
    dependencies = copy.deepcopy(config)
    dependencies["services"] = {k: v for k, v in config["services"].items() if k not in APPS}
    dependencies["networks"] = {"sandbox": config["networks"]["sandbox"]}
    validate_dependencies(dependencies, project)
    require(
        set(config["services"]) == APPS | {"postgres", "redis", "rabbitmq"},
        "Unexpected service",
    )
    require(set(config["networks"]) == {"sandbox", "ingress"}, "Unexpected networks")
    ingress = config["networks"]["ingress"]
    require(
        ingress.get("name") == project + "_ingress"
        and not ingress.get("external")
        and not ingress.get("driver_opts"),
        "External ingress",
    )
    contract = json.loads((TARGET / "docker/local-contract.json").read_text(encoding="utf-8"))
    if clean:
        contract["environment"]["backend"]["APP_WEB_URL"] = "http://localhost:38081/"
        contract["environment"]["db-init"]["APP_WEB_URL"] = "http://localhost:38081/"
        contract["environment"]["frontend"]["NEXTAUTH_URL"] = "http://localhost:38081"
    for name in APPS:
        service = config["services"][name]
        require(
            set(service)
            <= {
                "image",
                "build",
                "environment",
                "networks",
                "read_only",
                "tmpfs",
                "security_opt",
                "depends_on",
                "command",
                "entrypoint",
                "healthcheck",
                "working_dir",
                "ports",
            },
            "Unexpected service option: " + name,
        )
        image_name = {"db-init": "backend", "email-worker": "email"}.get(name, name)
        require(service["image"] == f"{PROJECT}-{image_name}:{tag}", "Unexpected app image")
        require(
            service.get("environment", {}) == contract["environment"][name],
            "Non-synthetic environment: " + name,
        )
        require(service.get("entrypoint") is None, "Entrypoint override forbidden")
        require(service.get("command") == contract["commands"][name], "Unexpected command")
        expected_networks = {"sandbox", "ingress"} if name == "proxy" else {"sandbox"}
        require(
            set(service["networks"]) == expected_networks,
            "Application egress forbidden: " + name,
        )
        build = service["build"]
        require(set(build) <= {"context", "dockerfile"}, "Build overrides forbidden")
        require(Path(build["context"]).resolve() == source_root.resolve(), "Build outside copy")
        dockerfile = (source_root / build["dockerfile"]).resolve()
        require(
            dockerfile.parent == (source_root / "docker").resolve()
            and dockerfile.suffix == ".Dockerfile",
            "Unexpected Dockerfile",
        )
        if name != "proxy":
            require(
                service.get("read_only") is True and service.get("tmpfs") == ["/tmp"],
                "Mutable root/host mount",
            )
            require(not service.get("ports"), "Application ports forbidden")
            require(
                service.get("security_opt") == ["no-new-privileges:true"],
                "Privilege escalation",
            )
        else:
            ports = service["ports"]
            require(
                len(ports) == 1
                and ports[0].get("host_ip") == "127.0.0.1"
                and int(ports[0]["published"]) == (38081 if clean else 38080)
                and ports[0]["target"] == 80,
                "Public ingress forbidden",
            )
        require(service.get("working_dir") in (None, "/tmp"), "Unexpected work directory")


if __name__ == "__main__":
    validate(resolve_local())
    print("PASS: complete stack restricted to the independent synthetic environment")
