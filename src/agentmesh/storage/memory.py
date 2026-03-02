"""In-memory storage backend."""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, List, Optional

from ..core.agent_card import AgentCard
from ..auth.user import User
from .base import StorageBackend

logger = logging.getLogger(__name__)

class MemoryStorage(StorageBackend):
    """Simple in-memory backend for development/testing."""

    def __init__(self):
        self._agents: Dict[str, AgentCard] = {}
        self._users: Dict[str, User] = {}
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        logger.info("MemoryStorage connected")

    async def close(self) -> None:
        self._agents.clear()
        self._users.clear()
        logger.info("MemoryStorage closed and cleared")

    # --- Agent Methods ---

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

    async def list_agents_since(self, timestamp: float) -> List[AgentCard]:
        async with self._lock:
            return [
                agent for agent in self._agents.values()
                if agent.updated_at.timestamp() > timestamp
            ]

    # --- User Methods ---

    async def upsert_user(self, user: User) -> None:
        async with self._lock:
            self._users[user.id] = user

    async def get_user(self, user_id: str) -> Optional[User]:
        async with self._lock:
            return self._users.get(user_id)

    async def get_user_by_phone(self, phone_number: str) -> Optional[User]:
        async with self._lock:
            for user in self._users.values():
                if user.phone_number == phone_number:
                    return user
            return None

    async def clear(self) -> int:
        async with self._lock:
            count = len(self._agents) + len(self._users)
            self._agents.clear()
            self._users.clear()
            return count
