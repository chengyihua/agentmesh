import time
import httpx
import logging
import asyncio
from typing import List, Dict, Optional, Set
from pydantic import BaseModel

from agentmesh.core.registry import AgentRegistry
from agentmesh.core.agent_card import AgentCard, AgentCardUpdate

logger = logging.getLogger(__name__)

class FederationUpdate(BaseModel):
    agents: List[AgentCard]
    peers: List[str] = []
    timestamp: float

class FederationManager:
    def __init__(self, registry: AgentRegistry, seeds: List[str] = None):
        self.registry = registry
        self.seeds = seeds or []
        self.peers: Set[str] = set(self.seeds)

    async def get_local_updates(self, since_timestamp: float = 0) -> FederationUpdate:
        agents = await self.registry.list_agents()
        
        # Filter by updated_at
        updates = []
        for agent in agents:
            # updated_at is datetime, convert to timestamp
            ts = agent.updated_at.timestamp() if agent.updated_at else 0
            if ts > since_timestamp:
                updates.append(agent)
                
        return FederationUpdate(
            agents=updates,
            peers=list(self.peers),
            timestamp=time.time()
        )

    async def sync_from_seeds(self):
        """Pull updates from all seed nodes and peers."""
        # Sync from all known peers (including seeds)
        # Use a copy to avoid modification during iteration
        targets = list(self.peers)
        if not targets:
            targets = list(self.seeds)
        
        async with httpx.AsyncClient() as client:
            for seed in targets:
                try:
                    # Append protocol if missing
                    if not seed.startswith("http"):
                        url = f"http://{seed}/federation/pull"
                    else:
                        url = f"{seed}/federation/pull"
                        
                    resp = await client.get(url, timeout=5.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        await self._process_sync_data(data)
                        if self.registry.telemetry:
                            self.registry.telemetry.federation_sync_ops.labels(status="success", seed=seed).inc()
                    else:
                        if self.registry.telemetry:
                            self.registry.telemetry.federation_sync_ops.labels(status="failure", seed=seed).inc()
                except Exception as e:
                    logger.warning(f"Failed to sync from seed {seed}: {e}")
                    if self.registry.telemetry:
                        self.registry.telemetry.federation_sync_ops.labels(status="error", seed=seed).inc()

    async def _process_sync_data(self, data: Dict):
        """Process received federation data."""
        # 1. Update peers
        remote_peers = data.get("peers", [])
        for p in remote_peers:
            if p:
                self.peers.add(p)
            
        # 2. Merge agents
        agents_data = data.get("agents", [])
        for agent_dict in agents_data:
            try:
                # Parse as AgentCard
                card = AgentCard(**agent_dict)
                
                # Verify signature if present/required
                if card.signature or card.manifest_signature:
                    if not await self.registry.security_manager.verify_signature(card):
                        logger.warning(f"Invalid signature for federated agent {card.id}")
                        continue
                
                existing = await self.registry.get_agent(card.id)
                
                if not existing:
                    # Register new agent
                    try:
                        await self.registry.register_agent(card)
                        logger.info(f"Registered new federated agent: {card.id}")
                        if self.registry.telemetry:
                            self.registry.telemetry.federated_agents_synced.labels(status="new").inc()
                    except Exception as reg_error:
                        logger.debug(f"Skipping agent {card.id} from sync: {reg_error}")
                        if self.registry.telemetry:
                            self.registry.telemetry.federated_agents_synced.labels(status="error").inc()
                else:
                    # Update existing if newer
                    # Use strict inequality to avoid loops on same timestamp
                    if card.updated_at > existing.updated_at:
                        # Create update object, EXCLUDING trust_score to preserve local trust
                        # But INCLUDE security fields because they are part of the authentic update
                        update_dict = card.model_dump(
                            exclude={
                                "trust_score", 
                                "created_at", 
                                "updated_at", 
                                "id", 
                                "claim_code", 
                                "species_id"
                            }, 
                            exclude_none=True
                        )
                        
                        # Handle URL fields conversion (pydantic HttpUrl to str)
                        for field in ["endpoint", "documentation_url", "source_code_url"]:
                            if field in update_dict and update_dict[field]:
                                update_dict[field] = str(update_dict[field])
                            
                        update_obj = AgentCardUpdate(**update_dict)
                        
                        await self.registry.update_agent(card.id, update_obj)
                        logger.info(f"Updated federated agent: {card.id}")
                        if self.registry.telemetry:
                            self.registry.telemetry.federated_agents_synced.labels(status="updated").inc()
                        
            except Exception as e:
                logger.warning(f"Failed to process agent from sync data: {e}")
                if self.registry.telemetry:
                    self.registry.telemetry.federated_agents_synced.labels(status="error").inc()

    async def start_background_sync(self, interval: float = 60.0):
        """Start background synchronization loop."""
        logger.info(f"Starting federation sync loop with interval {interval}s")
        while True:
            try:
                await self.sync_from_seeds()
            except asyncio.CancelledError:
                logger.info("Federation sync loop cancelled")
                raise
            except Exception as e:
                logger.error(f"Error in background sync: {e}")
            
            await asyncio.sleep(interval)
