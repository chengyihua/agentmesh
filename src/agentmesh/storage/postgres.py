"""PostgreSQL storage backend."""

from __future__ import annotations

import json
from typing import List, Optional

from ..core.agent_card import AgentCard
from .base import StorageBackend


class PostgresStorage(StorageBackend):
    """PostgreSQL backend using asyncpg."""

    def __init__(self, dsn: str = "postgresql://localhost:5432/agentmesh"):
        self.dsn = dsn
        self._pool = None

    async def connect(self) -> None:
        try:
            import asyncpg
        except ImportError as exc:
            raise RuntimeError("asyncpg package is required for PostgresStorage") from exc

        self._pool = await asyncpg.create_pool(self.dsn)
        await self._ensure_schema()

    async def _ensure_schema(self) -> None:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agentmesh_agents (
                    id TEXT PRIMARY KEY,
                    payload JSONB NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def upsert_agent(self, agent: AgentCard) -> None:
        if self._pool is None:
            await self.connect()
        payload = json.dumps(agent.model_dump(mode="json", exclude_none=True))

        assert self._pool is not None
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO agentmesh_agents (id, payload, updated_at)
                VALUES ($1, $2::jsonb, NOW())
                ON CONFLICT (id)
                DO UPDATE SET payload = EXCLUDED.payload, updated_at = NOW()
                """,
                agent.id,
                payload,
            )

    async def get_agent(self, agent_id: str) -> Optional[AgentCard]:
        if self._pool is None:
            await self.connect()

        assert self._pool is not None
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT payload FROM agentmesh_agents WHERE id = $1",
                agent_id,
            )
        if not row:
            return None
        return AgentCard.model_validate(row["payload"])

    async def delete_agent(self, agent_id: str) -> bool:
        if self._pool is None:
            await self.connect()

        assert self._pool is not None
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM agentmesh_agents WHERE id = $1",
                agent_id,
            )
        return result.endswith("1")

    async def list_agents(self, skip: int = 0, limit: int = 1000) -> List[AgentCard]:
        if self._pool is None:
            await self.connect()

        assert self._pool is not None
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT payload
                FROM agentmesh_agents
                ORDER BY updated_at DESC
                OFFSET $1
                LIMIT $2
                """,
                skip,
                limit,
            )
        return [AgentCard.model_validate(row["payload"]) for row in rows]

    async def clear(self) -> int:
        if self._pool is None:
            await self.connect()

        assert self._pool is not None
        async with self._pool.acquire() as conn:
            result = await conn.execute("DELETE FROM agentmesh_agents")
        return int(result.split(" ")[-1])
