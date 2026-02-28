import sys
import unittest

from fastapi.testclient import TestClient

sys.path.insert(0, "src")

from agentmesh.api.server import create_server


class TestRateLimiting(unittest.TestCase):
    def test_register_endpoint_rate_limit(self):
        app = create_server(debug=False).app

        with TestClient(app) as client:
            status_codes = []
            for i in range(70):
                payload = {
                    "id": f"limit-test-{i}",
                    "name": "LimitBot",
                    "version": "1.0.0",
                    "description": "rate limit test",
                    "skills": [{"name": f"skill-{i}", "description": "test"}],
                    "endpoint": f"http://localhost:90{i % 10}/agent",
                    "protocol": "http",
                    "health_status": "healthy",
                }
                response = client.post("/api/v1/agents/register", json=payload)
                status_codes.append(response.status_code)

            self.assertGreater(status_codes.count(201), 0)
            self.assertGreater(status_codes.count(429), 0)
