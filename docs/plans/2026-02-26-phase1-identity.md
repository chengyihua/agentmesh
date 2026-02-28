# AgentMesh Decentralized Phase 1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement Identity & Registration Model (PR1) for decentralized AgentMesh, including public key-based ID derivation and mandatory signature verification.

**Architecture:** Extend `AgentCard` with `public_key`, `manifest_signature` and other metadata. Implement logic in `SecurityManager` to derive Agent ID from public key and verify signatures. Update `AgentRegistry` to enforce signature verification based on configuration.

**Tech Stack:** Python 3.10+, Pydantic, cryptography (Ed25519/RSA), pytest.

---

### Task 1: Extend AgentCard Model

**Files:**
- Modify: `src/agentmesh/core/agent_card.py`
- Test: `tests/test_agent_card_model.py`

**Step 1: Write the failing test**

Create `tests/test_agent_card_model.py` to verify new fields.

```python
from agentmesh.core.agent_card import AgentCard, ProtocolType

def test_agent_card_extended_fields():
    card = AgentCard(
        id="test-agent-1",
        name="Test Agent",
        version="1.0.0",
        endpoint="http://localhost:8000",
        protocol=ProtocolType.HTTP,
        public_key="some_public_key",
        manifest_signature="some_signature",
        pricing={"model": "token", "rate": 0.001},
        qps_budget=100,
        concurrency_limit=10,
        vector_desc="This is a test agent for vector search",
        models=["gpt-4", "claude-3"]
    )
    assert card.public_key == "some_public_key"
    assert card.manifest_signature == "some_signature"
    assert card.pricing["model"] == "token"
    assert card.qps_budget == 100
    assert card.concurrency_limit == 10
    assert card.vector_desc == "This is a test agent for vector search"
    assert "gpt-4" in card.models
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_agent_card_model.py -v`
Expected: FAIL (ValidationError or AttributeError)

**Step 3: Write minimal implementation**

Update `src/agentmesh/core/agent_card.py`:

```python
# Add imports if needed
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

# Update AgentCard class
class AgentCard(BaseModel):
    # ... existing fields ...
    # Make public_key and signature optional for backward compatibility for now, 
    # or follow PRD strictness. Let's make them optional in Pydantic but enforced logic-wise if configured.
    # Actually PRD says "public_key (Required)". But for migration, let's keep Optional with default=None 
    # and validate in logic, OR make them required if we want strict schema update.
    # Given "Phase 1", let's stick to Optional for now to avoid breaking existing tests immediately, 
    # but add the fields.
    
    public_key: Optional[str] = Field(default=None, description="Public key of the agent identity")
    manifest_signature: Optional[str] = Field(default=None, description="Signature of the manifest by the private key")
    
    pricing: Optional[Dict[str, Any]] = Field(default=None, description="Pricing model")
    qps_budget: Optional[int] = Field(default=None, description="Global QPS budget")
    concurrency_limit: Optional[int] = Field(default=None, description="Max concurrent requests")
    vector_desc: Optional[str] = Field(default=None, description="Description for vector embedding")
    models: Optional[List[str]] = Field(default=None, description="Supported models")
    
    # ... existing methods ...
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_agent_card_model.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/agentmesh/core/agent_card.py tests/test_agent_card_model.py
git commit -m "feat: extend AgentCard with identity and governance fields"
```

---

### Task 2: Implement ID Derivation Logic

**Files:**
- Modify: `src/agentmesh/core/security.py`
- Test: `tests/test_security_identity.py`

**Step 1: Write the failing test**

Create `tests/test_security_identity.py`.

```python
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_security_identity.py -v`
Expected: FAIL (AttributeError: 'SecurityManager' object has no attribute 'derive_agent_id')

**Step 3: Write minimal implementation**

Update `src/agentmesh/core/security.py`:

```python
import hashlib
import base64

class SecurityManager:
    # ... existing methods ...

    def derive_agent_id(self, public_key: str) -> str:
        """Derive Agent ID from public key using SHA256 and Base58-like encoding (or just hex/base64url).
        PRD suggests: base58(sha256(public_key)[:20])
        Let's use a simple hex or base64url for now if base58 lib is not available, 
        or implement simple encoding. Let's use hex for simplicity first as per 'agent_id' constraints (alphanumeric).
        """
        # Clean the key
        key_bytes = public_key.encode('utf-8')
        digest = hashlib.sha256(key_bytes).digest()
        # Take first 20 bytes
        truncated = digest[:20]
        # Encode to hex to ensure it's safe for URLs and IDs
        return truncated.hex()

    def validate_agent_id(self, agent_id: str, public_key: str) -> bool:
        """Validate if the agent_id matches the public_key."""
        expected_id = self.derive_agent_id(public_key)
        return agent_id == expected_id
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_security_identity.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/agentmesh/core/security.py tests/test_security_identity.py
git commit -m "feat: implement agent ID derivation from public key"
```

---

### Task 3: Enforce Signature Verification in Registry

**Files:**
- Modify: `src/agentmesh/core/registry.py`
- Test: `tests/test_registry_enforcement.py`

**Step 1: Write the failing test**

Create `tests/test_registry_enforcement.py`.

```python
import pytest
from unittest.mock import MagicMock, AsyncMock
from agentmesh.core.registry import AgentRegistry, SecurityError
from agentmesh.core.agent_card import AgentCard
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
        manifest_signature=None
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
        manifest_signature="valid-sig"
    )
    
    # Mock verify_signature to return True to isolate ID check
    registry.security_manager.verify_signature = AsyncMock(return_value=True)
    # Mock validate_agent_id to return False
    registry.security_manager.validate_agent_id = MagicMock(return_value=False)
    
    with pytest.raises(SecurityError, match="ID mismatch"):
        await registry.register_agent(card)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_registry_enforcement.py -v`
Expected: FAIL (TypeError: unexpected keyword argument 'require_signed_registration' or no exception raised)

**Step 3: Write minimal implementation**

Update `src/agentmesh/core/registry.py`:

```python
class AgentRegistry:
    def __init__(
        self,
        security_manager: Optional[SecurityManager] = None,
        storage: Optional[StorageBackend] = None,
        sync_interval_seconds: int = 10,
        enable_storage_sync: Optional[bool] = None,
        protocol_gateway: Optional[ProtocolGateway] = None,
        require_signed_registration: bool = False, # New param
    ):
        # ... existing init ...
        self.require_signed_registration = require_signed_registration

    async def register_agent(self, agent_card: AgentCard) -> str:
        self._validate_agent_card(agent_card)

        # Enforce Signature Presence
        if self.require_signed_registration:
            if not agent_card.public_key or not agent_card.manifest_signature:
                raise SecurityError("Signature required for registration")
            
            # Enforce ID Match
            if not self.security_manager.validate_agent_id(agent_card.id, agent_card.public_key):
                raise SecurityError(f"Agent ID mismatch. Expected derived ID from public key.")

        if agent_card.signature or agent_card.manifest_signature:
             # Use manifest_signature if available, fallback to signature (legacy)
             # Note: verify_signature in security_manager likely needs update to handle new fields or use existing logic
             if not await self.security_manager.verify_signature(agent_card):
                raise SecurityError("Agent signature verification failed")

        # ... rest of method ...
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_registry_enforcement.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/agentmesh/core/registry.py tests/test_registry_enforcement.py
git commit -m "feat: enforce signed registration in registry"
```

---

### Task 4: CLI/Main Support for Configuration

**Files:**
- Modify: `src/agentmesh/__main__.py` or `src/agentmesh/cli.py`
- Modify: `src/agentmesh/api/server.py` (if applicable for passing config)

**Step 1: Inspect `src/agentmesh/cli.py` and `src/agentmesh/api/server.py`**

(No test code for this step, manual check in plan execution)

**Step 2: Update CLI to accept `--require-signed-registration`**

Update `src/agentmesh/cli.py` (assuming `serve` command exists there):

```python
@click.option("--require-signed-registration", is_flag=True, help="Enforce signature verification for agent registration")
def serve(..., require_signed_registration):
    # Pass to create_app or server factory
```

Update `src/agentmesh/api/server.py` `create_app` factory to accept this flag and pass to `AgentRegistry`.

**Step 3: Verify with dry-run**

Run `python -m agentmesh serve --help` to see the new option.

**Step 4: Commit**

```bash
git add src/agentmesh/cli.py src/agentmesh/api/server.py
git commit -m "feat: add CLI flag for signed registration enforcement"
```

---

