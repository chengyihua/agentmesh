"""Storage backend abstractions for AgentMesh."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from ..core.agent_card import AgentCard


class StorageBackend(ABC):
    """Abstract storage backend for agent persistence."""

    @abstractmethod
    async def connect(self) -> None:
        """Initialize storage connection/resources."""

    @abstractmethod
    async def close(self) -> None:
        """Release storage connection/resources."""

    @abstractmethod
    async def upsert_agent(self, agent: AgentCard) -> None:
        """Insert or update an agent record."""

    @abstractmethod
    async def get_agent(self, agent_id: str) -> Optional[AgentCard]:
        """Get one agent by id."""

    @abstractmethod
    async def delete_agent(self, agent_id: str) -> bool:
        """Delete one agent by id."""

    @abstractmethod
    async def list_agents(self, skip: int = 0, limit: int = 1000) -> List[AgentCard]:
        """List agents with pagination."""

    @abstractmethod
    async def clear(self) -> int:
        """Delete all agents and return deleted count."""
