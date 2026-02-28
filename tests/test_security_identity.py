import pytest
from agentmesh.core.security import SecurityManager

def test_derive_agent_id():
    sm = SecurityManager()
    # Mock a public key (e.g., base58 or hex string)
    public_key = "MCowBQYDK2VwAyEAqmT5j7x4j7x4j7x4j7x4j7x4j7x4j7x4j7x4j7x4j7w="
    agent_id = sm.derive_agent_id(public_key)
    assert agent_id is not None
    assert len(agent_id) > 0
    # Ensure it's deterministic
    assert agent_id == sm.derive_agent_id(public_key)

def test_validate_id_match():
    sm = SecurityManager()
    public_key = "MCowBQYDK2VwAyEAqmT5j7x4j7x4j7x4j7x4j7x4j7x4j7x4j7x4j7x4j7w="
    agent_id = sm.derive_agent_id(public_key)
    assert sm.validate_agent_id(agent_id, public_key) is True
    assert sm.validate_agent_id("wrong-id", public_key) is False

@pytest.mark.asyncio
async def test_verify_manifest_signature():
    sm = SecurityManager()
    
    # 1. Generate keys
    keys = sm.generate_key_pair()
    public_key = keys["public_key"]
    private_key = keys["private_key"]
    
    # 2. Create AgentCard
    from agentmesh.core.agent_card import AgentCard
    
    card = AgentCard(
        id=sm.derive_agent_id(public_key),
        name="Test Agent",
        version="1.0.0",
        endpoint="http://localhost:8000",
        public_key=public_key,
        # manifest_signature will be added later
        skills=[{"name": "test", "description": "test"}]
    )
    
    # 3. Sign it
    signature = await sm.sign_agent_card(card, private_key)
    # sign_agent_card returns "ed25519:..."
    
    # 4. Attach signature to manifest_signature
    card.manifest_signature = signature
    # Also verify it works without 'signature' field (legacy)
    card.signature = None
    
    # 5. Verify
    assert await sm.verify_signature(card) is True
    
    # 6. Tamper
    card.name = "Tampered Agent"
    assert await sm.verify_signature(card) is False
