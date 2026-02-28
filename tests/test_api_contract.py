import sys
import unittest

from fastapi.testclient import TestClient

sys.path.insert(0, "src")

from agentmesh.api.server import create_server


class TestAgentMeshAPIContract(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_server(debug=False).app
        self.client = TestClient(self.app)

    def _register_sample(self, agent_id: str = "weather-bot-001"):
        payload = {
            "id": agent_id,
            "name": "WeatherBot",
            "version": "1.0.0",
            "description": "Weather forecasting service",
            "skills": [{"name": "get_weather", "description": "Get weather"}],
            "endpoint": "http://localhost:8001/weather",
            "protocol": "http",
            "tags": ["weather", "api"],
            "health_status": "healthy",
        }
        response = self.client.post("/api/v1/agents/register", json=payload)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()["success"])

    def test_agent_lifecycle_and_discovery(self):
        self._register_sample("weather-bot-001")

        get_resp = self.client.get("/api/v1/agents/weather-bot-001")
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(get_resp.json()["data"]["agent"]["id"], "weather-bot-001")

        discover_resp = self.client.get("/api/v1/agents/discover?skill=get_weather")
        self.assertEqual(discover_resp.status_code, 200)
        self.assertEqual(len(discover_resp.json()["data"]["agents"]), 1)

        search_resp = self.client.get("/api/v1/agents/search?q=weather")
        self.assertEqual(search_resp.status_code, 200)
        self.assertGreaterEqual(search_resp.json()["data"]["total"], 1)

        stats_resp = self.client.get("/api/v1/stats")
        self.assertEqual(stats_resp.status_code, 200)
        self.assertEqual(stats_resp.json()["data"]["total_agents"], 1)

        delete_resp = self.client.delete("/api/v1/agents/weather-bot-001")
        self.assertEqual(delete_resp.status_code, 200)

        list_resp = self.client.get("/api/v1/agents")
        self.assertEqual(list_resp.status_code, 200)
        self.assertEqual(list_resp.json()["data"]["total"], 0)

    def test_auth_and_health_endpoints(self):
        self._register_sample("secure-bot-001")

        token_resp = self.client.post(
            "/api/v1/auth/token",
            json={"agent_id": "secure-bot-001", "secret": "agentmesh-dev-secret"},
        )
        self.assertEqual(token_resp.status_code, 200)
        token_data = token_resp.json()["data"]
        self.assertIn("access_token", token_data)
        self.assertIn("refresh_token", token_data)

        verify_resp = self.client.get(
            "/api/v1/auth/verify",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        self.assertEqual(verify_resp.status_code, 200)
        self.assertTrue(verify_resp.json()["data"]["valid"])

        refresh_resp = self.client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": token_data["refresh_token"]},
        )
        self.assertEqual(refresh_resp.status_code, 200)
        self.assertIn("access_token", refresh_resp.json()["data"])

        heartbeat_resp = self.client.post(
            "/api/v1/agents/secure-bot-001/heartbeat",
            json={"status": "healthy"},
        )
        self.assertEqual(heartbeat_resp.status_code, 200)
        self.assertEqual(heartbeat_resp.json()["data"]["status"], "healthy")

        health_resp = self.client.get("/api/v1/agents/secure-bot-001/health")
        self.assertEqual(health_resp.status_code, 200)
        self.assertEqual(health_resp.json()["data"]["status"], "healthy")

        version_resp = self.client.get("/version")
        self.assertEqual(version_resp.status_code, 200)
        self.assertEqual(version_resp.json()["data"]["api_version"], "v1")


if __name__ == "__main__":
    unittest.main()
