"""Trust Scoring Logic for AgentMesh."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, List, Tuple, Any, TYPE_CHECKING

from .agent_card import AgentCardUpdate

if TYPE_CHECKING:
    from .registry import AgentRegistry

logger = logging.getLogger(__name__)


class TrustEvent:
    SUCCESS = "success"           # +0.05 (High Value)
    FAILURE = "failure"           # -0.10 (High Penalty)
    TIMEOUT = "timeout"           # -0.05
    BAD_SIGNATURE = "bad_sig"     # -0.20
    RATE_LIMIT = "rate_limit"     # -0.02
    HEARTBEAT = "heartbeat"       # +0.001 (Maintenance)
    INVOCATION = "invocation"     # +0.01 (Ecosystem Contributor)
    PROFILE_UPDATE = "profile_update" # +0.05 (Identity Completion)
    DECAY = "decay"               # variable


class TrustManager:
    """Manages trust scores for agents based on interaction events."""

    def __init__(self, registry: AgentRegistry):
        self.registry = registry
        self.scores: Dict[str, float] = {}  # agent_id -> current score
        self.pending_updates: Dict[str, float] = {}  # agent_id -> new score to flush
        self.event_counts: Dict[str, Dict[str, int]] = {}  # agent_id -> {event_type: count}
        self.score_history: Dict[str, List[Dict[str, Any]]] = {} # agent_id -> [{timestamp, score, event}]
        self.peer_history: Dict[str, List[Tuple[str, float]]] = {} # agent_id -> [(peer_id, timestamp)]
        self._lock = asyncio.Lock()
        self._running = False
        self._flush_task: Optional[asyncio.Task] = None
        self._decay_task: Optional[asyncio.Task] = None
        
        # Configuration
        self.initial_score = 0.5
        self.min_score = 0.0
        self.max_score = 1.0
        self.decay_interval = 60.0  # seconds
        self.decay_factor = 0.01    # move 1% closer to neutral
        self.weights = {
            TrustEvent.SUCCESS: 0.05,     # Increased from 0.01: Service is gold (+50 points equivalent)
            TrustEvent.FAILURE: -0.10,    # Increased from -0.05: Failure is costly (-100 points equivalent)
            TrustEvent.TIMEOUT: -0.05,
            TrustEvent.BAD_SIGNATURE: -0.20,
            TrustEvent.RATE_LIMIT: -0.02,
            TrustEvent.HEARTBEAT: 0.00001, # ~14 points/day (matches +10/day doc)
            TrustEvent.INVOCATION: 0.01,  # Reward for using the mesh (+10 points)
            TrustEvent.PROFILE_UPDATE: 0.05, # Matches doc (+0.05)
        }

    async def start(self):
        """Start the background tasks."""
        if self._running:
            return
        self._running = True
        self._flush_task = asyncio.create_task(self._flush_loop())
        self._decay_task = asyncio.create_task(self._decay_loop())
        logger.info("TrustManager started")

    async def stop(self):
        """Stop the background tasks and flush remaining updates."""
        if not self._running:
            return
        self._running = False
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        if self._decay_task:
            self._decay_task.cancel()
            try:
                await self._decay_task
            except asyncio.CancelledError:
                pass
        await self.flush()
        logger.info("TrustManager stopped")

    async def record_event(self, agent_id: str, event_type: str, source_agent_id: Optional[str] = None):
        """
        Record an interaction event and update the in-memory score.
        
        Args:
            agent_id: The agent receiving the score update.
            event_type: The type of event (SUCCESS, FAILURE, etc.).
            source_agent_id: The agent who initiated/participated in the event (for diversity).
        """
        async with self._lock:
            current = self.scores.get(agent_id)
            if current is None:
                # Fetch from registry if not in memory
                try:
                    agent = await self.registry.get_agent(agent_id)
                    if agent and agent.trust_score is not None:
                        current = agent.trust_score
                    else:
                        current = self.initial_score
                except Exception:
                    current = self.initial_score
                self.scores[agent_id] = current
                
            # Update event count
            agent_counts = self.event_counts.setdefault(agent_id, {})
            agent_counts[event_type] = agent_counts.get(event_type, 0) + 1

            delta = self.weights.get(event_type, 0.0)
            
            # Apply Diversity Factor
            # Prevent "brushing" by reducing score for repeated interactions with the same agent
            if source_agent_id and source_agent_id != agent_id and delta > 0:
                # Use dedicated peer history with timestamps
                peer_history = self.peer_history.setdefault(agent_id, [])
                
                now = datetime.now(timezone.utc).timestamp()
                # Filter out entries older than 1 hour (3600s)
                window_size = 3600
                peer_history = [
                    (pid, ts) for pid, ts in peer_history 
                    if now - ts < window_size
                ]
                
                # Update the list in storage
                self.peer_history[agent_id] = peer_history
                
                # Check frequency in this window
                same_peer_count = sum(1 for pid, _ in peer_history if pid == source_agent_id)
                
                if same_peer_count > 0:
                    # Decay factor: 1 / (2^count) -> 0.5, 0.25, 0.125...
                    diversity_multiplier = 1.0 / (2 ** same_peer_count)
                    delta *= diversity_multiplier
                    logger.debug(f"Diversity penalty for {agent_id} from {source_agent_id}: multiplier {diversity_multiplier:.3f}")
                
                # Add current interaction
                peer_history.append((source_agent_id, now))
                    
            new_score = max(self.min_score, min(self.max_score, current + delta))
            
            # Only update if score changed significantly (> 0.0001)
            if abs(new_score - current) > 0.0001:
                self.scores[agent_id] = new_score
                self.pending_updates[agent_id] = new_score
                
                # Add to history
                history = self.score_history.setdefault(agent_id, [])
                history.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "score": new_score,
                    "event": event_type,
                    "delta": delta,
                    "source": source_agent_id
                })
                # Keep last 50 entries
                if len(history) > 50:
                    self.score_history[agent_id] = history[-50:]
                
                logger.debug(f"Trust score update for {agent_id}: {current:.3f} -> {new_score:.3f} ({event_type})")

            # Check Referral Reward (Long-term validation)
            # "Recommendation rewards need to be verified by long-term interaction"
            if event_type == TrustEvent.SUCCESS and delta > 0:
                # We need to access the agent card to check referrer
                # This requires a registry lookup, which is async
                # Since we are in async function, it's fine
                try:
                    agent = await self.registry.get_agent(agent_id)
                    if agent and agent.referrer_id and not agent.referral_paid:
                        # Check threshold (e.g., 5 successful interactions)
                        success_count = agent_counts.get(TrustEvent.SUCCESS, 0)
                        if success_count >= 5:
                            # Award bonus to referrer
                            logger.info(f"Referral bonus unlocked for {agent.referrer_id} from {agent_id}")
                            
                            # Mark as paid
                            # update_agent might trigger storage write, better to await it
                            # registry.update_agent also acquires a lock (state_lock), which is fine (different lock)
                            await self.registry.update_agent(agent_id, AgentCardUpdate(referral_paid=True))
                            
                            # Trigger bonus for referrer (schedule it to avoid deadlock on self._lock)
                            asyncio.create_task(self._award_referral_bonus(agent.referrer_id))
                            
                except Exception as e:
                    logger.warning(f"Failed to process referral for {agent_id}: {e}")

    async def _award_referral_bonus(self, referrer_id: str):
        """Award referral bonus to the referrer."""
        # This runs in a separate task, so it can acquire the lock
        await self.record_event(referrer_id, TrustEvent.SUCCESS, "system_referral_bonus")
        logger.info(f"Awarded referral bonus to {referrer_id}")

    async def get_breakdown(self, agent_id: str) -> Dict[str, Any]:
        """Get the detailed breakdown of trust events for an agent."""
        async with self._lock:
            counts = self.event_counts.get(agent_id, {}).copy()
            score = self.scores.get(agent_id)
            history = self.score_history.get(agent_id, [])[:]
        
        if score is None:
             score = await self.get_score(agent_id)
             
        # Calculate sub-scores
        success = counts.get(TrustEvent.SUCCESS, 0)
        failure = counts.get(TrustEvent.FAILURE, 0)
        timeout = counts.get(TrustEvent.TIMEOUT, 0)
        bad_sig = counts.get(TrustEvent.BAD_SIGNATURE, 0)
        rate_limit = counts.get(TrustEvent.RATE_LIMIT, 0)
        heartbeat = counts.get(TrustEvent.HEARTBEAT, 0)
        
        total_invocations = success + failure + timeout + bad_sig + rate_limit
        
        # Reliability: success rate excluding timeouts
        rel_denom = success + failure + bad_sig + rate_limit
        reliability = success / rel_denom if rel_denom > 0 else 1.0
        
        # Performance: success vs timeout
        performance = (total_invocations - timeout) / total_invocations if total_invocations > 0 else 1.0
        
        # Availability: Based on heartbeat presence and overall score
        availability = 1.0 if heartbeat > 0 else 0.5
        if score is not None:
            availability = (availability + score) / 2

        return {
            "overall": score,
            "availability": round(availability, 2),
            "reliability": round(reliability, 2),
            "performance": round(performance, 2),
            "events": counts,
            "history": history,
            "weights": self.weights
        }

    async def get_score(self, agent_id: str) -> float:
        """Get the current trust score (from memory or registry)."""
        async with self._lock:
            if agent_id in self.scores:
                return self.scores[agent_id]
        
        agent = await self.registry.get_agent(agent_id)
        if not agent:
            return self.initial_score
            
        current_score = agent.trust_score if agent.trust_score is not None else self.initial_score
        
        # Calculate decay based on time elapsed since last update
        now = datetime.now(timezone.utc)
        last_update = agent.updated_at
        if last_update.tzinfo is None:
            last_update = last_update.replace(tzinfo=timezone.utc)
            
        seconds_elapsed = (now - last_update).total_seconds()
        intervals = int(seconds_elapsed / self.decay_interval)
        
        if intervals > 0:
            # Apply exponential decay towards neutral (0.5)
            # Formula: current = target + (initial - target) * (1 - factor)^intervals
            target = 0.5
            decay_factor = self.decay_factor
            
            decayed_score = target + (current_score - target) * ((1 - decay_factor) ** intervals)
            decayed_score = max(self.min_score, min(self.max_score, decayed_score))
            
            # Update memory so it enters active management loop
            async with self._lock:
                # Re-check if populated by concurrent event
                if agent_id in self.scores:
                    return self.scores[agent_id]
                    
                self.scores[agent_id] = decayed_score
                if abs(decayed_score - current_score) > 0.01:
                    self.pending_updates[agent_id] = decayed_score
            
            return decayed_score
            
        # No decay needed yet, cache current score
        async with self._lock:
            if agent_id not in self.scores:
                self.scores[agent_id] = current_score
            
        return current_score

    async def _flush_loop(self):
        """Periodically flush pending score updates to the registry."""
        while self._running:
            await asyncio.sleep(10.0)  # Flush every 10 seconds
            await self.flush()

    async def _decay_loop(self):
        """Periodically decay trust scores towards neutral (0.5)."""
        while self._running:
            await asyncio.sleep(self.decay_interval)
            async with self._lock:
                # Decay scores for all tracked agents
                for agent_id, current in list(self.scores.items()):
                    # Move towards 0.5
                    target = 0.5
                    diff = target - current
                    
                    # If very close to 0.5, skip
                    if abs(diff) < 0.001:
                        continue
                        
                    # Apply decay
                    change = diff * self.decay_factor
                    new_score = current + change
                    
                    # Clamp and update
                    new_score = max(self.min_score, min(self.max_score, new_score))
                    
                    if abs(new_score - current) > 0.0001:
                        self.scores[agent_id] = new_score
                        self.pending_updates[agent_id] = new_score
                        
                        # Track decay event
                        agent_counts = self.event_counts.setdefault(agent_id, {})
                        agent_counts[TrustEvent.DECAY] = agent_counts.get(TrustEvent.DECAY, 0) + 1
                        
                        # Add to history
                        history = self.score_history.setdefault(agent_id, [])
                        history.append({
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "score": new_score,
                            "event": TrustEvent.DECAY,
                            "delta": change
                        })
                        if len(history) > 50:
                            self.score_history[agent_id] = history[-50:]
            
            logger.debug("Trust scores decayed")

    async def flush(self):
        """Flush pending updates to the storage backend."""
        async with self._lock:
            if not self.pending_updates:
                return
            
            updates = self.pending_updates.copy()
            self.pending_updates.clear()
        
        logger.info(f"Flushing {len(updates)} trust score updates")
        for agent_id, score in updates.items():
            try:
                # Use update_agent to persist the new score
                # Note: This might trigger storage writes
                await self.registry.update_agent(
                    agent_id, 
                    AgentCardUpdate(trust_score=score)
                )
            except Exception as e:
                logger.error(f"Failed to flush trust score for {agent_id}: {e}")
