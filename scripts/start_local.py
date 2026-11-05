"""Guarded, repeatable local deployment; no production paths or credentials."""

import json
import socket
import subprocess

from check_local_stack import COMPOSE, PROJECT, resolve_local, validate
from prepare_copy import TARGET


def preflight():
    validate(resolve_local())
    context = json.loads(subprocess.check_output(["docker", "context", "inspect"]))[0]
    endpoint = context["Endpoints"]["docker"]["Host"]
    if not endpoint.startswith(("npipe://", "unix://")):
        raise ValueError("Only a local Docker engine is allowed")
    ids = subprocess.check_output(
        [
            "docker",
            "ps",
            "-aq",
            "--filter",
            f"label=com.docker.compose.project={PROJECT}",
        ],
        text=True,
    ).split()
    found_proxy = False
    if ids:
        for container in json.loads(subprocess.check_output(["docker", "inspect", *ids])):
            labels = container["Config"]["Labels"]
            workdir = labels.get("com.docker.compose.project.working_dir", "")
            if workdir.replace("\\", "/").lower() != str(TARGET).replace("\\", "/").lower():
                raise ValueError("Project name already belongs to another workspace")
            found_proxy |= labels.get("com.docker.compose.service") == "proxy"
    if not found_proxy:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 38080))


if __name__ == "__main__":
    preflight()
    subprocess.run(
        COMPOSE + ["up", "-d", "--wait", "--wait-timeout", "240"],
        cwd=TARGET,
        check=True,
    )
    print("Local stack ready: http://localhost:38080")
