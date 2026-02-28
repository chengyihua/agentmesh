import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from agentmesh.core.vector_index import VectorIndexManager
from agentmesh.core.agent_card import AgentCard

@pytest.mark.asyncio
async def test_vector_index_add_search():
    # Mock embedding model to avoid loading heavy model in tests
    with patch("sentence_transformers.SentenceTransformer") as MockModel:
        mock_model = MockModel.return_value
        # Mock encode to return fixed vector
        # Using numpy to ensure it's a vector of floats
        mock_model.encode.return_value = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        
        manager = VectorIndexManager()
        
        agent = AgentCard(
            id="a1", 
            name="A", 
            version="1", 
            endpoint="http://a",
            skills=[{"name": "test", "description": "test"}],
            vector_desc="test agent"
        )
        
        await manager.add_agent(agent)
        
        # Search
        results = await manager.search("query", top_k=1)
        assert len(results) == 1
        assert results[0]["agent_id"] == "a1"
        assert results[0]["score"] > 0
