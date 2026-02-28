# AgentMesh Decentralized Phase 3 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement Semantic Discovery (PR3) for decentralized AgentMesh, allowing agents to be found via natural language queries using vector embeddings and trust scores.

**Architecture:** 
- Add `vector_desc` field to `AgentCard` for embedding generation.
- Integrate `sentence-transformers` for local embedding generation.
- Integrate `faiss-cpu` (or `numpy` for MVP) for vector similarity search.
- Implement `VectorIndexManager` to maintain the index.
- Expose `/agents/discover` endpoint for semantic search.
- Update `agentmesh discover` CLI command.

**Tech Stack:** Python 3.10+, sentence-transformers, faiss-cpu/numpy, FastAPI.

---

### Task 1: Update AgentCard & Dependencies

**Files:**
- Modify: `pyproject.toml` (add optional dependencies)
- Modify: `src/agentmesh/core/agent_card.py`
- Test: `tests/test_agent_card_semantic.py`

**Step 1: Update dependencies**

Add `sentence-transformers` and `numpy` to `pyproject.toml` (optional group `semantic`).
For MVP, we might skip `faiss` and use `numpy` for simplicity if dataset is small, or just add `faiss-cpu`.
Let's add `sentence-transformers` and `faiss-cpu`.

**Step 2: Write failing test for AgentCard**

Create `tests/test_agent_card_semantic.py`:

```python
import pytest
from agentmesh.core.agent_card import AgentCard

def test_agent_card_vector_fields():
    card = AgentCard(
        id="test-1",
        name="Test",
        version="1.0",
        endpoint="http://localhost",
        vector_desc="A test agent for vector search",
        capabilities=["search", "vector"]
    )
    assert card.vector_desc == "A test agent for vector search"
    assert "search" in card.capabilities
```

**Step 3: Run test (Fail)**

**Step 4: Update AgentCard**

Add fields to `AgentCard`:
- `vector_desc`: Optional[str]
- `capabilities`: Optional[List[str]]

**Step 5: Run test (Pass)**

---

### Task 2: Vector Index Manager (MVP with NumPy)

**Files:**
- Create: `src/agentmesh/core/vector_index.py`
- Test: `tests/test_vector_index.py`

**Step 1: Write failing test**

Create `tests/test_vector_index.py`.

```python
import pytest
from unittest.mock import MagicMock, patch
from agentmesh.core.vector_index import VectorIndexManager
from agentmesh.core.agent_card import AgentCard

@pytest.mark.asyncio
async def test_vector_index_add_search():
    # Mock embedding model to avoid loading heavy model in tests
    with patch("sentence_transformers.SentenceTransformer") as MockModel:
        mock_model = MockModel.return_value
        # Mock encode to return fixed vector
        mock_model.encode.return_value = [0.1, 0.2, 0.3]
        
        manager = VectorIndexManager()
        
        agent = AgentCard(
            id="a1", name="A", version="1", endpoint="http://a",
            vector_desc="test agent"
        )
        
        await manager.add_agent(agent)
        
        # Search
        results = await manager.search("query", top_k=1)
        assert len(results) == 1
        assert results[0].agent_id == "a1"
        assert results[0].score > 0
```

**Step 2: Run test (Fail)**

**Step 3: Implement VectorIndexManager**

Create `src/agentmesh/core/vector_index.py`.
- Use `sentence-transformers` if available, else mock/warn.
- Maintain a list of vectors and IDs.
- Implement `search` using cosine similarity (dot product of normalized vectors).

**Step 4: Run test (Pass)**

---

### Task 3: Integrate with Registry & API

**Files:**
- Modify: `src/agentmesh/core/registry.py` (hooks)
- Modify: `src/agentmesh/api/server.py` (init)
- Modify: `src/agentmesh/api/routes.py` (endpoint)
- Test: `tests/test_discovery_api.py`

**Step 1: Write failing test for API**

Create `tests/test_discovery_api.py`.

**Step 2: Run test (Fail)**

**Step 3: Integrate Registry Hooks**

Update `AgentRegistry` to call `VectorIndexManager.add_agent` on registration.
Or better, `AgentMeshServer` orchestrates this?
Actually, `AgentRegistry` should probably have an optional `vector_index` dependency.

**Step 4: Add /agents/discover Endpoint**

Add `GET /agents/discover?q=...` to `routes.py`.

**Step 5: Run test (Pass)**

---

### Task 4: CLI Support

**Files:**
- Modify: `src/agentmesh/cli.py`
- Modify: `src/agentmesh/client.py`

**Step 1: Update Client**

Add `discover_agents(query, limit)` to `SyncAgentMeshClient`.

**Step 2: Update CLI**

Add `discover` command to `cli.py`.

**Step 3: Manual Verify**

Run `agentmesh discover --query "weather"` (mocking server).
