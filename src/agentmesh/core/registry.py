"""Agent registry core service."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from ..relay.manager import RelayManager

from .agent_card import AgentCard, AgentCardUpdate, HealthStatus
from .security import SecurityManager
from .vector_index import VectorIndexManager
from .trust import TrustManager, TrustEvent
from .negotiation import NegotiationManager
from .pow import PoWManager
from ..protocols import InvocationRequest, ProtocolGateway, ProtocolInvocationError
from ..storage import MemoryStorage, StorageBackend

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Security related errors."""


class AgentRegistry:
    """Registry for agent cards and discovery operations."""

    def __init__(
        self,
        security_manager: Optional[SecurityManager] = None,
        storage: Optional[StorageBackend] = None,
        sync_interval_seconds: int = 10,
        enable_storage_sync: Optional[bool] = None,
        protocol_gateway: Optional[ProtocolGateway] = None,
        require_signed_registration: bool = False,
        vector_index: Optional[VectorIndexManager] = None,
        telemetry: Any = None,
    ):
        """Initialize registry with security manager and storage backend."""
        self.agents: Dict[str, AgentCard] = {}
        self.skill_index: Dict[str, Set[str]] = {}
        self.protocol_index: Dict[str, Set[str]] = {}
        self.tag_index: Dict[str, Set[str]] = {}

        self.require_signed_registration = require_signed_registration
        self.security_manager = security_manager or SecurityManager()
        self.storage = storage or MemoryStorage()
        self.protocol_gateway = protocol_gateway or ProtocolGateway()
        self.vector_index = vector_index
        self.trust_manager = TrustManager(self)
        self.telemetry = telemetry
        self.relay_manager: Optional["RelayManager"] = None
        self.negotiation_manager = NegotiationManager()
        self.pow_manager = PoWManager()

        self.health_check_interval = 30
        self.max_unhealthy_time = 300
        self.prune_timeout = 3600  # 1 hour
        self.min_trust_score = 0.2
        self._health_check_task: Optional[asyncio.Task] = None
        self._sync_task: Optional[asyncio.Task] = None
        self._sync_interval_seconds = max(1, sync_interval_seconds)
        if enable_storage_sync is None:
            self._enable_storage_sync = not isinstance(self.storage, MemoryStorage)
        else:
            self._enable_storage_sync = enable_storage_sync
        self._started_at = datetime.now(timezone.utc)
        self._state_lock = asyncio.Lock()

        self._search_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._agent_metrics: Dict[str, Dict[str, Any]] = {}

        logger.info("AgentRegistry initialized")

    async def start(self):
        """Start registry tasks and load persisted agents."""
        await self.storage.connect()
        await self._load_from_storage()
        await self.trust_manager.start()
        if self._health_check_task is None:
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            logger.info("Health check loop started")
        if self._enable_storage_sync and self._sync_task is None:
            self._sync_task = asyncio.create_task(self._storage_sync_loop())
            logger.info("Storage sync loop started")

    async def stop(self):
        """Stop registry tasks and close storage."""
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
            self._sync_task = None
            logger.info("Storage sync loop stopped")
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            self._health_check_task = None
            logger.info("Health check loop stopped")
        
        await self.trust_manager.stop()
        await self.storage.close()

    async def _load_from_storage(self) -> None:
        await self._sync_from_storage(force=True)

    def _snapshot(self, agents: Dict[str, AgentCard]) -> Dict[str, str]:
        return {
            agent_id: agent.updated_at.astimezone(timezone.utc).isoformat()
            for agent_id, agent in agents.items()
        }

    async def _sync_from_storage(self, force: bool = False) -> bool:
        stored_agents = await self.storage.list_agents(skip=0, limit=100000)
        stored_map = {agent.id: agent for agent in stored_agents}

        async with self._state_lock:
            if not force and self._snapshot(self.agents) == self._snapshot(stored_map):
                return False

            self.agents = stored_map
            self._rebuild_indexes()
            
            if self.vector_index:
                # Rebuild vector index
                # We do this asynchronously but we need to ensure it's eventually consistent
                # For simplicity, we just trigger tasks
                for agent in stored_agents:
                    asyncio.create_task(self.vector_index.add_agent(agent))

            for agent in stored_agents:
                self._agent_metrics.setdefault(
                    agent.id,
                    {
                        "discoveries": 0,
                        "health_checks": 0,
                        "heartbeats": 0,
                        "invocations": 0,
                        "failed_invocations": 0,
                        "latency_sum": 0.0,
                        "latency_count": 0,
                        "uptime_streak": 0,
                        "registered_at": agent.created_at,
                    },
                )

            for agent_id in list(self._agent_metrics.keys()):
                if agent_id not in self.agents:
                    self._agent_metrics.pop(agent_id, None)

            self._search_cache.clear()
            return True

    def _rebuild_indexes(self) -> None:
        self.skill_index.clear()
        self.protocol_index.clear()
        self.tag_index.clear()
        for agent_id, agent_card in self.agents.items():
            self._update_indexes(agent_id, agent_card)

    async def register_agent(self, agent_card: AgentCard) -> str:
        self._validate_agent_card(agent_card)

        # Enforce ID derivation if public key is present (Phase 1 Requirement)
        if agent_card.public_key:
             if not self.security_manager.validate_agent_id(agent_card.id, agent_card.public_key):
                 raise SecurityError(f"Agent ID '{agent_card.id}' does not match derived ID from public key")

        # Enforce Signature Presence
        if self.require_signed_registration:
            if not agent_card.public_key or not agent_card.manifest_signature:
                raise SecurityError("Signature required for registration")
            
            # Enforce ID Match
            if not self.security_manager.validate_agent_id(agent_card.id, agent_card.public_key):
                raise SecurityError(f"Agent ID mismatch. Expected derived ID from public key.")

        if agent_card.signature or agent_card.manifest_signature:
            is_valid = await self.security_manager.verify_signature(agent_card)
            
            if self.telemetry:
                # Simple algorithm detection for telemetry
                algo = "unknown"
                if agent_card.manifest_signature and agent_card.manifest_signature.startswith("ed25519:"):
                    algo = "ed25519"
                elif agent_card.signature and agent_card.signature.startswith("rsa:"):
                    algo = "rsa"
                    
                self.telemetry.signature_verifications.labels(
                    status="valid" if is_valid else "invalid", 
                    algorithm=algo
                ).inc()
                
            if not is_valid:
                raise SecurityError("Agent signature verification failed")

        async with self._state_lock:
            if agent_card.id in self.agents:
                raise ValueError(f"Agent ID '{agent_card.id}' already exists")

            # Calculate Species ID based on skills (deterministic)
            skills_data = [s.model_dump() if hasattr(s, 'model_dump') else s for s in agent_card.skills]
            skills_json = json.dumps(sorted(skills_data, key=lambda x: x.get('name', '')), sort_keys=True)
            agent_card.species_id = hashlib.sha256(skills_json.encode()).hexdigest()

            # Generate Claim Code for orphaned nodes
            if not agent_card.owner_id:
                alphabet = string.ascii_uppercase + string.digits
                agent_card.claim_code = f"{''.join(secrets.choice(alphabet) for _ in range(4))}-{''.join(secrets.choice(alphabet) for _ in range(4))}"
                logger.info("Generated claim code for orphaned agent %s: %s", agent_card.id, agent_card.claim_code)

            now = datetime.now(timezone.utc)
            agent_card.created_at = now
            agent_card.updated_at = now

            self.agents[agent_card.id] = agent_card
            self._update_indexes(agent_card.id, agent_card)
            
            if self.vector_index:
                # Update vector index asynchronously to avoid blocking
                asyncio.create_task(self.vector_index.add_agent(agent_card))
                
            await self.storage.upsert_agent(agent_card)

            self._agent_metrics[agent_card.id] = {
                "discoveries": 0,
                "health_checks": 0,
                "heartbeats": 0,
                "invocations": 0,
                "failed_invocations": 0,
                "latency_sum": 0.0,
                "latency_count": 0,
                "uptime_streak": 0,
                "registered_at": now,
            }
            self._search_cache.clear()
            
            if self.telemetry:
                self.telemetry.agent_registrations.labels(status="success").inc()
                self.telemetry.active_agents.set(len(self.agents))

        logger.info("Agent registered: %s", agent_card.id)
        return agent_card.id

    async def claim_agent(self, agent_id: str, claim_code: str, owner_id: str) -> bool:
        """Claim an orphaned agent using a claim code."""
        async with self._state_lock:
            if agent_id not in self.agents:
                raise ValueError(f"Agent '{agent_id}' not found")

            agent = self.agents[agent_id]
            if agent.owner_id:
                raise ValueError(f"Agent '{agent_id}' is already claimed by {agent.owner_id}")

            if not agent.claim_code or agent.claim_code != claim_code:
                raise ValueError("Invalid claim code")

            agent.owner_id = owner_id
            agent.claim_code = None  # Clear the code after claim
            agent.update_timestamp()

            await self.storage.upsert_agent(agent)
            self._search_cache.clear()

        logger.info("Agent %s claimed by owner %s", agent_id, owner_id)
        return True

    async def update_agent(self, agent_id: str, update_data: AgentCardUpdate) -> bool:
        async with self._state_lock:
            if agent_id not in self.agents:
                raise ValueError(f"Agent ID '{agent_id}' does not exist")

            agent_card = self.agents[agent_id]
            self._remove_from_indexes(agent_id, agent_card)

            for field, value in update_data.model_dump(exclude_none=True).items():
                if hasattr(agent_card, field):
                    setattr(agent_card, field, value)

            agent_card.update_timestamp()
            self._update_indexes(agent_id, agent_card)
            await self.storage.upsert_agent(agent_card)

            # Record trust event for profile update
            if self.trust_manager:
                await self.trust_manager.record_event(agent_id, TrustEvent.PROFILE_UPDATE)

            self._search_cache.clear()
        return True

    async def deregister_agent(self, agent_id: str) -> bool:
        async with self._state_lock:
            if agent_id not in self.agents:
                return False

            agent_card = self.agents[agent_id]
            self._remove_from_indexes(agent_id, agent_card)
            del self.agents[agent_id]

            await self.storage.delete_agent(agent_id)
            self._agent_metrics.pop(agent_id, None)
            self._search_cache.clear()
            
            if self.telemetry:
                self.telemetry.active_agents.set(len(self.agents))
        return True

    async def get_agent(self, agent_id: str) -> Optional[AgentCard]:
        agent = self.agents.get(agent_id)
        if agent is not None:
            return agent

        # Fallback for storage out-of-sync situations.
        agent = await self.storage.get_agent(agent_id)
        if agent is not None:
            async with self._state_lock:
                existing = self.agents.get(agent_id)
                if existing is not None:
                    return existing
                self.agents[agent_id] = agent
                self._update_indexes(agent_id, agent)
                self._agent_metrics.setdefault(
                    agent_id,
                    {
                        "discoveries": 0,
                        "health_checks": 0,
                        "heartbeats": 0,
                        "invocations": 0,
                        "failed_invocations": 0,
                        "registered_at": agent.created_at,
                    },
                )
                self._search_cache.clear()
        return agent

    async def list_agents(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        sort_by: str = "updated_at", 
        order: str = "desc"
    ) -> List[AgentCard]:
        """List agents with pagination and sorting."""
        
        # Pre-calculate trust scores if sorting by trust
        if sort_by == "trust_score":
            for agent in self.agents.values():
                if agent.trust_score is None: # Optimization: avoid recalc if cached/fresh
                     agent.trust_score = await self.calculate_trust_score(agent.id)

        # Define sort key
        def get_sort_key(agent):
            if sort_by == "trust_score":
                return agent.trust_score or 0.0
            elif sort_by == "updated_at":
                return agent.updated_at.timestamp()
            elif sort_by == "created_at":
                return agent.created_at.timestamp()
            return 0.0
             
        reverse = (order.lower() == "desc")
        
        agents = sorted(self.agents.values(), key=get_sort_key, reverse=reverse)
        paginated = agents[skip : skip + limit]
        
        # Ensure trust score is calculated for returned agents (if not already done)
        if sort_by != "trust_score":
            for agent in paginated:
                agent.trust_score = await self.calculate_trust_score(agent.id)
            
        return paginated

    async def discover_agents(
        self,
        skill_name: Optional[str] = None,
        protocol: Optional[str] = None,
        tags: Optional[List[str]] = None,
        tag: Optional[str] = None,
        q: Optional[str] = None,
        healthy_only: bool = True,
        min_trust: Optional[float] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> List[AgentCard]:
        candidate_ids: Optional[Set[str]] = None
        
        if self.telemetry:
            # Simple heuristic for metric labeling
            discovery_type = "keyword"
            if q and not skill_name and not protocol and not tags:
                discovery_type = "semantic" if self.vector_index else "keyword"
            elif skill_name:
                discovery_type = "skill"
            elif protocol:
                discovery_type = "protocol"
            elif tags:
                discovery_type = "tag"
            elif not q and not skill_name and not protocol and not tags:
                discovery_type = "all"
            self.telemetry.agent_discovery_requests.labels(type=discovery_type).inc()

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
            candidate_ids = set(self.agents.keys())

        agents: List[AgentCard] = []
        query = (q or "").strip().lower()

        for agent_id in candidate_ids:
            agent = self.agents.get(agent_id)
            if agent is None:
                continue

            # Ensure trust score is up-to-date
            agent.trust_score = await self.calculate_trust_score(agent_id)
            
            if min_trust is not None and agent.trust_score < min_trust:
                continue

            if healthy_only and agent.health_status != HealthStatus.HEALTHY:
                continue
            if query and not await self._matches_query(agent, query):
                continue
            agents.append(agent)

        agents.sort(key=lambda x: x.updated_at, reverse=True)

        for agent in agents:
            metrics = self._agent_metrics.setdefault(agent.id, {"discoveries": 0, "health_checks": 0, "heartbeats": 0})
            metrics["discoveries"] = metrics.get("discoveries", 0) + 1
            agent.trust_score = await self.calculate_trust_score(agent.id)
        return agents[offset : offset + limit]

    async def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the top-performing agents based on trust and activity."""
        leaderboard = []
        
        for agent_id, agent in self.agents.items():
            trust_score = await self.calculate_trust_score(agent_id)
            metrics = self._agent_metrics.get(agent_id, {})
            
            # Activity factor: total interactions
            heartbeats = metrics.get("heartbeats", 0)
            invocations = metrics.get("invocations", 0)
            activity_score = min(1.0, (heartbeats + (invocations * 5)) / 1000.0)
            
            # Weighted combo
            composite_score = (trust_score * 0.7) + (activity_score * 0.3)
            
            tier = "Bronze"
            if composite_score >= 0.9:
                tier = "Gold"
            elif composite_score >= 0.7:
                tier = "Silver"
                
            leaderboard.append({
                "agent_id": agent_id,
                "name": agent.name,
                "trust_score": round(trust_score, 3),
                "composite_score": round(composite_score, 3),
                "tier": tier,
                "metrics": {
                    "heartbeats": heartbeats,
                    "invocations": invocations
                }
            })
            
        leaderboard.sort(key=lambda x: x["composite_score"], reverse=True)
        return leaderboard[:limit]

    async def search_agents(
        self,
        q: Optional[str],
        skill_name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        protocol: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        healthy_only: bool = False,
        min_trust: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        query = q.strip().lower() if q else ""
        
        cache_key = f"q={query}|skill={skill_name}|tags={tags}|protocol={protocol}|limit={limit}|offset={offset}|healthy={healthy_only}|trust={min_trust}"
        if cache_key in self._search_cache:
            return self._search_cache[cache_key]

        # Get base candidates filtered by metadata (skills, tags, protocol)
        # We pass q=None so we don't filter by keywords yet, allowing vector search to find semantic matches
        candidates = await self.discover_agents(
            skill_name=skill_name,
            protocol=protocol,
            tags=tags,
            healthy_only=healthy_only,
            min_trust=min_trust,
            q=None,
            limit=10000,
            offset=0,
        )
        
        candidate_map = {a.id: a for a in candidates}
        scored_agents: Dict[str, Dict[str, Any]] = {}

        # 1. Vector Search (if available and query exists)
        if self.vector_index and query:
            try:
                # Request more than limit to allow for intersection with candidates
                vector_results = await self.vector_index.search(query, top_k=max(50, limit * 2))
                for res in vector_results:
                    aid = res["agent_id"]
                    if aid in candidate_map:
                        # Vector scores are 0-1. Scale up to match keyword scoring magnitude.
                        # Using 3.0 multiplier to make strong semantic matches comparable to strong keyword matches.
                        scored_agents[aid] = {
                            "score": res["score"] * 3.0,
                            "matched_fields": ["vector_embedding"]
                        }
            except Exception as e:
                logger.error(f"Vector search failed in search_agents: {e}")

        # 2. Keyword Search & Merging
        final_results = []
        
        for agent in candidates:
            # Keyword score
            if query:
                keyword_score, matched_fields = await self._search_score(agent, query)
            else:
                keyword_score, matched_fields = 0.0, []
            
            # Vector score
            vector_data = scored_agents.get(agent.id, {"score": 0.0, "matched_fields": []})
            vector_score = vector_data["score"]
            vector_fields = vector_data["matched_fields"]
            
            total_score = keyword_score + vector_score
            
            # If query is present, filter out zero scores
            if query and total_score <= 0:
                continue
            
            # If query is missing, treat as match (filtered by metadata)
            if not query:
                total_score = 1.0
                
            all_matched_fields = list(set(matched_fields + vector_fields))
            
            final_results.append({
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "score": round(total_score, 3),
                "matched_fields": all_matched_fields,
                "vector_score": round(vector_score, 3),
                "keyword_score": round(keyword_score, 3)
            })

        final_results.sort(key=lambda x: x["score"], reverse=True)
        sliced = final_results[offset : offset + limit]
        self._search_cache[cache_key] = sliced
        return sliced

    async def match_capability(self, q: str) -> Optional[Dict[str, Any]]:
        """Find the single best matching agent for a given capability query."""
        results = await self.search_agents(
            q, 
            limit=1, 
            healthy_only=True, 
            min_trust=self.min_trust_score
        )
        if not results:
            return None
        
        best = results[0]
        agent = await self.get_agent(best["id"])
        if not agent:
            return None
            
        return {
            "agent": {
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "protocol": agent.protocol.value if hasattr(agent.protocol, "value") else str(agent.protocol),
                "endpoint": str(agent.endpoint),
                "skills": [s.name for s in agent.skills],
            },
            "score": best["score"],
            "reason": f"Matches query '{q}' with score {best['score']}.",
            "suggestion": f"I found '{agent.name}' which matches your requirement. You can invoke it via {agent.protocol.value} at {agent.endpoint}.",
            "action_instructions": {
                "step_1": f"POST /api/v1/agents/{agent.id}/negotiate with your task proposal.",
                "step_2": f"If feasible, POST /api/v1/agents/{agent.id}/invoke with your specific payload.",
                "sample_negotiation": {
                    "url": f"/api/v1/agents/{agent.id}/negotiate",
                    "payload": {"proposal": "I need help with [task_description]"}
                }
            }
        }

    async def negotiate_capability(
        self, 
        agent_id: str, 
        proposal: str, 
        session_id: Optional[str] = None,
        action: Optional[str] = None
    ) -> Dict[str, Any]:
        """Negotiate capability usage with a specific agent based on a task proposal."""
        agent = await self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent '{agent_id}' not found")

        # If session_id provided, continue existing negotiation
        if session_id:
            try:
                # Process the next step in the negotiation
                # For now, we simulate auto-acceptance if the action is "accept"
                # In a real implementation, this would involve agent interaction
                session = self.negotiation_manager.process_round(
                    session_id, 
                    action or "counter", 
                    content=proposal
                )
                return session.dict()
            except ValueError as e:
                # If session not found or invalid transition
                raise ValueError(str(e))

        # Start new negotiation
        # Simulate negotiation logic: Check if the proposal keywords match any agent skills/description
        proposal_lower = proposal.lower()
        matched_skills = [s.name for s in agent.skills if s.name.lower() in proposal_lower]
        
        # Feasibility check
        is_feasible = len(matched_skills) > 0 or any(word in (agent.description or "").lower() for word in proposal_lower.split())
        
        confidence = 0.9 if len(matched_skills) > 0 else (0.5 if is_feasible else 0.1)
        
        # Create session
        session = self.negotiation_manager.create_session(agent_id, proposal)
        
        # If highly feasible, auto-accept (simulate)
        # In real world, this would be "PROPOSED" waiting for agent response
        if confidence > 0.8:
            session.status = "agreed"
            session.commitment = {"confidence": confidence, "valid_until": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()}
        elif is_feasible:
            session.status = "proposed"
            session.history.append({"sender": "system", "content": "Proposal received, waiting for agent confirmation."})
        else:
            session.status = "rejected"
            session.history.append({"sender": "system", "content": "Proposal deemed not feasible based on agent profile."})

        result = session.dict()
        result.update({
            "feasible": is_feasible,
            "confidence": confidence,
            "matched_skills": matched_skills,
            "instructions": "Proceed to /invoke if agreed, or continue negotiation with session_id." if is_feasible else "The agent might not be suitable for this task."
        })
        
        return result

    async def heartbeat(
        self,
        agent_id: str,
        status: HealthStatus = HealthStatus.HEALTHY,
        timestamp: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        agent = await self.get_agent(agent_id)
        if agent is None:
            raise ValueError(f"Agent '{agent_id}' not found")

        now = timestamp or datetime.now(timezone.utc)
        async with self._state_lock:
            agent.health_status = status
            agent.last_health_check = now
            agent.last_heartbeat = now
            agent.updated_at = now
            await self.storage.upsert_agent(agent)

            metrics = self._agent_metrics.setdefault(
                agent_id,
                {
                    "discoveries": 0,
                    "health_checks": 0,
                    "heartbeats": 0,
                    "invocations": 0,
                    "failed_invocations": 0,
                },
            )
            metrics["heartbeats"] = metrics.get("heartbeats", 0) + 1
            if status == HealthStatus.HEALTHY:
                metrics["uptime_streak"] = metrics.get("uptime_streak", 0) + 1
            else:
                metrics["uptime_streak"] = 0

        # Record Trust Event: Heartbeat
        await self.trust_manager.record_event(agent_id, TrustEvent.HEARTBEAT)

        return {
            "agent_id": agent_id,
            "status": status.value,
            "timestamp": now.isoformat(),
            "next_check": (now + timedelta(seconds=self.health_check_interval)).isoformat(),
        }

    async def check_agent_health(self, agent_id: str) -> HealthStatus:
        agent = await self.get_agent(agent_id)
        if agent is None:
            return HealthStatus.UNKNOWN

        async with self._state_lock:
            metrics = self._agent_metrics.setdefault(
                agent_id,
                {
                    "discoveries": 0,
                    "health_checks": 0,
                    "heartbeats": 0,
                    "invocations": 0,
                    "failed_invocations": 0,
                },
            )
            metrics["health_checks"] = metrics.get("health_checks", 0) + 1

            if agent.last_health_check is not None:
                delta = datetime.now(timezone.utc) - agent.last_health_check.astimezone(timezone.utc)
                if delta.total_seconds() > self.max_unhealthy_time:
                    agent.set_health_status(HealthStatus.UNHEALTHY)
                    await self.storage.upsert_agent(agent)

        return agent.health_status

    async def batch_health_check(self, agent_ids: List[str]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for agent_id in agent_ids:
            status = await self.check_agent_health(agent_id)
            results.append(
                {
                    "agent_id": agent_id,
                    "health_status": status.value,
                    "status": "success",
                }
            )
        return results

    async def calculate_trust_score(self, agent_id: str) -> float:
        """
        Calculate trust score using TrustManager (v2 logic).
        """
        return await self.trust_manager.get_score(agent_id)

    async def get_trust_breakdown(self, agent_id: str) -> Dict[str, Any]:
        """Get the individual components of the trust score."""
        return await self.trust_manager.get_breakdown(agent_id)

    async def get_agent_stats(self, agent_id: str) -> Dict[str, Any]:
        agent = await self.get_agent(agent_id)
        if agent is None:
            raise ValueError(f"Agent '{agent_id}' not found")

        metrics = self._agent_metrics.setdefault(
            agent_id,
            {
                "discoveries": 0,
                "health_checks": 0,
                "heartbeats": 0,
                "invocations": 0,
                "failed_invocations": 0,
            },
        )

        # Calculate Rank (Dynamic)
        all_scores = []
        for aid, a in self.agents.items():
            t_score = await self.calculate_trust_score(aid)
            m = self._agent_metrics.get(aid, {})
            h = m.get("heartbeats", 0)
            i = m.get("invocations", 0)
            # Same formula as leaderboard
            act_score = min(1.0, (h + (i * 5)) / 1000.0)
            comp_score = (t_score * 0.7) + (act_score * 0.3)
            all_scores.append({"id": aid, "score": comp_score})
            
        all_scores.sort(key=lambda x: x["score"], reverse=True)
        
        rank = -1
        for idx, item in enumerate(all_scores):
            if item["id"] == agent_id:
                rank = idx + 1
                break
        
        percentile = 0.0
        if len(all_scores) > 1 and rank > 0:
            percentile = (len(all_scores) - rank) / (len(all_scores) - 1) * 100
        elif len(all_scores) == 1:
            percentile = 100.0

        # Find this agent's composite score from the sorted list
        my_composite_score = 0.0
        for item in all_scores:
            if item["id"] == agent_id:
                my_composite_score = item["score"]
                break

        return {
            "agent_id": agent.id,
            "name": agent.name,
            "health_status": agent.health_status.value,
            "trust_score": await self.calculate_trust_score(agent.id),
            "rank": rank,
            "percentile": round(percentile, 1),
            "total_agents": len(all_scores),
            "contribution_score": round(my_composite_score, 4),
            "trust_breakdown": await self.get_trust_breakdown(agent.id),
            "last_seen": (agent.last_health_check or agent.updated_at).isoformat(),
            "discoveries": metrics.get("discoveries", 0),
            "health_checks": metrics.get("health_checks", 0),
            "heartbeats": metrics.get("heartbeats", 0),
            "invocations": metrics.get("invocations", 0),
            "failed_invocations": metrics.get("failed_invocations", 0),
            "skills_count": len(agent.skills),
            "tags_count": len(agent.tags or []),
            "protocol": agent.protocol.value if hasattr(agent.protocol, "value") else str(agent.protocol),
        }

    async def invoke_agent(
        self,
        agent_id: str,
        *,
        skill: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        path: Optional[str] = None,
        method: str = "POST",
        timeout_seconds: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        agent = await self.get_agent(agent_id)
        if agent is None:
            raise ValueError(f"Agent '{agent_id}' not found")

        request = InvocationRequest(
            agent_id=agent.id,
            endpoint=str(agent.endpoint),
            protocol=agent.protocol.value if hasattr(agent.protocol, "value") else str(agent.protocol),
            skill=skill,
            payload=payload or {},
            path=path,
            method=method,
            timeout_seconds=timeout_seconds,
            headers=headers or {},
        )

        try:
            start_time = datetime.now(timezone.utc)
            result = await self.protocol_gateway.invoke(agent, request)
            
            # Record success metrics (latency)
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            async with self._state_lock:
                metrics = self._agent_metrics.setdefault(agent_id, {})
                metrics["invocations"] = metrics.get("invocations", 0) + 1
                
                # Update latency moving average (simplified)
                current_sum = metrics.get("latency_sum", 0.0)
                current_count = metrics.get("latency_count", 0)
                metrics["latency_sum"] = current_sum + duration
                metrics["latency_count"] = current_count + 1
            
            if result.ok:
                # Record Trust Event: Successful Invocation
                await self.trust_manager.record_event(agent_id, TrustEvent.SUCCESS)
                
                if self.telemetry:
                    self.telemetry.agent_invocations.labels(
                        agent_id=agent_id,
                        protocol=request.protocol,
                        status="success"
                    ).inc()
            else:
                # Record Trust Event: Failed Invocation (result not ok)
                await self.trust_manager.record_event(agent_id, TrustEvent.FAILURE)
                
                async with self._state_lock:
                    metrics = self._agent_metrics.setdefault(agent_id, {})
                    metrics["failed_invocations"] = metrics.get("failed_invocations", 0) + 1

                if self.telemetry:
                    self.telemetry.agent_invocations.labels(
                        agent_id=agent_id,
                        protocol=request.protocol,
                        status="failure"
                    ).inc()

            return result.to_dict()
            
        except Exception as e:
            # Record failure metrics
            async with self._state_lock:
                metrics = self._agent_metrics.setdefault(agent_id, {})
                metrics["failed_invocations"] = metrics.get("failed_invocations", 0) + 1
            
            # Record Trust Event: Failed Invocation
            await self.trust_manager.record_event(agent_id, TrustEvent.FAILURE)
            
            if self.telemetry:
                self.telemetry.agent_invocations.labels(
                    agent_id=agent_id,
                    protocol=request.protocol,
                    status="failure"
                ).inc()

            if isinstance(e, ProtocolInvocationError):
                raise
            raise ProtocolInvocationError(f"Invocation failed: {str(e)}") from e

    async def clear_cache(self) -> Dict[str, Any]:
        async with self._state_lock:
            cache_size = len(self._search_cache)
            self._search_cache.clear()
        return {
            "cleared_at": datetime.now(timezone.utc).isoformat(),
            "cache_entries": cache_size,
        }

    def get_stats(self) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        storage_backend = self.storage.__class__.__name__.replace("Storage", "").lower()

        # Calculate protocol distribution
        protocol_dist = {}
        for agent in self.agents.values():
            p = agent.protocol.value if hasattr(agent.protocol, "value") else str(agent.protocol)
            protocol_dist[p] = protocol_dist.get(p, 0) + 1

        return {
            "total_agents": len(self.agents),
            "total_skills": len(self.skill_index),
            "total_protocols": len(self.protocol_index),
            "total_tags": len(self.tag_index),
            "healthy_agents": sum(1 for a in self.agents.values() if a.health_status == HealthStatus.HEALTHY),
            "unhealthy_agents": sum(1 for a in self.agents.values() if a.health_status == HealthStatus.UNHEALTHY),
            "unknown_agents": sum(1 for a in self.agents.values() if a.health_status == HealthStatus.UNKNOWN),
            "protocol_distribution": protocol_dist,
            "storage_backend": storage_backend,
            "uptime_seconds": int((now - self._started_at).total_seconds()),
            "cached_searches": len(self._search_cache),
            "storage_sync_enabled": self._enable_storage_sync,
            "storage_sync_interval_seconds": self._sync_interval_seconds if self._enable_storage_sync else None,
        }

    def _validate_agent_card(self, agent_card: AgentCard) -> None:
        if not agent_card.skills:
            raise ValueError("Agent must have at least one skill")
        if not agent_card.endpoint:
            raise ValueError("Agent must include an endpoint")

    def _update_indexes(self, agent_id: str, agent_card: AgentCard) -> None:
        for skill in agent_card.skills:
            self.skill_index.setdefault(skill.name, set()).add(agent_id)

        protocol = agent_card.protocol.value if hasattr(agent_card.protocol, "value") else str(agent_card.protocol)
        self.protocol_index.setdefault(protocol, set()).add(agent_id)

        if agent_card.tags:
            for tag in agent_card.tags:
                self.tag_index.setdefault(tag, set()).add(agent_id)

    def _remove_from_indexes(self, agent_id: str, agent_card: AgentCard) -> None:
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

    async def _matches_query(self, agent: AgentCard, query: str) -> bool:
        score, _ = await self._search_score(agent, query)
        return score > 0

    async def _search_score(self, agent: AgentCard, query: str) -> Any:
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
        # We use a multiplier: 0.8 (minimum) to 1.2 (for 1.0 trust)
        trust_score = await self.calculate_trust_score(agent.id)
        trust_booster = 0.8 + (trust_score * 0.4)
        
        final_score = semantic_score * trust_booster

        return final_score, matched_fields

    async def _health_check_loop(self) -> None:
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._perform_health_checks()
            except asyncio.CancelledError:
                break
            except Exception as exc:  # pragma: no cover
                logger.error("Health check loop error: %s", exc)

    async def _storage_sync_loop(self) -> None:
        while True:
            try:
                await asyncio.sleep(self._sync_interval_seconds)
                changed = await self._sync_from_storage()
                if changed:
                    logger.info("Registry synchronized from storage")
            except asyncio.CancelledError:
                break
            except Exception as exc:  # pragma: no cover
                logger.error("Storage sync loop error: %s", exc)

    async def _perform_health_checks(self) -> None:
        now = datetime.now(timezone.utc)
        async with self._state_lock:
            for agent_id, agent in list(self.agents.items()):
                try:
                    if agent.last_health_check is None:
                        continue

                    delta = now - agent.last_health_check.astimezone(timezone.utc)
                    if delta.total_seconds() > self.max_unhealthy_time:
                        agent.set_health_status(HealthStatus.OFFLINE)
                        await self.storage.upsert_agent(agent)
                        logger.warning("Agent %s marked as offline due to stale heartbeat", agent_id)
                except Exception as exc:  # pragma: no cover
                    logger.error("Health check failed for %s: %s", agent_id, exc)
                    agent.set_health_status(HealthStatus.UNHEALTHY)
                    await self.storage.upsert_agent(agent)
