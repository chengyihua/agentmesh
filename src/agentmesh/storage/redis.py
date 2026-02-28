"""Redis storage backend."""

from __future__ import annotations

import json
from typing import List, Optional

from ..core.agent_card import AgentCard
from .base import StorageBackend


class RedisStorage(StorageBackend):
    """Redis-backed storage for agent records."""

    def __init__(self, url: str = "redis://localhost:6379", prefix: str = "agentmesh:"):
        self.url = url
        self.prefix = prefix
        self._client = None

    async def connect(self) -> None:
        try:
            import redis.asyncio as redis
        except ImportError as exc:
            raise RuntimeError("redis package is required for RedisStorage") from exc

        self._client = redis.from_url(self.url, decode_responses=True)
        await self._client.ping()

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _key(self, agent_id: str) -> str:
        return f"{self.prefix}agent:{agent_id}"

    async def upsert_agent(self, agent: AgentCard) -> None:
        if self._client is None:
            await self.connect()
        payload = json.dumps(agent.model_dump(mode="json", exclude_none=True))
        await self._client.set(self._key(agent.id), payload)

    async def get_agent(self, agent_id: str) -> Optional[AgentCard]:
        if self._client is None:
            await self.connect()
        raw = await self._client.get(self._key(agent_id))
        if raw is None:
            return None
        return AgentCard.model_validate(json.loads(raw))

    async def delete_agent(self, agent_id: str) -> bool:
        if self._client is None:
            await self.connect()
        deleted = await self._client.delete(self._key(agent_id))
        return bool(deleted)

    async def list_agents(self, skip: int = 0, limit: int = 1000) -> List[AgentCard]:
        if self._client is None:
            await self.connect()

        keys = []
        async for key in self._client.scan_iter(match=f"{self.prefix}agent:*"):
            keys.append(key)

        keys.sort()
        selected = keys[skip : skip + limit]
        if not selected:
            return []

        raw_values = await self._client.mget(selected)
        agents: List[AgentCard] = []
        for raw in raw_values:
            if raw:
                agents.append(AgentCard.model_validate(json.loads(raw)))
        return agents

    async def clear(self) -> int:
        if self._client is None:
            await self.connect()

        keys = []
        async for key in self._client.scan_iter(match=f"{self.prefix}agent:*"):
            keys.append(key)
        if not keys:
            return 0
        return int(await self._client.delete(*keys))
