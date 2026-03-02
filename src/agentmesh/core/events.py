import asyncio
import logging
from typing import Dict, List, Any, Callable, Awaitable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class EventType(str, Enum):
    AGENT_REGISTERED = "agent_registered"
    AGENT_UPDATED = "agent_updated"
    AGENT_HEALTH_CHANGED = "agent_health_changed"
    TRUST_SCORE_CHANGED = "trust_score_changed"

@dataclass
class Event:
    type: EventType
    data: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class EventBus:
    def __init__(self):
        self._subscribers: List[asyncio.Queue] = []

    async def publish(self, event: Event):
        for queue in self._subscribers:
            await queue.put(event)

    async def subscribe(self) -> asyncio.Queue:
        queue = asyncio.Queue()
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        if queue in self._subscribers:
            self._subscribers.remove(queue)

# Global singleton instance
event_bus = EventBus()
