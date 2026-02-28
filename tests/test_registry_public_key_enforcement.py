
import pytest
from unittest.mock import MagicMock, AsyncMock
from agentmesh.core.registry import AgentRegistry, SecurityError
from agentmesh.core.agent_card import AgentCard
from agentmesh.core.security import SecurityManager

@pytest.fixture
def mock_security_manager():
    sm = MagicMock(spec=SecurityManager)
    # Default behavior: ID validation fails unless configured
    sm.validate_agent_id.return_value = False 
    sm.verify_signature = AsyncMock(return_value=True)
    return sm

@pytest.fixture
def registry(mock_security_manager):
    # Initialize with require_signed_registration=False to test base logic
    return AgentRegistry(
        security_manager=mock_security_manager,
        require_signed_registration=False
    )

@pytest.mark.asyncio
async def test_registration_with_valid_public_key_and_matching_id(registry, mock_security_manager):
    """
    Test that registration succeeds when public key is present and ID matches.
    """
    # Setup
    mock_security_manager.validate_agent_id.return_value = True
    
    card = AgentCard(
        id="derived-id",
        name="Valid Agent",
        version="1.0.0",
        endpoint="http://localhost",
        public_key="valid-public-key",
        skills=[{"name": "test", "description": "test"}]
    )
    
    # Execute
    result_id = await registry.register_agent(card)
    
    # Verify
    assert result_id == "derived-id"
    mock_security_manager.validate_agent_id.assert_called_with("derived-id", "valid-public-key")

@pytest.mark.asyncio
async def test_registration_with_public_key_mismatch_id(registry, mock_security_manager):
    """
    Test that registration FAILS when public key is present but ID does not match.
    Even if require_signed_registration=False.
    """
    # Setup
    mock_security_manager.validate_agent_id.return_value = False
    
    card = AgentCard(
        id="mismatch-id",
        name="Invalid Agent",
        version="1.0.0",
        endpoint="http://localhost",
        public_key="some-public-key",
        skills=[{"name": "test", "description": "test"}]
    )
    
    # Execute & Verify
    with pytest.raises(SecurityError, match="does not match derived ID"):
        await registry.register_agent(card)
        
    mock_security_manager.validate_agent_id.assert_called_with("mismatch-id", "some-public-key")

@pytest.mark.asyncio
async def test_registration_without_public_key_legacy_mode(registry, mock_security_manager):
    """
    Test that registration succeeds without public key in default (legacy) mode.
    """
    card = AgentCard(
        id="legacy-agent",
        name="Legacy Agent",
        version="1.0.0",
        endpoint="http://localhost",
        public_key=None,
        skills=[{"name": "test", "description": "test"}]
    )
    
    # Execute
    result_id = await registry.register_agent(card)
    
    # Verify
    assert result_id == "legacy-agent"
    # validate_agent_id should NOT be called
    mock_security_manager.validate_agent_id.assert_not_called()

@pytest.mark.asyncio
async def test_registration_strict_mode_requires_signature_and_key():
    """
    Test that require_signed_registration=True enforces public key and signature.
    """
    mock_sm = MagicMock(spec=SecurityManager)
    mock_sm.validate_agent_id.return_value = True
    mock_sm.verify_signature = AsyncMock(return_value=True)
    
    strict_registry = AgentRegistry(
        security_manager=mock_sm,
        require_signed_registration=True
    )
    
    # 1. Missing Public Key -> Fail
    card_no_key = AgentCard(
        id="agent-1",
        name="No Key",
        version="1.0.0",
        endpoint="http://localhost",
        public_key=None,
        manifest_signature="sig",
        skills=[{"name": "test", "description": "test"}]
    )
    with pytest.raises(SecurityError, match="Signature required"):
        await strict_registry.register_agent(card_no_key)
        
    # 2. Missing Signature -> Fail
    card_no_sig = AgentCard(
        id="agent-2",
        name="No Sig",
        version="1.0.0",
        endpoint="http://localhost",
        public_key="pk",
        manifest_signature=None,
        skills=[{"name": "test", "description": "test"}]
    )
    with pytest.raises(SecurityError, match="Signature required"):
        await strict_registry.register_agent(card_no_sig)
        
    # 3. Both Present & Valid -> Pass
    card_valid = AgentCard(
        id="valid-agent",
        name="Valid",
        version="1.0.0",
        endpoint="http://localhost",
        public_key="pk",
        manifest_signature="sig",
        skills=[{"name": "test", "description": "test"}]
    )
    await strict_registry.register_agent(card_valid)
