import asyncio
import sys
import unittest
from typing import Dict, List, Optional

sys.path.insert(0, "src")

from agentmesh.core.agent_card import AgentCard, HealthStatus, Skill
from agentmesh.core.registry import AgentRegistry
from agentmesh.storage import StorageBackend


def _clone_agent(agent: AgentCard) -> AgentCard:
    return AgentCard.model_validate(agent.model_dump(mode="json", exclude_none=True))


class SharedMemoryStorage(StorageBackend):
    def __init__(self):
        self._agents: Dict[str, AgentCard] = {}
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        return None

    async def close(self) -> None:
        return None

    async def upsert_agent(self, agent: AgentCard) -> None:
        async with self._lock:
            self._agents[agent.id] = _clone_agent(agent)

    async def get_agent(self, agent_id: str) -> Optional[AgentCard]:
        async with self._lock:
            agent = self._agents.get(agent_id)
            return _clone_agent(agent) if agent else None

    async def delete_agent(self, agent_id: str) -> bool:
        async with self._lock:
            if agent_id in self._agents:
                del self._agents[agent_id]
                return True
            return False

    async def list_agents(self, skip: int = 0, limit: int = 1000) -> List[AgentCard]:
        async with self._lock:
            agents = sorted(self._agents.values(), key=lambda x: x.updated_at, reverse=True)
            selected = agents[skip : skip + limit]
            return [_clone_agent(agent) for agent in selected]

    async def clear(self) -> int:
        async with self._lock:
            count = len(self._agents)
            self._agents.clear()
            return count


class TestRegistryCrossInstanceSync(unittest.TestCase):
    def test_sync_from_shared_storage(self):
        async def _run():
            storage = SharedMemoryStorage()
            primary = AgentRegistry(storage=storage, sync_interval_seconds=1, enable_storage_sync=True)
            replica = AgentRegistry(storage=storage, sync_interval_seconds=1, enable_storage_sync=True)

            await primary.start()
            await replica.start()
            try:
                agent = AgentCard(
                    id="sync-agent-001",
                    name="SyncAgent",
                    version="1.0.0",
                    description="Cross-instance sync test",
                    skills=[Skill(name="sync_skill", description="sync")],
                    endpoint="http://localhost:9002",
                    protocol="http",
                    tags=["sync"],
                    health_status=HealthStatus.HEALTHY,
                )

                await primary.register_agent(agent)

                found = False
                for _ in range(20):
                    discovered = await replica.discover_agents(skill_name="sync_skill", healthy_only=False)
                    if any(item.id == "sync-agent-001" for item in discovered):
                        found = True
                        break
                    await asyncio.sleep(0.2)
                self.assertTrue(found, "Replica should discover agents registered by primary instance")

                await primary.deregister_agent("sync-agent-001")

                removed = False
                for _ in range(20):
                    discovered = await replica.discover_agents(skill_name="sync_skill", healthy_only=False)
                    if all(item.id != "sync-agent-001" for item in discovered):
                        removed = True
                        break
                    await asyncio.sleep(0.2)
                self.assertTrue(removed, "Replica should remove agents deleted by primary instance")
            finally:
                await primary.stop()
                await replica.stop()

        asyncio.run(_run())
