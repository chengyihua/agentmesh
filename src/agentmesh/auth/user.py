"""User model definition."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field

class User(BaseModel):
    """Human user model."""
    id: str = Field(..., description="Unique user identifier (e.g. phone number or UUID)")
    phone_number: str = Field(..., description="Phone number for verification")
    username: Optional[str] = Field(default=None, description="Optional username")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None
    owned_agent_ids: List[str] = Field(default_factory=list)

class OTPRequest(BaseModel):
    phone_number: str = Field(..., min_length=10, description="Phone number with country code")

class OTPVerify(BaseModel):
    phone_number: str
    code: str

class LoginResponse(BaseModel):
    token: str
    user: User
