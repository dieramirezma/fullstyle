"""Isolation failures must be caught before running application containers."""

import copy
import unittest

from check_local_stack import resolve_local, validate


class LocalStackIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = resolve_local()

    def test_valid_stack(self):
        validate(self.config)

    def test_reject_external_connections_and_privileges(self):
        for name, mutate in (
            (
                "real DB",
                lambda c: c["services"]["backend"]["environment"].update(
                    DATABASE_URL="postgresql://original/data"
                ),
            ),
            (
                "provider key",
                lambda c: c["services"]["frontend"]["environment"].update(
                    RESEND_API_KEY="do-not-use"
                ),
            ),
            (
                "egress",
                lambda c: c["services"]["chatbot"]["networks"].update(ingress=None),
            ),
            (
                "host mount",
                lambda c: c["services"]["backend"].update(
                    volumes=[
                        {
                            "type": "bind",
                            "source": "D:/dev/FullStyle-Local-Orchestration",
                            "target": "/app",
                        }
                    ]
                ),
            ),
            ("privileged", lambda c: c["services"]["auth"].update(privileged=True)),
            (
                "public port",
                lambda c: c["services"]["proxy"]["ports"][0].update(host_ip="0.0.0.0"),
            ),
            (
                "foreign build",
                lambda c: c["services"]["email"]["build"].update(
                    context="D:/dev/FullStyle-Local-Orchestration"
                ),
            ),
            (
                "external network",
                lambda c: c["networks"]["ingress"].update(external=True),
            ),
            (
                "extra database",
                lambda c: c["services"].update(other={"image": "postgres"}),
            ),
        ):
            with self.subTest(name=name):
                candidate = copy.deepcopy(self.config)
                mutate(candidate)
                with self.assertRaises(ValueError):
                    validate(candidate)
