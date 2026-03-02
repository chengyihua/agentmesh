import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from .agent_card import AgentCard, HealthStatus
from .events import event_bus, Event, EventType
from ..storage import StorageBackend

logger = logging.getLogger(__name__)

class HealthMonitor:
    def __init__(self, storage: StorageBackend):
        self.storage = storage
        self.health_check_interval = 30
        self.max_unhealthy_time = 300
        self._check_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self, agents: Dict[str, AgentCard]):
        self._running = True
        self._check_task = asyncio.create_task(self._loop(agents))
        logger.info("HealthMonitor started")

    async def stop(self):
        self._running = False
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass

    async def record_heartbeat(self, agent: AgentCard, status: HealthStatus, timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        now = timestamp or datetime.now(timezone.utc)
        old_status = agent.health_status
        
        agent.health_status = status
        agent.last_health_check = now
        agent.last_heartbeat = now
        agent.updated_at = now
        
        # Persist changes
        await self.storage.upsert_agent(agent)
        
        # Publish event if status changed
        if old_status != status:
            await event_bus.publish(Event(
                type=EventType.AGENT_HEALTH_CHANGED, 
                data={"agent_id": agent.id, "status": status.value, "old_status": old_status.value}
            ))
        
        return {
            "agent_id": agent.id,
            "status": status.value,
            "timestamp": now.isoformat(),
            "next_check": (now + timedelta(seconds=self.health_check_interval)).isoformat()
        }

    async def check_agent(self, agent: AgentCard) -> HealthStatus:
        if agent.last_health_check:
            delta = datetime.now(timezone.utc) - agent.last_health_check.astimezone(timezone.utc)
            if delta.total_seconds() > self.max_unhealthy_time:
                old_status = agent.health_status
                if old_status != HealthStatus.UNHEALTHY:
                    agent.set_health_status(HealthStatus.UNHEALTHY) # Or OFFLINE based on logic
                    await self.storage.upsert_agent(agent)
                    
                    await event_bus.publish(Event(
                        type=EventType.AGENT_HEALTH_CHANGED, 
                        data={"agent_id": agent.id, "status": HealthStatus.UNHEALTHY.value, "old_status": old_status.value}
                    ))
        return agent.health_status

    async def _loop(self, agents: Dict[str, AgentCard]):
        while self._running:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._perform_checks(agents)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")

    async def _perform_checks(self, agents: Dict[str, AgentCard]):
        now = datetime.now(timezone.utc)
        for agent in agents.values():
            if not agent.last_health_check:
                continue
            delta = now - agent.last_health_check.astimezone(timezone.utc)
            if delta.total_seconds() > self.max_unhealthy_time:
                if agent.health_status != HealthStatus.OFFLINE:
                    old_status = agent.health_status
                    agent.set_health_status(HealthStatus.OFFLINE)
                    await self.storage.upsert_agent(agent)
                    logger.warning(f"Agent {agent.id} marked OFFLINE")
                    
                    await event_bus.publish(Event(
                        type=EventType.AGENT_HEALTH_CHANGED, 
                        data={"agent_id": agent.id, "status": HealthStatus.OFFLINE.value, "old_status": old_status.value}
                    ))
