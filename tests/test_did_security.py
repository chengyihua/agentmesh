import pytest
import hashlib
from agentmesh.core.security import SecurityManager

def test_did_generation():
    security = SecurityManager()
    public_key = "test_public_key_12345"
    
    # Calculate expected DID
    digest = hashlib.sha256(public_key.encode("utf-8")).hexdigest()
    expected_did = f"did:agent:{digest}"
    
    # Test derivation
    assert security.derive_did(public_key) == expected_did
    
    # Test validation
    assert security.validate_agent_id(expected_did, public_key) is True
    assert security.validate_agent_id("did:agent:wrong_hash", public_key) is False
    assert security.validate_agent_id(expected_did, "wrong_key") is False

def test_legacy_id_support():
    security = SecurityManager()
    public_key = "test_public_key_legacy"
    
    # Calculate legacy ID
    digest = hashlib.sha256(public_key.encode("utf-8")).digest()
    expected_legacy_id = digest[:20].hex()
    
    # Test legacy validation
    assert security.validate_agent_id(expected_legacy_id, public_key) is True
    
    # Ensure legacy ID is NOT treated as DID
    assert not expected_legacy_id.startswith("did:agent:")
