import logging
import asyncio
from typing import Dict, List, Optional, Set, Any
from .agent_card import AgentCard
from .vector_index import VectorIndexManager

logger = logging.getLogger(__name__)

class DiscoveryService:
    def __init__(self, vector_index: Optional[VectorIndexManager] = None):
        self.vector_index = vector_index
        self.skill_index: Dict[str, Set[str]] = {}
        self.protocol_index: Dict[str, Set[str]] = {}
        self.tag_index: Dict[str, Set[str]] = {}
        self._search_cache: Dict[str, List[Any]] = {}

    def clear_indexes(self):
        self.skill_index.clear()
        self.protocol_index.clear()
        self.tag_index.clear()
        self.clear_cache()

    def clear_cache(self):
        self._search_cache.clear()

    def update_indexes(self, agent_id: str, agent_card: AgentCard) -> None:
        for skill in agent_card.skills:
            self.skill_index.setdefault(skill.name, set()).add(agent_id)

        protocol = agent_card.protocol.value if hasattr(agent_card.protocol, "value") else str(agent_card.protocol)
        self.protocol_index.setdefault(protocol, set()).add(agent_id)

        if agent_card.tags:
            for tag in agent_card.tags:
                self.tag_index.setdefault(tag, set()).add(agent_id)
        
        self.clear_cache()

    def remove_from_indexes(self, agent_id: str, agent_card: AgentCard) -> None:
        for skill in agent_card.skills:
            if skill.name in self.skill_index:
                self.skill_index[skill.name].discard(agent_id)
                if not self.skill_index[skill.name]:
                    del self.skill_index[skill.name]

        protocol = agent_card.protocol.value if hasattr(agent_card.protocol, "value") else str(agent_card.protocol)
        if protocol in self.protocol_index:
            self.protocol_index[protocol].discard(agent_id)
            if not self.protocol_index[protocol]:
                del self.protocol_index[protocol]

        if agent_card.tags:
            for tag in agent_card.tags:
                if tag in self.tag_index:
                    self.tag_index[tag].discard(agent_id)
                    if not self.tag_index[tag]:
                        del self.tag_index[tag]
        
        self.clear_cache()

    async def get_candidates(
        self,
        agents: Dict[str, AgentCard],
        skill_name: Optional[str] = None,
        protocol: Optional[str] = None,
        tags: Optional[List[str]] = None,
        tag: Optional[str] = None,
        q: Optional[str] = None,
    ) -> Set[str]:
        candidate_ids: Optional[Set[str]] = None
        
        if skill_name:
            skill_ids = self.skill_index.get(skill_name, set())
            candidate_ids = skill_ids if candidate_ids is None else candidate_ids.intersection(skill_ids)

        if protocol:
            protocol_key = protocol.value if hasattr(protocol, "value") else str(protocol)
            protocol_ids = self.protocol_index.get(protocol_key, set())
            candidate_ids = protocol_ids if candidate_ids is None else candidate_ids.intersection(protocol_ids)

        tag_filters = list(tags or [])
        if tag:
            tag_filters.append(tag)

        if tag_filters:
            for one_tag in tag_filters:
                tag_ids = self.tag_index.get(one_tag, set())
                candidate_ids = tag_ids if candidate_ids is None else candidate_ids.intersection(tag_ids)

        if candidate_ids is None:
            candidate_ids = set(agents.keys())
            
        return candidate_ids

    async def search(
        self, 
        agents: Dict[str, AgentCard], 
        query: Optional[str], 
        **filters
    ) -> List[Dict[str, Any]]:
        # This will be used by search_agents
        # Logic to be moved from Registry.search_agents
        pass

    async def search_score(self, agent: AgentCard, query: str, trust_score: float = 0.5) -> Any:
        matched_fields: List[str] = []
        semantic_score = 0.0

        name = (agent.name or "").lower()
        description = (agent.description or "").lower()
        skills = [skill.name.lower() for skill in agent.skills]
        skill_desc = [skill.description.lower() for skill in agent.skills]
        tags = [tag.lower() for tag in (agent.tags or [])]

        if query in name:
            semantic_score += 1.0
            matched_fields.append("name")
        if query in description:
            semantic_score += 0.8
            matched_fields.append("description")
        if any(query in skill for skill in skills):
            semantic_score += 0.9
            matched_fields.append("skills")
        if any(query in desc for desc in skill_desc):
            semantic_score += 0.6
            if "skills" not in matched_fields:
                matched_fields.append("skills")
        if any(query in tag for tag in tags):
            semantic_score += 0.7
            matched_fields.append("tags")

        # Factor in Trust (Search Rank Booster)
        trust_booster = 0.8 + (trust_score * 0.4)
        
        final_score = semantic_score * trust_booster

        return final_score, matched_fields
