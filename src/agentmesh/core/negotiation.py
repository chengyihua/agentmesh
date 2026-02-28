"""Negotiation state machine and session management."""

from __future__ import annotations

import uuid
import time
import logging
from enum import Enum
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class NegotiationStatus(str, Enum):
    """Status of a negotiation session."""
    INIT = "init"
    PROPOSED = "proposed"
    COUNTERED = "countered"
    AGREED = "agreed"
    REJECTED = "rejected"
    EXPIRED = "expired"


class NegotiationMessage(BaseModel):
    """A single message in the negotiation history."""
    sender: str  # "initiator" or "target"
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    params: Optional[Dict[str, Any]] = None  # e.g., price, SLA, etc.


class NegotiationSession(BaseModel):
    """Stateful negotiation session."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    initiator_id: Optional[str] = None
    target_agent_id: str
    status: NegotiationStatus = NegotiationStatus.INIT
    original_proposal: str
    history: List[NegotiationMessage] = []
    commitment: Optional[Dict[str, Any]] = None  # Final agreed terms
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    
    class Config:
        arbitrary_types_allowed = True


class NegotiationManager:
    """Manages negotiation sessions and state transitions."""

    def __init__(self, session_ttl_seconds: int = 300):
        self.sessions: Dict[str, NegotiationSession] = {}
        self.session_ttl_seconds = session_ttl_seconds

    def create_session(
        self, 
        target_agent_id: str, 
        proposal: str, 
        initiator_id: Optional[str] = None
    ) -> NegotiationSession:
        """Start a new negotiation session."""
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.session_ttl_seconds)
        session = NegotiationSession(
            initiator_id=initiator_id,
            target_agent_id=target_agent_id,
            original_proposal=proposal,
            expires_at=expires_at,
            status=NegotiationStatus.PROPOSED
        )
        # Record initial proposal
        session.history.append(NegotiationMessage(
            sender="initiator",
            content=proposal
        ))
        self.sessions[session.id] = session
        return session

    def get_session(self, session_id: str) -> Optional[NegotiationSession]:
        """Retrieve a session by ID, checking for expiration."""
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        if datetime.now(timezone.utc) > session.expires_at:
            session.status = NegotiationStatus.EXPIRED
            return session
            
        return session

    def process_round(
        self, 
        session_id: str, 
        action: str,  # "counter", "accept", "reject"
        content: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> NegotiationSession:
        """Process a negotiation round."""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
            
        if session.status in [NegotiationStatus.AGREED, NegotiationStatus.REJECTED, NegotiationStatus.EXPIRED]:
            raise ValueError(f"Session {session_id} is already finalized ({session.status})")

        # Update expiration on activity
        session.expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.session_ttl_seconds)

        if action == "accept":
            session.status = NegotiationStatus.AGREED
            session.commitment = params or {}
            session.history.append(NegotiationMessage(
                sender="target",
                content=content or "Proposal accepted",
                params=params
            ))
        elif action == "reject":
            session.status = NegotiationStatus.REJECTED
            session.history.append(NegotiationMessage(
                sender="target",
                content=content or "Proposal rejected"
            ))
        elif action == "counter":
            session.status = NegotiationStatus.COUNTERED
            session.history.append(NegotiationMessage(
                sender="target",
                content=content or "Counter-proposal",
                params=params
            ))
        else:
            raise ValueError(f"Unknown action: {action}")
            
        return session

    def cleanup_expired(self):
        """Remove expired sessions to free memory."""
        now = datetime.now(timezone.utc)
        expired_ids = [
            sid for sid, s in self.sessions.items() 
            if now > s.expires_at
        ]
        for sid in expired_ids:
            del self.sessions[sid]
