
import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from agentmesh.core.federation import FederationManager
from agentmesh.core.registry import AgentRegistry
from agentmesh.core.agent_card import AgentCard, AgentCardUpdate

@pytest.fixture
def mock_registry():
    registry = MagicMock(spec=AgentRegistry)
    registry.list_agents = AsyncMock()
    registry.get_agent = AsyncMock()
    registry.register_agent = AsyncMock()
    registry.update_agent = AsyncMock()
    # Mock security manager
    registry.security_manager = MagicMock()
    registry.security_manager.verify_signature = AsyncMock(return_value=True)
    registry.telemetry = MagicMock()
    return registry

@pytest.mark.asyncio
async def test_get_local_updates_filtering(mock_registry):
    """Test that get_local_updates filters agents by updated_at timestamp."""
    
    # Create timestamps
    now = datetime.now(timezone.utc)
    old_time = now - timedelta(hours=2)
    new_time = now - timedelta(minutes=10)
    
    # Create two agents
    agent_old = AgentCard(
        id="agent-old",
        name="Old Agent",
        version="1.0.0",
        endpoint="http://old.com",
        updated_at=old_time,
        skills=[{"name": "test", "description": "test"}]
    )
    
    agent_new = AgentCard(
        id="agent-new",
        name="New Agent",
        version="2.0.0",
        endpoint="http://new.com",
        updated_at=new_time,
        skills=[{"name": "test", "description": "test"}]
    )
    
    mock_registry.list_agents.return_value = [agent_old, agent_new]
    
    federation = FederationManager(registry=mock_registry)
    
    # Query with timestamp between old and new
    query_time = (now - timedelta(hours=1)).timestamp()
    updates = await federation.get_local_updates(since_timestamp=query_time)
    
    # Should only return the new agent
    assert len(updates.agents) == 1
    assert updates.agents[0].id == "agent-new"
    
    # Query with very old timestamp
    updates_all = await federation.get_local_updates(since_timestamp=0)
    assert len(updates_all.agents) == 2

@pytest.mark.asyncio
async def test_process_sync_data_preserves_trust_score(mock_registry):
    """Test that processing updates preserves local trust score."""
    
    # Setup existing agent in registry
    existing_agent = AgentCard(
        id="agent-1",
        name="Agent One",
        version="1.0.0",
        endpoint="http://agent1.com",
        trust_score=0.8,
        updated_at=datetime.now(timezone.utc) - timedelta(hours=1),
        skills=[{"name": "test", "description": "test"}]
    )
    mock_registry.get_agent.return_value = existing_agent
    
    federation = FederationManager(registry=mock_registry)
    
    # Create incoming update with different trust score
    incoming_data = {
        "agents": [{
            "id": "agent-1",
            "name": "Agent One Updated",
            "version": "1.1.0",
            "endpoint": "http://agent1.com",
            "trust_score": 0.5,  # Should be ignored
            "updated_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
            "skills": [{"name": "test", "description": "test"}]
        }],
        "peers": [],
        "timestamp": datetime.now(timezone.utc).timestamp()
    }
    
    # Process update
    await federation._process_sync_data(incoming_data)
    
    # Verify update_agent was called
    assert mock_registry.update_agent.call_count == 1
    call_args = mock_registry.update_agent.call_args
    agent_id, update_obj = call_args[0]
    
    assert agent_id == "agent-1"
    assert isinstance(update_obj, AgentCardUpdate)
    
    # Verify trust_score was NOT included in update (so it stays as None in update_obj, preserving local value)
    # The update logic in FederationManager creates AgentCardUpdate.
    # If trust_score is excluded from model_dump, it won't be in the kwargs passed to AgentCardUpdate.
    # However, AgentCardUpdate has trust_score field.
    # Let's check the actual value in the update object.
    assert update_obj.trust_score is None
    assert update_obj.name == "Agent One Updated"
    assert update_obj.version == "1.1.0"

@pytest.mark.asyncio
async def test_process_sync_data_updates_security_fields(mock_registry):
    """Test that processing updates includes security fields."""
    
    # Setup existing agent
    existing_agent = AgentCard(
        id="agent-secure",
        name="Secure Agent",
        version="1.0.0",
        endpoint="http://secure.com",
        signature="old-sig",
        updated_at=datetime.now(timezone.utc) - timedelta(hours=1),
        skills=[{"name": "test", "description": "test"}]
    )
    mock_registry.get_agent.return_value = existing_agent
    
    federation = FederationManager(registry=mock_registry)
    
    # Incoming update with new signature
    incoming_data = {
        "agents": [{
            "id": "agent-secure",
            "name": "Secure Agent",
            "version": "1.0.1",
            "endpoint": "http://secure.com",
            "signature": "new-sig",
            "manifest_signature": "new-manifest-sig",
            "public_key": "new-pk",
            "updated_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
            "skills": [{"name": "test", "description": "test"}]
        }],
        "peers": [],
        "timestamp": datetime.now(timezone.utc).timestamp()
    }
    
    await federation._process_sync_data(incoming_data)
    
    # Verify update included security fields
    call_args = mock_registry.update_agent.call_args
    _, update_obj = call_args[0]
    
    assert update_obj.signature == "new-sig"
    assert update_obj.manifest_signature == "new-manifest-sig"
    assert update_obj.public_key == "new-pk"
