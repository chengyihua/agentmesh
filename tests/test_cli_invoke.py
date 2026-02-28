import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, "src")

from agentmesh import cli


class TestCLIInvoke(unittest.TestCase):
    def test_cli_invoke_parses_payload_and_headers(self):
        with patch("agentmesh.cli.SyncAgentMeshClient") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.invoke_agent.return_value = {"success": True}

            with patch("builtins.print"):
                exit_code = cli.main(
                    [
                        "agents",
                        "invoke",
                        "agent-001",
                        "--skill",
                        "echo",
                        "--payload",
                        "{\"value\":1}",
                        "--path",
                        "/invoke",
                        "--method",
                        "POST",
                        "--timeout",
                        "12.5",
                        "--header",
                        "X-Test=abc",
                        "--header",
                        "X-Trace=123",
                    ]
                )

            self.assertEqual(exit_code, 0)
            mock_client.invoke_agent.assert_called_once_with(
                "agent-001",
                payload={"value": 1},
                skill="echo",
                path="/invoke",
                method="POST",
                timeout_seconds=12.5,
                headers={"X-Test": "abc", "X-Trace": "123"},
            )

    def test_cli_invoke_invalid_json(self):
        with patch("agentmesh.cli.SyncAgentMeshClient") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            with patch("builtins.print"):
                exit_code = cli.main(["agents", "invoke", "agent-001", "--payload", "{invalid"])
            self.assertEqual(exit_code, 1)
            mock_client.invoke_agent.assert_not_called()
