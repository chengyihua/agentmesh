import pytest
from unittest.mock import MagicMock, AsyncMock
from agentmesh.core.registry import AgentRegistry, SecurityError
from agentmesh.core.agent_card import AgentCard, ProtocolType
from agentmesh.core.security import SecurityManager

@pytest.mark.asyncio
async def test_register_enforce_signature_missing():
    # Setup registry with enforcement enabled
    registry = AgentRegistry(require_signed_registration=True)
    
    card = AgentCard(
        id="test-agent", 
        name="Test", 
        version="1.0", 
        endpoint="http://localhost",
        public_key=None, 
        manifest_signature=None,
        skills=[{"name": "test", "description": "test"}]
    )
    
    with pytest.raises(SecurityError, match="Signature required"):
        await registry.register_agent(card)

@pytest.mark.asyncio
async def test_register_enforce_id_mismatch():
    registry = AgentRegistry(require_signed_registration=True)
    # Mock security manager to pass signature but fail ID check if implemented there
    # For now, we assume ID check is part of registration logic
    
    # We need a valid-looking key but ID that doesn't match
    card = AgentCard(
        id="mismatch-id",
        name="Test",
        version="1.0",
        endpoint="http://localhost",
        public_key="some-key",
        manifest_signature="valid-sig",
        skills=[{"name": "test", "description": "test"}]
    )
    
    # Mock verify_signature to return True to isolate ID check
    # Note: Registry creates its own SecurityManager by default if not passed.
    # We should inject a mock if possible, but let's see if Registry allows injection.
    # Assuming the implementation plan suggests Registry takes optional SecurityManager.
    
    mock_sm = MagicMock(spec=SecurityManager)
    mock_sm.verify_signature = AsyncMock(return_value=True)
    mock_sm.validate_agent_id = MagicMock(return_value=False)
    registry.security_manager = mock_sm
    
    with pytest.raises(SecurityError, match="does not match derived ID"):
        await registry.register_agent(card)
