import logging
import numpy as np
import asyncio
from typing import List, Dict, Any, Optional
from agentmesh.core.agent_card import AgentCard

logger = logging.getLogger(__name__)

class VectorIndexManager:
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        self.model_name = model_name
        self._model = None
        self.vectors: List[np.ndarray] = []
        self.agent_ids: List[str] = []

    @property
    def model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                # Suppress huggingface logs
                logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                logger.warning("sentence-transformers not installed. Vector search disabled.")
                self._model = None
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                self._model = None
        return self._model

    async def add_agent(self, agent: AgentCard):
        """Add or update an agent in the vector index."""
        if not self.model:
            return
            
        # Construct text representation
        # Priority: vector_desc > description > name
        text = agent.vector_desc or agent.description or agent.name
        if not text:
            return
            
        # Combine capabilities if available
        if agent.capabilities:
            text += " " + " ".join(agent.capabilities)
            
        # Encode
        try:
            loop = asyncio.get_running_loop()
            vector = await loop.run_in_executor(None, self.model.encode, text)
            
            # Normalize for cosine similarity
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
                
            # Update or Insert
            if agent.id in self.agent_ids:
                idx = self.agent_ids.index(agent.id)
                self.vectors[idx] = vector
            else:
                self.vectors.append(vector)
                self.agent_ids.append(agent.id)
        except Exception as e:
            logger.error(f"Error adding agent {agent.id} to vector index: {e}")

    async def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search for agents semantically."""
        if not self.model or not self.vectors:
            return []
            
        try:
            loop = asyncio.get_running_loop()
            query_vector = await loop.run_in_executor(None, self.model.encode, query)
            
            # Normalize
            norm = np.linalg.norm(query_vector)
            if norm > 0:
                query_vector = query_vector / norm
                
            # Compute scores (dot product)
            matrix = np.stack(self.vectors)
            scores = np.dot(matrix, query_vector)
            
            # Sort indices descending
            top_indices = np.argsort(scores)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                results.append({
                    "agent_id": self.agent_ids[idx],
                    "score": float(scores[idx])
                })
                
            return results
        except Exception as e:
            logger.error(f"Error during vector search: {e}")
            return []
