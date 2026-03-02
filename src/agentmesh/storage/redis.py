"""Redis storage backend."""

from __future__ import annotations

import json
from typing import List, Optional

from ..core.agent_card import AgentCard
from ..auth.user import User
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

    def _updated_at_key(self) -> str:
        return f"{self.prefix}index:agents:updated_at"

    async def upsert_agent(self, agent: AgentCard) -> None:
        if self._client is None:
            await self.connect()
        payload = json.dumps(agent.model_dump(mode="json", exclude_none=True))
        
        async with self._client.pipeline() as pipe:
            pipe.set(self._key(agent.id), payload)
            # Add to sorted set for time-based queries
            pipe.zadd(self._updated_at_key(), {agent.id: agent.updated_at.timestamp()})
            await pipe.execute()

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
        
        async with self._client.pipeline() as pipe:
            pipe.delete(self._key(agent_id))
            pipe.zrem(self._updated_at_key(), agent_id)
            results = await pipe.execute()
            
        return bool(results[0])

    async def list_agents(self, skip: int = 0, limit: int = 1000) -> List[AgentCard]:
        if self._client is None:
            await self.connect()

        # Use ZSET for consistent pagination based on updated_at
        # ZREVRANGE to show newest first
        agent_ids = await self._client.zrevrange(self._updated_at_key(), skip, skip + limit - 1)
        
        if not agent_ids:
            return []

        keys = [self._key(aid) for aid in agent_ids]
        raw_values = await self._client.mget(keys)
        
        agents: List[AgentCard] = []
        for raw in raw_values:
            if raw:
                agents.append(AgentCard.model_validate(json.loads(raw)))
        return agents

    async def list_agents_since(self, timestamp: float) -> List[AgentCard]:
        """Get agents updated since the given timestamp using ZSET."""
        if self._client is None:
            await self.connect()
            
        # Get IDs updated after timestamp
        # ZRANGEBYSCORE key min max
        # min = (timestamp + epsilon), max = +inf
        # Redis uses exclusive range with "(" prefix
        agent_ids = await self._client.zrangebyscore(self._updated_at_key(), f"({timestamp}", "+inf")
        
        if not agent_ids:
            return []
            
        keys = [self._key(aid) for aid in agent_ids]
        raw_values = await self._client.mget(keys)
        
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

    def _user_key(self, user_id: str) -> str:
        return f"{self.prefix}user:{user_id}"

    def _user_phone_idx(self, phone: str) -> str:
        return f"{self.prefix}idx:user_phone:{phone}"

    async def upsert_user(self, user: User) -> None:
        if self._client is None:
            await self.connect()
        # Ensure model_dump handles datetime serialization properly (mode="json")
        payload = json.dumps(user.model_dump(mode="json", exclude_none=True))
        
        async with self._client.pipeline() as pipe:
            pipe.set(self._user_key(user.id), payload)
            # Maintain secondary index for phone
            pipe.set(self._user_phone_idx(user.phone_number), user.id)
            await pipe.execute()

    async def get_user(self, user_id: str) -> Optional[User]:
        if self._client is None:
            await self.connect()
        raw = await self._client.get(self._user_key(user_id))
        if raw is None:
            return None
        return User.model_validate(json.loads(raw))

    async def get_user_by_phone(self, phone_number: str) -> Optional[User]:
        if self._client is None:
            await self.connect()
        
        # Look up ID from index
        # Redis returns bytes if not decode_responses=True (which we set in connect)
        user_id = await self._client.get(self._user_phone_idx(phone_number))
        if not user_id:
            return None
            
        return await self.get_user(user_id)
