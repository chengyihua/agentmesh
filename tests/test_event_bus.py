import pytest
import asyncio
from agentmesh.core.events import EventBus, Event, EventType

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
