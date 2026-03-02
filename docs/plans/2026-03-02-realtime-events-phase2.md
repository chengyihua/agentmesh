# Real-time Event System (SSE) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement a Server-Sent Events (SSE) system to push real-time agent updates (health, trust) to the frontend, replacing inefficient polling.

**Architecture:**
- **EventBus**: An in-memory Pub/Sub mechanism to broadcast events.
- **SSE Route**: A FastAPI streaming endpoint (`/events`) that subscribes to the EventBus and yields messages to clients.
- **Frontend Integration**: A `useEvents` hook to consume the stream and update React Query cache.

**Tech Stack:** Python (asyncio), FastAPI (StreamingResponse), React (EventSource)

---

### Task 1: Create EventBus

**Files:**
- Create: `src/agentmesh/core/events.py`
- Test: `tests/test_event_bus.py`

**Step 1: Define EventBus Class**

Create `src/agentmesh/core/events.py`:
```python
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
```

**Step 2: Create Test for EventBus**

Create `tests/test_event_bus.py`:
```python
import pytest
import asyncio
from src.agentmesh.core.events import EventBus, Event, EventType

@pytest.mark.asyncio
async def test_pub_sub():
    bus = EventBus()
    queue = await bus.subscribe()
    
    event = Event(type=EventType.AGENT_REGISTERED, data={"id": "test-1"})
    await bus.publish(event)
    
    received = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert received.type == EventType.AGENT_REGISTERED
    assert received.data["id"] == "test-1"
    
    bus.unsubscribe(queue)
    assert len(bus._subscribers) == 0
```

### Task 2: Integrate EventBus into Registry

**Files:**
- Modify: `src/agentmesh/core/registry.py`
- Modify: `src/agentmesh/core/health.py`

**Step 1: Publish Health Events**

Modify `src/agentmesh/core/health.py`:
- Import `event_bus`, `Event`, `EventType`.
- In `record_heartbeat` and `check_agent`, publish `AGENT_HEALTH_CHANGED` event if status changes.

```python
# In record_heartbeat:
if old_status != status:
    await event_bus.publish(Event(
        type=EventType.AGENT_HEALTH_CHANGED, 
        data={"agent_id": agent.id, "status": status.value}
    ))
```

**Step 2: Publish Registration Events**

Modify `src/agentmesh/core/registry.py`:
- Import `event_bus`, `Event`, `EventType`.
- In `register_agent`, publish `AGENT_REGISTERED` or `AGENT_UPDATED`.

```python
# In register_agent (after upsert):
event_type = EventType.AGENT_UPDATED if is_update else EventType.AGENT_REGISTERED
await event_bus.publish(Event(type=event_type, data={"agent_id": agent.id}))
```

### Task 3: Implement SSE Endpoint

**Files:**
- Modify: `src/agentmesh/api/routes.py`

**Step 1: Add /events Route**

Modify `src/agentmesh/api/routes.py`:
```python
from fastapi.responses import StreamingResponse
from ..core.events import event_bus, Event

@router.get("/events")
async def sse_endpoint(request: Request):
    async def event_generator():
        queue = await event_bus.subscribe()
        try:
            while True:
                if await request.is_disconnected():
                    break
                event: Event = await queue.get()
                yield f"event: {event.type.value}\ndata: {json.dumps(event.data)}\n\n"
        finally:
            event_bus.unsubscribe(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

### Task 4: Frontend Integration

**Files:**
- Create: `web/src/hooks/useEvents.ts`
- Modify: `web/src/app/agents/page.tsx`

**Step 1: Create useEvents Hook**

Create `web/src/hooks/useEvents.ts`:
```typescript
import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';

export function useEvents() {
  const queryClient = useQueryClient();

  useEffect(() => {
    const eventSource = new EventSource('/api/events');

    eventSource.addEventListener('agent_registered', () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    });

    eventSource.addEventListener('agent_updated', () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    });
    
    eventSource.addEventListener('agent_health_changed', () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    });

    return () => {
      eventSource.close();
    };
  }, [queryClient]);
}
```

**Step 2: Use Hook in Page**

Modify `web/src/app/agents/page.tsx`:
- Import and call `useEvents()` at the top level of the component.
