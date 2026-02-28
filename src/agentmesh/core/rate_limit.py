"""Rate limiting and budget enforcement for AgentMesh."""

from __future__ import annotations

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Optional, Tuple

from fastapi import HTTPException, status

from .agent_card import AgentCard
from .telemetry import TelemetryManager
from .trust import TrustEvent
from .errors import ErrorCode, raise_error

logger = logging.getLogger(__name__)


class AgentRateLimiter:
    """
    Enforces local rate limits (QPS and Concurrency) defined in AgentCard.
    Operates on the 'callee' side (target agent).
    """

    def __init__(self, telemetry: Optional[TelemetryManager] = None, trust_manager: Optional[Any] = None):
        # agent_id -> current concurrent requests
        self._concurrency: Dict[str, int] = {}
        # agent_id -> (last_refill_time, tokens)
        self._qps_state: Dict[str, Tuple[float, float]] = {}
        self._lock = asyncio.Lock()
        self.telemetry = telemetry
        self.trust_manager = trust_manager

    async def _acquire(self, agent: AgentCard) -> bool:
        """
        Attempt to acquire execution slot for the agent.
        Checks both concurrency limit and QPS budget.
        """
        async with self._lock:
            now = time.time()
            agent_id = agent.id

            # 1. Check Concurrency Limit
            if agent.concurrency_limit is not None and agent.concurrency_limit > 0:
                current = self._concurrency.get(agent_id, 0)
                if current >= agent.concurrency_limit:
                    logger.warning(
                        f"Concurrency limit exceeded for {agent_id}: {current}/{agent.concurrency_limit}",
                        extra={"agent_id": agent_id, "limit_type": "concurrency", "current": current, "limit": agent.concurrency_limit}
                    )
                    if self.telemetry:
                        self.telemetry.rate_limit_rejections.labels(
                            agent_id=agent_id, 
                            limit_type="concurrency"
                        ).inc()
                    
                    if self.trust_manager:
                        await self.trust_manager.record_event(agent_id, TrustEvent.RATE_LIMIT)
                        
                    return False
                self._concurrency[agent_id] = current + 1

            # 2. Check QPS Budget (Token Bucket)
            # qps_budget is float (e.g. 0.5 = 1 req / 2 sec)
            if agent.qps_budget is not None and agent.qps_budget > 0:
                # Capacity should be at least 1.0 to allow burst of 1 if rate is low
                capacity = max(float(agent.qps_budget), 1.0)
                
                # Default state: full bucket
                last_refill, tokens = self._qps_state.get(agent_id, (now, capacity))
                
                # Refill tokens based on elapsed time
                elapsed = now - last_refill
                refill_amount = elapsed * float(agent.qps_budget)
                tokens = min(capacity, tokens + refill_amount)
                
                if tokens < 1.0:
                    logger.warning(
                        f"QPS budget exceeded for {agent_id}: {tokens:.2f}/{agent.qps_budget}",
                        extra={"agent_id": agent_id, "limit_type": "qps", "tokens": tokens, "budget": agent.qps_budget}
                    )
                    if self.telemetry:
                        self.telemetry.rate_limit_rejections.labels(
                            agent_id=agent_id, 
                            limit_type="qps"
                        ).inc()
                    
                    if self.trust_manager:
                        await self.trust_manager.record_event(agent_id, TrustEvent.RATE_LIMIT)
                    
                    # Rollback concurrency if QPS failed
                    if agent.concurrency_limit is not None and agent.concurrency_limit > 0:
                        self._concurrency[agent_id] -= 1
                    return False
                
                # Consume 1 token
                self._qps_state[agent_id] = (now, tokens - 1.0)

            return True

    async def _release(self, agent: AgentCard):
        """Release concurrency slot."""
        if agent.concurrency_limit is not None and agent.concurrency_limit > 0:
            async with self._lock:
                current = self._concurrency.get(agent.id, 0)
                if current > 0:
                    self._concurrency[agent.id] = current - 1

    @asynccontextmanager
    async def limit(self, agent: AgentCard):
        """
        Async context manager to enforce limits.
        Raises HTTPException(429) if limits are exceeded.
        """
        if not await self._acquire(agent):
            raise_error(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                code=ErrorCode.RATE_LIMIT_EXCEEDED,
                message="Rate limit exceeded",
                details={
                    "agent_id": agent.id,
                    "limits": {
                        "qps": agent.qps_budget,
                        "concurrency": agent.concurrency_limit,
                    },
                }
            )
        try:
            yield
        finally:
            await self._release(agent)
