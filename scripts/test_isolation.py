"""Exercise boundaries that protect original and external data."""

import copy
import unittest

from check_isolation import resolve, validate


class IsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = resolve()
        validate(cls.config, "fullstyle-portfolio")

    def test_valid_configuration(self):
        validate(self.config, "fullstyle-portfolio")

    def test_implicit_redis_volume_rejected(self):
        config = copy.deepcopy(self.config)
        config["services"]["redis"].pop("volumes")
        with self.assertRaisesRegex(ValueError, "Unexpected mount"):
            validate(config, "fullstyle-portfolio")

    def test_unsafe_mutations_rejected(self):
        mutations = [
            ("original project", lambda c: c.update(name="original")),
            ("external network", lambda c: c["networks"]["sandbox"].update(external=True)),
            ("network egress", lambda c: c["networks"]["sandbox"].update(internal=False)),
            (
                "external database",
                lambda c: c["services"]["postgres"]["environment"].update(
                    DATABASE_URL="postgresql://external.invalid/db"
                ),
            ),
            (
                "original volume",
                lambda c: c["volumes"]["postgres_synthetic"].update(name="original_database"),
            ),
            (
                "host-backed volume",
                lambda c: c["volumes"]["postgres_synthetic"].update(
                    driver_opts={"device": "D:/original"}
                ),
            ),
            ("host bind", lambda c: c["services"]["postgres"]["volumes"][0].update(type="bind")),
            (
                "public port",
                lambda c: c["services"]["postgres"]["ports"][0].update(host_ip="0.0.0.0"),
            ),
            (
                "original port",
                lambda c: c["services"]["postgres"]["ports"][0].update(published="5432"),
            ),
            ("application", lambda c: c["services"].update(backend={"image": "backend"})),
            ("host network", lambda c: c["services"]["redis"].update(network_mode="host")),
            ("entrypoint", lambda c: c["services"]["redis"].update(entrypoint=["sh"])),
        ]
        for name, mutate in mutations:
            with self.subTest(risk=name):
                config = copy.deepcopy(self.config)
                mutate(config)
                with self.assertRaises(ValueError):
                    validate(config, "fullstyle-portfolio")


if __name__ == "__main__":
    unittest.main()
