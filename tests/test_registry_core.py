import asyncio
import sys
import unittest
from uuid import uuid4

sys.path.insert(0, "src")

from agentmesh.core.agent_card import AgentCard, HealthStatus, ProtocolType, Skill
from agentmesh.core.registry import AgentRegistry


class TestAgentRegistryCore(unittest.TestCase):
    def test_registry_lifecycle(self):
        async def _run():
            registry = AgentRegistry()
            await registry.start()
            try:
                agent = AgentCard(
                    id=f"core-test-{uuid4().hex[:8]}",
                    name="CoreTestBot",
                    version="1.0.0",
                    description="Registry core lifecycle test",
                    skills=[Skill(name="test_skill", description="Test skill")],
                    endpoint="http://localhost:9001",
                    protocol=ProtocolType.HTTP,
                    tags=["test"],
                    health_status=HealthStatus.HEALTHY,
                )

                agent_id = await registry.register_agent(agent)
                self.assertEqual(agent_id, agent.id)

                stored = await registry.get_agent(agent_id)
                self.assertIsNotNone(stored)
                assert stored is not None
                self.assertEqual(stored.name, "CoreTestBot")

                discovered = await registry.discover_agents(skill_name="test_skill")
                self.assertEqual(len(discovered), 1)
                self.assertEqual(discovered[0].id, agent_id)

                deleted = await registry.deregister_agent(agent_id)
                self.assertTrue(deleted)

                stats = registry.get_stats()
                self.assertEqual(stats["total_agents"], 0)
            finally:
                await registry.stop()

        asyncio.run(_run())
