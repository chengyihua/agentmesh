import sys
import unittest

sys.path.insert(0, "src")

from agentmesh.api.server import create_server


class TestServerSecurityConfig(unittest.TestCase):
    def test_production_requires_api_key(self):
        with self.assertRaisesRegex(ValueError, "requires --api-key"):
            create_server(production=True, auth_secret="strong-auth-secret")

    def test_production_requires_non_default_auth_secret(self):
        with self.assertRaisesRegex(ValueError, "non-default --auth-secret"):
            create_server(production=True, api_key="strong-api-key")

    def test_production_allows_strong_config(self):
        server = create_server(
            production=True,
            api_key="strong-api-key",
            auth_secret="strong-auth-secret",
        )
        self.assertIsNotNone(server.app)
