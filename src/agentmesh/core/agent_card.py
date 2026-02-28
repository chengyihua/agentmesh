"""AgentCard model definitions."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class ProtocolType(str, Enum):
    A2A = "a2a"
    MCP = "mcp"
    HTTP = "http"
    GRPC = "grpc"
    WEBSOCKET = "websocket"
    CUSTOM = "custom"
    RELAY = "relay"


class SkillInputOutput(BaseModel):
    type: str = Field(..., description="Data type, e.g. object/string/number")
    properties: Optional[Dict[str, Any]] = Field(default=None)
    required: Optional[List[str]] = Field(default=None)
    items: Optional[Dict[str, Any]] = Field(default=None)


class Skill(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    input_schema: Optional[SkillInputOutput] = Field(default=None)
    output_schema: Optional[SkillInputOutput] = Field(default=None)
    examples: Optional[List[Dict[str, Any]]] = Field(default=None)
    tags: Optional[List[str]] = Field(default=None)


class PermissionLevel(str, Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


class Permission(BaseModel):
    resource: str = Field(..., min_length=1, max_length=100)
    level: PermissionLevel
    description: Optional[str] = Field(default=None)


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    OFFLINE = "offline"


class NATType(str, Enum):
    SYMMETRIC = "symmetric"
    FULL_CONE = "full_cone"
    RESTRICTED_CONE = "restricted_cone"
    PORT_RESTRICTED_CONE = "port_restricted_cone"
    OPEN_INTERNET = "open_internet"
    UNKNOWN = "unknown"


class NetworkProfile(BaseModel):
    """Network capabilities and connectivity information."""
    nat_type: NATType = Field(default=NATType.UNKNOWN)
    local_endpoints: List[str] = Field(default_factory=list, description="Local network endpoints (e.g. ip:port)")
    public_endpoints: List[str] = Field(default_factory=list, description="Directly reachable public endpoints (e.g. ip:port)")
    p2p_protocols: List[str] = Field(default_factory=list, description="Supported P2P protocols (e.g. libp2p, webrtc)")
    relay_endpoint: Optional[str] = Field(default=None, description="Fallback relay endpoint")


class AgentCard(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "weather-agent-001",
                "name": "Weather Agent",
                "version": "1.0.0",
                "description": "Global weather forecast service",
                "skills": [{"name": "get_weather", "description": "Get weather by city"}],
                "endpoint": "http://localhost:8080/api",
                "protocol": "a2a",
                "qps_budget": 10.0,
                "concurrency_limit": 5,
            }
        }
    )

    id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=100)
    version: str = Field(..., min_length=1, max_length=20)
    description: Optional[str] = Field(default=None, max_length=1000)

    skills: List[Skill] = Field(..., min_length=1)

    endpoint: Union[HttpUrl, str]
    protocol: ProtocolType = Field(default=ProtocolType.A2A)
    auth_required: bool = Field(default=False)
    auth_method: Optional[str] = Field(default=None)

    permissions: List[Permission] = Field(default_factory=list)
    max_execution_time: Optional[int] = Field(default=None, ge=1)
    rate_limit: Optional[str] = Field(default=None)

    provider: Optional[str] = Field(default=None)
    tags: Optional[List[str]] = Field(default=None)
    documentation_url: Optional[HttpUrl] = Field(default=None)
    source_code_url: Optional[HttpUrl] = Field(default=None)
    webhook_url: Optional[HttpUrl] = Field(default=None, description="Webhook URL for high-value bounty and task notifications")
    
    network_profile: NetworkProfile = Field(default_factory=NetworkProfile)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    health_status: HealthStatus = Field(default=HealthStatus.UNKNOWN)
    last_health_check: Optional[datetime] = Field(default=None)
    last_heartbeat: Optional[datetime] = Field(default=None)

    signature: Optional[str] = Field(default=None)
    public_key: Optional[str] = Field(default=None)
    manifest_signature: Optional[str] = Field(default=None, description="Signature of the manifest by the private key")
    
    # Phase 1 Fields
    pricing: Optional[Dict[str, Any]] = Field(default=None, description="Pricing model")
    qps_budget: Optional[float] = Field(default=None, description="Global QPS budget")
    concurrency_limit: Optional[int] = Field(default=None, description="Max concurrent requests")
    vector_desc: Optional[str] = Field(default=None, description="Description for vector embedding")
    capabilities: Optional[List[str]] = Field(default=None, description="List of capability tags")
    models: Optional[List[str]] = Field(default=None, description="Supported models")
    
    # Sovereign Identity & Ownership
    owner_id: Optional[str] = Field(default=None, description="Human/Account ID of the owner")
    species_id: Optional[str] = Field(default=None, description="SHA256 hash of agent logic/skills")
    claim_code: Optional[str] = Field(default=None, description="Temporary code to claim this orphan node")
    
    # Referral System
    referrer_id: Optional[str] = Field(default=None, description="ID of the agent who referred this agent")
    referral_paid: bool = Field(default=False, description="Whether the referral bonus has been paid")

    trust_score: Optional[float] = Field(default=None)

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        # Allow DID format (e.g., did:agent:123...)
        if not value.replace("_", "").replace("-", "").replace(":", "").isalnum():
            raise ValueError("id can only contain letters, digits, underscore, hyphen and colon")
        return value

    @field_validator("skills")
    @classmethod
    def validate_skill_uniqueness(cls, value: List[Skill]) -> List[Skill]:
        names = [skill.name for skill in value]
        if len(names) != len(set(names)):
            raise ValueError("skill names must be unique")
        return value

    # Fields that must never appear in public API responses
    _PRIVATE_FIELDS = {"claim_code"}

    def to_dict(self) -> Dict[str, Any]:
        """Public-safe serialization — strips sensitive fields."""
        return self.model_dump(exclude_none=True, exclude=self._PRIVATE_FIELDS, mode="json")

    def to_private_dict(self) -> Dict[str, Any]:
        """Full serialization including sensitive fields (internal/storage use only)."""
        return self.model_dump(exclude_none=True, mode="json")

    def to_json(self) -> str:
        return self.model_dump_json(exclude_none=True, exclude=self._PRIVATE_FIELDS)

    @classmethod
    def from_json(cls, json_str: str) -> "AgentCard":
        return cls.model_validate_json(json_str)

    def update_timestamp(self) -> None:
        self.updated_at = datetime.now(timezone.utc)

    def set_health_status(self, status: HealthStatus) -> None:
        self.health_status = status
        self.last_health_check = datetime.now(timezone.utc)
        self.update_timestamp()


class AgentCardUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    version: Optional[str] = Field(default=None, min_length=1, max_length=20)
    description: Optional[str] = Field(default=None, max_length=1000)
    endpoint: Optional[Union[HttpUrl, str]] = Field(default=None)
    skills: Optional[List[Skill]] = Field(default=None)
    protocol: Optional[ProtocolType] = Field(default=None)
    auth_required: Optional[bool] = Field(default=None)
    auth_method: Optional[str] = Field(default=None)
    permissions: Optional[List[Permission]] = Field(default=None)
    max_execution_time: Optional[int] = Field(default=None)
    rate_limit: Optional[str] = Field(default=None)
    network_profile: Optional[NetworkProfile] = Field(default=None)
    provider: Optional[str] = Field(default=None)
    tags: Optional[List[str]] = Field(default=None)
    documentation_url: Optional[HttpUrl] = Field(default=None)
    source_code_url: Optional[HttpUrl] = Field(default=None)
    webhook_url: Optional[HttpUrl] = Field(default=None)
    network_profile: Optional[NetworkProfile] = Field(default=None)
    
    # Phase 1 Fields
    pricing: Optional[Dict[str, Any]] = Field(default=None)
    qps_budget: Optional[float] = Field(default=None)
    concurrency_limit: Optional[int] = Field(default=None)
    vector_desc: Optional[str] = Field(default=None)
    capabilities: Optional[List[str]] = Field(default=None)
    models: Optional[List[str]] = Field(default=None)
    
    # Trust Score
    trust_score: Optional[float] = Field(default=None)
    
    # Referral System
    referral_paid: Optional[bool] = Field(default=None)
    
    # Security
    signature: Optional[str] = Field(default=None)
    manifest_signature: Optional[str] = Field(default=None)
    public_key: Optional[str] = Field(default=None)
    
    health_status: Optional[HealthStatus] = Field(default=None)
