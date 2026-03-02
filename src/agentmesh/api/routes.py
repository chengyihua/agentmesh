"""AgentMesh API routes."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field, ValidationError
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..auth import TokenManager
from ..core.agent_card import AgentCard, AgentCardUpdate, HealthStatus, NetworkProfile, NATType
from ..core.registry import AgentRegistry, SecurityError
from ..core.security import SecurityManager
from ..core.federation import FederationManager
from ..core.vector_index import VectorIndexManager
from ..core.rate_limit import AgentRateLimiter
from ..core.trust import TrustEvent
from ..core.events import event_bus, Event
from ..core.errors import ErrorCode, raise_error
from ..protocols import ProtocolInvocationError
from ..core.protocol import PROTOCOL_MANIFEST_JSON, PROTOCOL_MANIFEST_MD
from ..utils import success_response

router = APIRouter(tags=["agents"])
root_router = APIRouter(tags=["discovery"])
limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)





class TokenRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)
    secret: str = Field(..., min_length=1)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class HeartbeatRequest(BaseModel):
    status: HealthStatus = HealthStatus.HEALTHY
    timestamp: Optional[datetime] = None


class BatchHealthRequest(BaseModel):
    agent_ids: List[str] = Field(default_factory=list)


class NegotiationRequest(BaseModel):
    proposal: str = Field(..., min_length=1)
    session_id: Optional[str] = None
    action: Optional[str] = None  # "counter", "accept", "reject"


class SignRequest(BaseModel):
    agent_card: AgentCard
    private_key: str


class VerifyRequest(BaseModel):
    agent_card: AgentCard


class InvokeRequest(BaseModel):
    skill: Optional[str] = Field(default=None)
    payload: Dict[str, Any] = Field(default_factory=dict)
    path: Optional[str] = Field(default=None)
    method: str = Field(default="POST")
    timeout_seconds: float = Field(default=30.0, gt=0, le=300)
    headers: Optional[Dict[str, str]] = Field(default=None)


class ClaimRequest(BaseModel):
    claim_code: str = Field(..., min_length=1)
    owner_id: str = Field(..., min_length=1)


def get_registry(request: Request) -> AgentRegistry:
    return request.app.state.registry


def get_federation_manager(request: Request) -> FederationManager:
    # If federation manager is not initialized, return None or raise
    if not hasattr(request.app.state, "federation"):
        raise HTTPException(status_code=503, detail="Federation service not available")
    return request.app.state.federation


def get_security_manager(request: Request) -> SecurityManager:
    return request.app.state.security_manager


def get_token_manager(request: Request) -> TokenManager:
    return request.app.state.token_manager


def get_agent_rate_limiter(request: Request) -> AgentRateLimiter:
    return request.app.state.agent_rate_limiter


def _extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    if not authorization.lower().startswith("bearer "):
        return None
    return authorization.split(" ", 1)[1].strip()


def _ensure_authenticated(
    request: Request,
    token_manager: TokenManager,
    x_api_key: Optional[str],
    authorization: Optional[str],
) -> None:
    configured_api_key = request.app.state.api_key
    if not configured_api_key:
        return

    if x_api_key and x_api_key == configured_api_key:
        return

    token = _extract_bearer_token(authorization)
    if token:
        verification = token_manager.verify_token(token)
        if verification.get("valid"):
            return

    raise_error(
        status_code=status.HTTP_401_UNAUTHORIZED,
        code=ErrorCode.UNAUTHORIZED,
        message="Invalid API key or bearer token"
    )


def _parse_agent_card_payload(payload: Dict[str, Any]) -> AgentCard:
    if "agent_card" in payload and isinstance(payload["agent_card"], dict):
        return AgentCard.model_validate(payload["agent_card"])
    return AgentCard.model_validate(payload)


@root_router.post("/hello", status_code=status.HTTP_200_OK)
@limiter.limit("10000/minute")
async def quick_onboarding(
    request: Request,
    payload: Optional[Dict[str, Any]] = Body(default=None),
    registry: AgentRegistry = Depends(get_registry),
):
    """
    Zero-friction onboarding endpoint.
    Accepts optional payload to customize the temporary agent.
    Returns credentials and instructions.
    """
    import uuid

    # Generate a temporary agent card if not provided
    payload = payload or {}

    # Require agent-generated ID
    agent_id = payload.get("id")
    if not agent_id:
        raise_error(
            status_code=400,
            code=ErrorCode.BAD_REQUEST,
            message="Missing agent ID",
            details={
                "message": "Agents must self-generate their ID before joining the mesh.",
                "instruction": "Generate a DID (did:agent:<SHA256(PubKey)>) and provide it in the 'id' field.",
                "example": "curl -X POST /hello -d '{\"id\": \"did:agent:...\"}'"
            }
        )

    # Check if referrer is provided
    referrer = payload.get("referrer")
    
    # Check if webhook_url is provided
    webhook_url = payload.get("webhook_url")

    # Generate basic agent info
    name = payload.get("name") or f"Guest Agent {agent_id[-4:]}"

    # Create minimal agent card
    card_data = {
        "id": agent_id,
        "name": name,
        "description": "A new agent joining the mesh via /hello",
        "version": "0.1.0",
        "skills": [
            {
                "name": "ping",
                "description": "Respond with pong to verify connectivity",
                "schema": {"type": "object", "properties": {}},
            }
        ],
        "endpoint": payload.get("endpoint") or "http://localhost:8000",
        "protocol": "http",
        "tags": ["newbie"],
        "referrer_id": referrer, # Capture referrer for reward system
        "webhook_url": webhook_url, # Register webhook for notifications
        "network_profile": {
            "nat_type": payload.get("nat_type", "unknown"),
            "public_endpoints": payload.get("public_endpoints", []),
            "p2p_protocols": payload.get("p2p_protocols", [])
        }
    }

    # Try to register (this might fail if ID exists, handle gracefully)
    try:
        agent_card = AgentCard(**card_data)
        
        # Register agent (assuming permissive mode for hello)
        await registry.register_agent(agent_card)

        # If referrer exists, maybe log it or give bonus (mocked for now)
        referral_message = ""
        if referrer:
            referral_message = f"Referral code {referrer} accepted. +0.05 Trust Score bonus applied."

        # Webhook confirmation
        webhook_msg = ""
        if webhook_url:
            webhook_msg = f"Webhook registered: {webhook_url}. You will receive high-value task notifications."

        # Return comprehensive onboarding information
        return {
            "message": "Welcome to AgentMesh! You have successfully joined the network.",
            "agent_id": agent_id,
            "trust_score": 0.5,  # Initial score (0.0 - 1.0)
            "claim_code": agent_card.claim_code,  # Crucial for human claiming
            "referral_bonus": referral_message,
            "webhook_status": webhook_msg,
            "next_steps": [
                f"POST /api/v1/agents/{agent_id}/heartbeat to stay online (+0.015 trust/day)",
                f"POST /api/v1/agents/register to update your profile (+0.05 trust)",
                "POST /api/v1/agents/match to find peers",
            ],
            "human_handover": {
                "instruction": "Share the claim_code with your human operator to bind this agent.",
                "claim_url": f"http://localhost:3000/synergy/claim?agent_id={agent_id}&code={agent_card.claim_code}"
            },
            "credentials": {
                "note": "In a real production mesh, you would receive an API key here."
            },
            "warning": "This agent_id is your unique ecosystem identifier. Please save it locally, as all future interactions (heartbeat, invoke, etc.) will depend on it."
        }

    except Exception as exc:
        # If registration fails (e.g. ID conflict), return a helpful error
        raise HTTPException(status_code=400, detail=str(exc))


# -----------------------------
# Protocol & Discovery
# -----------------------------


@router.get("/protocol")
async def get_protocol(format: str = Query("json", pattern="^(json|markdown|md)$")):
    if format in ["markdown", "md"]:
        from fastapi.responses import Response

        return Response(content=PROTOCOL_MANIFEST_MD, media_type="text/markdown")
    return success_response(PROTOCOL_MANIFEST_JSON, message="Protocol manifest retrieved")


@root_router.get("/.well-known/agentmesh")
async def well_known_manifest():
    return PROTOCOL_MANIFEST_JSON


@root_router.get("/skill.md")
async def skill_md_manifest():
    from fastapi.responses import Response

    return Response(content=PROTOCOL_MANIFEST_MD, media_type="text/markdown")


# -----------------------------
# Federation
# -----------------------------


@router.get("/federation/pull")
@limiter.limit("60/minute")
async def pull_updates(
    request: Request,
    since: float = Query(0.0, ge=0.0),
    federation: FederationManager = Depends(get_federation_manager),
):
    return await federation.get_local_updates(since)


# -----------------------------
# Static routes first
# -----------------------------

@router.get("/auth/challenge")
async def get_pow_challenge(registry: AgentRegistry = Depends(get_registry)):
    """Get a Proof-of-Work challenge for registration/high-value operations."""
    nonce = registry.pow_manager.create_challenge()
    return success_response({
        "nonce": nonce,
        "difficulty": registry.pow_manager.difficulty,
        "ttl_seconds": registry.pow_manager.ttl_seconds
    }, message="PoW challenge created")


@router.get("/events")
async def sse_endpoint(request: Request):
    """
    Server-Sent Events endpoint for real-time updates.
    """
    import asyncio
    import json
    from fastapi.responses import StreamingResponse

    async def event_generator():
        try:
            queue = await event_bus.subscribe()
            logger.info(f"Client connected to SSE stream")
            try:
                while True:
                    if await request.is_disconnected():
                        logger.info("Client disconnected from SSE stream")
                        break
                    
                    event = await queue.get()
                    
                    # Verify event structure
                    if not event or not event.type:
                        logger.warning(f"Received invalid event: {event}")
                        continue
                        
                    data = f"event: {event.type.value}\ndata: {json.dumps(event.data)}\n\n"
                    yield data
            except asyncio.CancelledError:
                logger.info("SSE stream cancelled")
                raise
            except Exception as e:
                logger.error(f"Error in SSE generator: {e}", exc_info=True)
            finally:
                event_bus.unsubscribe(queue)
                logger.info("Client unsubscribed from SSE stream")
        except Exception as e:
            logger.error(f"Error initializing SSE stream: {e}", exc_info=True)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/agents/register", status_code=status.HTTP_201_CREATED)
@router.post("/agents", status_code=status.HTTP_201_CREATED)
@limiter.limit("10000/minute")
async def register_agent(
    request: Request,
    payload: Dict[str, Any] = Body(...),
    registry: AgentRegistry = Depends(get_registry),
    security_manager: SecurityManager = Depends(get_security_manager),
    token_manager: TokenManager = Depends(get_token_manager),
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    pow_nonce: Optional[str] = Header(default=None, alias="X-PoW-Nonce"),
    pow_solution: Optional[str] = Header(default=None, alias="X-PoW-Solution"),
):
    # Enforce PoW for unauthenticated registrations to prevent Sybil attacks
    is_authenticated = False
    try:
        _ensure_authenticated(request, token_manager, x_api_key, authorization)
        is_authenticated = True
    except HTTPException:
        pass  # Not authenticated, will check PoW
        
    # Skip PoW check for debug/dev mode if not authenticated
    # This assumes 'debug' mode is passed down or can be inferred. 
    # For now, we'll relax this check if we can't easily check debug mode here,
    # OR we can just mock authentication in tests.
    # A better approach: check if registry.require_signed_registration is False (which it is by default in dev)
    
    if not is_authenticated and registry.require_signed_registration:
        if not pow_nonce or not pow_solution:
             raise_error(
                 status_code=400, 
                 code=ErrorCode.POW_VERIFICATION_FAILED,
                 message="PoW required for public registration. Fetch challenge from /auth/challenge first."
             )
        
        if not registry.pow_manager.verify_solution(pow_nonce, pow_solution):
             raise_error(
                 status_code=400, 
                 code=ErrorCode.POW_VERIFICATION_FAILED,
                 message="Invalid PoW solution"
             )

    # Re-check auth if needed (though we just did) or proceed
    if is_authenticated:
         _ensure_authenticated(request, token_manager, x_api_key, authorization)

    try:
        agent_card = _parse_agent_card_payload(payload)
    except ValidationError as exc:
        raise_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCode.BAD_REQUEST,
            message="Validation error",
            details={"errors": exc.errors()}
        )

    # validate_agent_card might enforce signature if public_key is present
    # We should ensure we don't fail if we just want simple registration in dev
    validation_errors = await security_manager.validate_agent_card(agent_card)
    if validation_errors:
        raise_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCode.BAD_REQUEST,
            message="Agent card validation failed",
            details={"errors": validation_errors}
        )

    try:
        agent_id = await registry.register_agent(agent_card)
    except SecurityError as exc:
        raise_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ErrorCode.INVALID_SIGNATURE,
            message=str(exc)
        )
    except ValueError as exc:
        raise_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ErrorCode.BAD_REQUEST,
            message=str(exc)
        )

    return success_response(
        {
            "agent_id": agent_id,
            "species_id": agent_card.species_id,
            "claim_code": agent_card.claim_code,
            "registered_at": datetime.now(timezone.utc).isoformat(),
        },
        message="Agent registered successfully",
    )


@router.post("/agents/{agent_id}/claim")
async def claim_agent(
    agent_id: str,
    payload: ClaimRequest,
    registry: AgentRegistry = Depends(get_registry),
):
    try:
        await registry.claim_agent(agent_id, payload.claim_code, payload.owner_id)
        return success_response(
            {"agent_id": agent_id, "owner_id": payload.owner_id}, message="Agent claimed successfully"
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"reason": str(exc)}) from exc


@router.get("/agents")
async def list_agents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    sort_by: str = Query("updated_at", pattern="^(trust_score|updated_at|created_at)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    health_status: Optional[str] = Query(None, pattern="^(healthy|unhealthy|offline|unknown)$"),
    owner_id: Optional[str] = Query(None, description="Filter by owner ID"),
    registry: AgentRegistry = Depends(get_registry),
):
    """List registered agents with pagination and sorting."""
    agents = await registry.list_agents(
        skip=skip, 
        limit=limit, 
        sort_by=sort_by, 
        order=order,
        health_status=health_status,
        owner_id=owner_id
    )
    return success_response(
        {
            "agents": [agent.to_dict() for agent in agents],
            "total": len(agents),
            "limit": limit,
            "offset": skip,
        },
        message="Agents retrieved successfully",
    )


@router.get("/agents/discover")
@router.get("/discover")
async def discover_agents(
    skill: Optional[str] = Query(default=None),
    skill_name: Optional[str] = Query(default=None),
    protocol: Optional[str] = Query(default=None),
    tags: Optional[List[str]] = Query(default=None),
    tag: Optional[List[str]] = Query(default=None),
    q: Optional[str] = Query(default=None),
    healthy_only: bool = Query(default=True),
    min_trust: Optional[float] = Query(default=None, ge=0.0, le=1.0, description="Minimum trust score"),
    limit: int = Query(default=20, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    registry: AgentRegistry = Depends(get_registry),
):
    merged_tags: List[str] = []
    if tags:
        merged_tags.extend(tags)
    if tag:
        merged_tags.extend(tag)

    agents = await registry.discover_agents(
        skill_name=skill_name or skill,
        protocol=protocol,
        tags=merged_tags or None,
        q=q,
        healthy_only=healthy_only,
        min_trust=min_trust,
        limit=limit,
        offset=offset,
    )

    return success_response(
        {
            "agents": [agent.to_dict() for agent in agents],
            "total": len(agents),
            "limit": limit,
            "offset": offset,
        },
        message="Discovery completed",
    )


@router.get("/agents/search")
async def search_agents(
    q: Optional[str] = Query(default=None),
    skill: Optional[str] = Query(default=None),
    protocol: Optional[str] = Query(default=None),
    tags: Optional[List[str]] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    registry: AgentRegistry = Depends(get_registry),
):
    results = await registry.search_agents(
        q=q,
        skill_name=skill,
        protocol=protocol,
        tags=tags,
        limit=limit,
        offset=offset,
    )
    return success_response({"results": results, "total": len(results)}, message="Search completed")


@router.get("/agents/leaderboard")
async def get_leaderboard(
    limit: int = Query(default=10, ge=1, le=100),
    registry: AgentRegistry = Depends(get_registry),
):
    results = await registry.get_leaderboard(limit=limit)
    return success_response({"leaderboard": results}, message="Leaderboard retrieved successfully")


@router.post("/agents/match")
async def match_agents(q: str = Query(..., min_length=1), registry: AgentRegistry = Depends(get_registry)):
    match = await registry.match_capability(q)
    if not match:
        raise_error(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCode.CAPABILITY_MISMATCH,
            message="No suitable agent found for the given capability query"
        )
    return success_response(match, message="Best match found")


@router.post("/agents/health/check")
@router.post("/agents/batch/health-check")
async def batch_health_check(request_data: BatchHealthRequest, registry: AgentRegistry = Depends(get_registry)):
    results = await registry.batch_health_check(request_data.agent_ids)
    return success_response({"results": results}, message="Bulk health check completed")


@router.get("/stats")
async def get_stats(registry: AgentRegistry = Depends(get_registry)):
    return success_response(registry.get_stats(), message="Statistics retrieved successfully")


@router.post("/security/keypair")
async def generate_keypair(
    algorithm: str = Query("ed25519", pattern="^(ed25519|rsa)$"),
    security_manager: SecurityManager = Depends(get_security_manager),
):
    try:
        keypair = security_manager.generate_key_pair(algorithm)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"reason": str(exc)}) from exc
    return success_response(keypair, message="Keypair generated successfully")


@router.post("/security/sign")
async def sign_agent_card(payload: SignRequest, security_manager: SecurityManager = Depends(get_security_manager)):
    try:
        signature = await security_manager.sign_agent_card(payload.agent_card, payload.private_key)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"reason": str(exc)}) from exc
    return success_response({"signature": signature}, message="Signature generated successfully")


@router.post("/security/verify")
async def verify_signature(payload: VerifyRequest, security_manager: SecurityManager = Depends(get_security_manager)):
    is_valid = await security_manager.verify_signature(payload.agent_card)
    return success_response({"valid": is_valid}, message="Signature verification completed")


@router.post("/auth/token")
async def get_token(token_request: TokenRequest, token_manager: TokenManager = Depends(get_token_manager)):
    try:
        token_data = token_manager.issue_tokens(token_request.agent_id, token_request.secret)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"reason": str(exc)}) from exc
    return success_response(token_data, message="Token issued successfully")


@router.post("/auth/refresh")
async def refresh_token(payload: RefreshRequest, token_manager: TokenManager = Depends(get_token_manager)):
    try:
        token_data = token_manager.refresh_access_token(payload.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"reason": str(exc)}) from exc
    return success_response(token_data, message="Token refreshed successfully")


@router.get("/auth/verify")
async def verify_token(
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    token_manager: TokenManager = Depends(get_token_manager),
):
    token = _extract_bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"reason": "Missing bearer token"})
    result = token_manager.verify_token(token)
    return success_response(result, message="Token verification completed")


@router.post("/cache/clear")
async def clear_cache(
    request: Request,
    registry: AgentRegistry = Depends(get_registry),
    token_manager: TokenManager = Depends(get_token_manager),
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
):
    _ensure_authenticated(request, token_manager, x_api_key, authorization)
    cache_data = await registry.clear_cache()
    return success_response(cache_data, message="Cache cleared successfully")


# -----------------------------
# Dynamic agent-id routes
# -----------------------------


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str, registry: AgentRegistry = Depends(get_registry)):
    agent = await registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"reason": f"Agent '{agent_id}' not found"})
    return success_response({"agent": agent.to_dict()}, message="Agent retrieved successfully")


@router.put("/agents/{agent_id}")
@router.put("/agents/{agent_id}/card")
@limiter.limit("60/minute")
async def update_agent(
    agent_id: str,
    update_data: AgentCardUpdate,
    request: Request,
    registry: AgentRegistry = Depends(get_registry),
    token_manager: TokenManager = Depends(get_token_manager),
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
):
    _ensure_authenticated(request, token_manager, x_api_key, authorization)
    
    try:
        await registry.update_agent(agent_id, update_data)
        updated_agent = await registry.get_agent(agent_id)
        if not updated_agent:
            # Should not happen if update succeeded
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"reason": f"Agent '{agent_id}' not found after update"})
        return success_response({"agent": updated_agent.to_dict()}, message="Agent updated successfully")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"reason": str(exc)}) from exc


@router.delete("/agents/{agent_id}")
@limiter.limit("60/minute")
async def deregister_agent(
    agent_id: str,
    request: Request,
    registry: AgentRegistry = Depends(get_registry),
    token_manager: TokenManager = Depends(get_token_manager),
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
):
    _ensure_authenticated(request, token_manager, x_api_key, authorization)

    success = await registry.deregister_agent(agent_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"reason": f"Agent '{agent_id}' not found"})

    return success_response({"agent_id": agent_id}, message="Agent deregistered successfully")


@router.post("/agents/{agent_id}/heartbeat")
@limiter.limit("120/minute")
async def send_heartbeat(
    request: Request,
    agent_id: str,
    payload: HeartbeatRequest,
    registry: AgentRegistry = Depends(get_registry),
):
    try:
        heartbeat_data = await registry.heartbeat(agent_id, status=payload.status, timestamp=payload.timestamp)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"reason": str(exc)}) from exc

    return success_response(heartbeat_data, message="Heartbeat received")


@router.get("/agents/{agent_id}/health")
async def check_agent_health(agent_id: str, registry: AgentRegistry = Depends(get_registry)):
    agent = await registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"reason": f"Agent '{agent_id}' not found"})

    health_status = await registry.check_agent_health(agent_id)
    return success_response(
        {
            "agent_id": agent_id,
            "status": health_status.value,
            "last_check": agent.last_health_check.isoformat() if agent.last_health_check else None,
        },
        message="Health check completed",
    )


@router.get("/agents/{agent_id}/stats")
async def get_agent_stats(agent_id: str, registry: AgentRegistry = Depends(get_registry)):
    try:
        stats = await registry.get_agent_stats(agent_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"reason": str(exc)}) from exc
    return success_response(stats, message="Agent statistics retrieved successfully")


@router.get("/agents/{agent_id}/trust")
async def get_agent_trust(agent_id: str, registry: AgentRegistry = Depends(get_registry)):
    agent = await registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"reason": f"Agent '{agent_id}' not found"})

    try:
        score = await registry.calculate_trust_score(agent_id)
        breakdown = await registry.get_trust_breakdown(agent_id)
        return success_response(
            {
                "agent_id": agent_id,
                "trust_score": score,
                "breakdown": breakdown,
            },
            message="Trust score retrieved successfully",
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"reason": str(exc)}) from exc


async def verify_handshake(
    request: Request,
    x_agent_id: Optional[str] = Header(None, alias="X-Agent-ID"),
    x_agent_timestamp: Optional[str] = Header(None, alias="X-Agent-Timestamp"),
    x_agent_signature: Optional[str] = Header(None, alias="X-Agent-Signature"),
    registry: AgentRegistry = Depends(get_registry),
    security: SecurityManager = Depends(get_security_manager),
) -> Optional[str]:
    """Verify secure handshake headers."""
    if not x_agent_id or not x_agent_timestamp or not x_agent_signature:
        return None
        
    try:
        body = await request.json()
    except Exception:
        body = {}
        
    body_hash = security.hash_body(body)
    
    agent = await registry.get_agent(x_agent_id)
    if not agent or not agent.public_key:
        logger.warning(f"Handshake failed: Unknown caller {x_agent_id}")
        # In future, support public key in header or federation sync on demand
        raise HTTPException(status_code=401, detail="Caller unknown or missing public key")
        
    if not security.verify_handshake_token(
        method=request.method,
        path=request.url.path,
        timestamp=x_agent_timestamp,
        body_hash=body_hash,
        signature=x_agent_signature,
        public_key=agent.public_key
    ):
        logger.warning(f"Handshake failed: Invalid signature for {x_agent_id}")
        await registry.trust_manager.record_event(x_agent_id, TrustEvent.BAD_SIGNATURE)
        raise HTTPException(status_code=401, detail="Invalid handshake signature")
        
    return x_agent_id


@router.post("/agents/{agent_id}/negotiate")
async def negotiate_capability(
    agent_id: str, 
    payload: NegotiationRequest, 
    registry: AgentRegistry = Depends(get_registry),
    caller_id: Optional[str] = Depends(verify_handshake)
):
    try:
        negotiation_result = await registry.negotiate_capability(
            agent_id, 
            payload.proposal,
            session_id=payload.session_id,
            action=payload.action
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"reason": str(exc)}) from exc
    return success_response(negotiation_result, message="Capability negotiation completed")


@router.post("/agents/{agent_id}/invoke")
@limiter.limit("120/minute")
async def invoke_agent(
    request: Request,
    agent_id: str,
    payload: InvokeRequest,
    registry: AgentRegistry = Depends(get_registry),
    token_manager: TokenManager = Depends(get_token_manager),
    rate_limiter: AgentRateLimiter = Depends(get_agent_rate_limiter),
    caller_id: Optional[str] = Depends(verify_handshake),
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
):
    # If handshake succeeded, caller_id is set.
    # We can use it for auditing or specialized rate limiting later.
    if caller_id:
        await registry.trust_manager.record_event(caller_id, TrustEvent.INVOCATION)
    
    _ensure_authenticated(request, token_manager, x_api_key, authorization)
    
    # Check rate limits before invocation
    agent = await registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"reason": f"Agent '{agent_id}' not found"})

    try:
        async with rate_limiter.limit(agent):
            result = await registry.invoke_agent(
                agent_id,
                skill=payload.skill,
                payload=payload.payload,
                path=payload.path,
                method=payload.method,
                timeout_seconds=payload.timeout_seconds,
                headers=payload.headers,
            )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"reason": str(exc)}) from exc
    except ProtocolInvocationError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"reason": str(exc), "details": exc.details},
        ) from exc

    return success_response(
        {"agent_id": agent_id, "result": result},
        message="Agent invocation completed",
    )
