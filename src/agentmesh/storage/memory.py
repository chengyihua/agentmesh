"""In-memory storage backend."""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, List, Optional

from ..core.agent_card import AgentCard
from .base import StorageBackend

logger = logging.getLogger(__name__)

class MemoryStorage(StorageBackend):
    """Simple in-memory backend for development/testing."""

    def __init__(self):
        self._agents: Dict[str, AgentCard] = {}
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        logger.info("MemoryStorage connected")

    async def close(self) -> None:
        self._agents.clear()
        logger.info("MemoryStorage closed and cleared")

    async def upsert_agent(self, agent: AgentCard) -> None:
        async with self._lock:
            self._agents[agent.id] = agent

    async def get_agent(self, agent_id: str) -> Optional[AgentCard]:
        async with self._lock:
            return self._agents.get(agent_id)

    async def delete_agent(self, agent_id: str) -> bool:
        async with self._lock:
            if agent_id in self._agents:
                del self._agents[agent_id]
                return True
            return False

    async def list_agents(self, skip: int = 0, limit: int = 1000) -> List[AgentCard]:
        async with self._lock:
            agents = list(self._agents.values())
            return agents[skip : skip + limit]

    async def clear(self) -> int:
        async with self._lock:
            count = len(self._agents)
            self._agents.clear()
            return count
