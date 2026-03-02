"""Authentication routes for human users."""

from __future__ import annotations

import logging
import uuid
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status, Header
from pydantic import ValidationError

from ..auth.user import User, OTPRequest, OTPVerify, LoginResponse
from ..auth.otp import OTPManager
from ..core.registry import AgentRegistry
from ..utils import success_response
from .routes import get_registry

logger = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])

# In-memory OTP manager for simplicity (or use Redis in production)
otp_manager = OTPManager()

def get_otp_manager() -> OTPManager:
    return otp_manager

@router.post("/auth/send-otp")
async def send_otp(
    payload: OTPRequest,
    otp_mgr: OTPManager = Depends(get_otp_manager)
):
    """Send OTP to phone number."""
    code = await otp_mgr.generate_otp(payload.phone_number)
    
    # In debug mode, we might want to return the code for testing
    # But for security, we should only log it.
    # The user can see it in the logs.
    return success_response(
        {"message": "OTP sent successfully", "debug_code": code}, # Remove debug_code in prod
        message="OTP sent"
    )

@router.post("/auth/login", response_model=Dict[str, Any])
async def login_with_otp(
    payload: OTPVerify,
    request: Request,
    otp_mgr: OTPManager = Depends(get_otp_manager),
    registry: AgentRegistry = Depends(get_registry)
):
    """Verify OTP and login/register user."""
    is_valid = await otp_mgr.verify_otp(payload.phone_number, payload.code)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )

    # Check if user exists
    user = await registry.storage.get_user_by_phone(payload.phone_number)
    
    if not user:
        # Register new user
        user = User(
            id=str(uuid.uuid4()),
            phone_number=payload.phone_number,
            username=f"user_{payload.phone_number[-4:]}"
        )
        await registry.storage.upsert_user(user)
        is_new = True
    else:
        is_new = False
        
    # Generate simple token (in real app, use JWT)
    # For now, we use user_id as token for simplicity in this demo context
    token = f"user:{user.id}"
    
    return success_response({
        "token": token,
        "user": user.model_dump(),
        "is_new": is_new
    }, message="Login successful")

@router.get("/users/me")
async def get_current_user(
    request: Request,
    authorization: str = Header(..., alias="Authorization"),
    registry: AgentRegistry = Depends(get_registry)
):
    """Get current user profile."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
        
    token = authorization.split(" ")[1]
    if not token.startswith("user:"):
        raise HTTPException(status_code=401, detail="Invalid user token")
        
    user_id = token.split(":")[1]
    user = await registry.storage.get_user(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return success_response({"user": user.model_dump()}, message="User profile")

@router.post("/agents/bind")
async def bind_agent(
    payload: Dict[str, str],
    request: Request,
    authorization: str = Header(..., alias="Authorization"),
    registry: AgentRegistry = Depends(get_registry)
):
    """Bind an agent using claim code to the current user."""
    # 1. Auth check
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    
    token = authorization.split(" ")[1]
    if not token.startswith("user:"):
        raise HTTPException(status_code=401, detail="Invalid user token")
    
    user_id = token.split(":")[1]
    user = await registry.storage.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Get payload params
    agent_id = payload.get("agent_id")
    claim_code = payload.get("claim_code")
    
    if not agent_id or not claim_code:
        raise HTTPException(status_code=400, detail="Missing agent_id or claim_code")

    # 3. Perform Claim
    # We use the user.id as the owner_id
    try:
        await registry.claim_agent(agent_id, claim_code, user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 4. Update User's owned list (optional, but good for quick lookup)
    if agent_id not in user.owned_agent_ids:
        user.owned_agent_ids.append(agent_id)
        await registry.storage.upsert_user(user)

    return success_response(
        {"agent_id": agent_id, "owner_id": user.id},
        message="Agent bound successfully"
    )
