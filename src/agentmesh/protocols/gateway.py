"""Protocol gateway that dispatches invocation requests by protocol."""

from __future__ import annotations

from importlib.util import find_spec
from typing import Optional

from ..core.agent_card import AgentCard, NATType
from .a2a import A2AProtocolHandler
from .base import (
    HttpRequestFn,
    InvocationRequest,
    InvocationResult,
    ProtocolNotImplementedError,
    RelayInvokeFn,
)
from .grpc import GrpcInvokeFn, GrpcProtocolHandler
from .http_custom import HttpCustomProtocolHandler
from .mcp import MCPProtocolHandler
from .websocket import WebsocketInvokeFn, WebsocketProtocolHandler
from .relay import RelayProtocolHandler


class ProtocolGateway:
    """Dispatch protocol invocation to concrete handlers."""

    def __init__(
        self,
        http_request: Optional[HttpRequestFn] = None,
        websocket_invoke: Optional[WebsocketInvokeFn] = None,
        grpc_invoke: Optional[GrpcInvokeFn] = None,
        relay_invoke: Optional[RelayInvokeFn] = None,
    ):
        self._has_custom_websocket_invoke = websocket_invoke is not None
        self._has_custom_grpc_invoke = grpc_invoke is not None
        self._handlers = {
            "http": HttpCustomProtocolHandler(http_request=http_request),
            "custom": HttpCustomProtocolHandler(http_request=http_request),
            "a2a": A2AProtocolHandler(http_request=http_request),
            "mcp": MCPProtocolHandler(http_request=http_request),
            "websocket": WebsocketProtocolHandler(websocket_invoke=websocket_invoke),
            "grpc": GrpcProtocolHandler(grpc_invoke=grpc_invoke),
            "relay": RelayProtocolHandler(relay_invoke=relay_invoke),
        }

    async def invoke(self, agent: AgentCard, request: InvocationRequest) -> InvocationResult:
        # Mock logic for seed/demo agents to ensure playground functionality
        if agent.id in [
            "weather-bot-001", "crypto-analyst-pro", "code-reviewer-ai", 
            "travel-planner-v2", "legal-doc-summarizer", "health-tracker-iot"
        ]:
            return self._mock_invoke(agent.id, request)

        protocol = agent.protocol.value if hasattr(agent.protocol, "value") else str(agent.protocol)

        handler = self._handlers.get(protocol)
        if handler is None:
            raise ProtocolNotImplementedError(f"Protocol '{protocol}' invocation bridge is not implemented")

        request.protocol = protocol
        request.endpoint = str(agent.endpoint)

        # Smart Fallback Strategy:
        # If P2P (direct) fails, try Relay if available
        # Currently we don't have full P2P implementation, but we can simulate the "Brain" logic:
        # 1. Try primary protocol (e.g. HTTP/Direct)
        # 2. If fails and agent has relay_endpoint/relay protocol support, fallback to Relay
        
        # Smart Routing: Prioritize Relay for difficult NATs or Unknown NAT
        # This aligns with the "Brain" logic: if we know direct connection is unlikely to succeed,
        # we try Relay first to save time and improve success rate.
        original_protocol = request.protocol
        original_endpoint = request.endpoint
        relay_attempted = False

        if (
            agent.network_profile 
            and agent.network_profile.relay_endpoint
            and agent.network_profile.nat_type in (NATType.UNKNOWN, NATType.SYMMETRIC)
        ):
            relay_handler = self._handlers.get("relay")
            if relay_handler:
                try:
                    request.protocol = "relay"
                    request.endpoint = agent.network_profile.relay_endpoint
                    result = await relay_handler.invoke(request)
                    relay_attempted = True
                    return result
                except Exception:
                    # Reset request for fallback to direct
                    request.protocol = original_protocol
                    request.endpoint = original_endpoint
                    # Continue to standard flow

        try:
            return await handler.invoke(request)
        except Exception as e:
            # Smart Fallback Strategy:
            # If P2P/Direct fails, check if we can fallback to Relay
            # Skip if we already tried relay and failed
            if relay_attempted:
                raise e

            if (
                protocol in ["http", "a2a", "custom"]
                and agent.network_profile
                and agent.network_profile.relay_endpoint
            ):
                # Brain Logic: Target is not reachable directly (maybe NAT), but has a relay
                relay_handler = self._handlers.get("relay")
                if relay_handler:
                    # Update request to use relay protocol
                    request.protocol = "relay"
                    request.endpoint = agent.network_profile.relay_endpoint
                    return await relay_handler.invoke(request)
            
            # If no fallback possible or fallback failed, raise original error
            raise e

    def _mock_invoke(self, agent_id: str, request: InvocationRequest) -> InvocationResult:
        import random
        from datetime import datetime, timedelta

        skill = request.skill or "default"
        payload = request.payload or {}
        
        # Simulate network latency
        import time
        # In async context we should ideally use asyncio.sleep but here we keep it simple for mock
        # or assume it's fast enough. Since this is sync-looking code in async func, let's just proceed.

        data = {}
        
        if agent_id == "weather-bot-001":
            location = payload.get("location", "Unknown Location")
            if skill == "get_forecast":
                data = {
                    "location": location,
                    "forecast": [
                        {"day": "Today", "temp": random.randint(20, 30), "condition": "Sunny"},
                        {"day": "Tomorrow", "temp": random.randint(18, 28), "condition": "Cloudy"},
                        {"day": "Day 3", "temp": random.randint(15, 25), "condition": "Rain"}
                    ]
                }
            else: # current_weather
                data = {
                    "location": location,
                    "temp": random.randint(15, 30),
                    "condition": random.choice(["Sunny", "Cloudy", "Rainy", "Windy"]),
                    "humidity": random.randint(30, 80),
                    "wind_speed": f"{random.randint(5, 20)} km/h"
                }
                
        elif agent_id == "crypto-analyst-pro":
            symbol = payload.get("symbol", "BTC-USD")
            if skill == "get_price":
                base_price = 50000 if "BTC" in symbol else 3000
                price = base_price * (1 + random.uniform(-0.05, 0.05))
                data = {
                    "symbol": symbol,
                    "price": round(price, 2),
                    "change_24h": f"{random.uniform(-5, 5):.2f}%",
                    "volume": f"{random.randint(1, 10)}B"
                }
            else: # sentiment
                data = {
                    "symbol": symbol,
                    "sentiment_score": round(random.uniform(0, 1), 2),
                    "social_volume": "High",
                    "trending_keywords": ["bullish", "moon", "upgrade"]
                }
                
        elif agent_id == "code-reviewer-ai":
            repo = payload.get("repo_url", "unknown/repo")
            if skill == "review_pr":
                data = {
                    "repo": repo,
                    "status": "Review Complete",
                    "issues_found": random.randint(0, 5),
                    "suggestions": [
                        {"file": "main.py", "line": 42, "comment": "Consider using list comprehension here."},
                        {"file": "utils.py", "line": 10, "comment": "Missing type hint for return value."}
                    ]
                }
            else:
                data = {"status": "Linting fixes applied", "files_changed": ["src/app.py", "tests/test_api.py"]}

        elif agent_id == "travel-planner-v2":
            dest = payload.get("destination", "Paris")
            data = {
                "destination": dest,
                "flights": [
                    {"airline": "AirMesh", "price": "$450", "duration": "8h 30m"},
                    {"airline": "SkyNet", "price": "$380", "duration": "10h 15m"}
                ],
                "hotels": [
                    {"name": "Grand Hotel", "rating": 4.5, "price_per_night": "$200"},
                    {"name": "Cozy Hostel", "rating": 4.0, "price_per_night": "$80"}
                ]
            }

        elif agent_id == "legal-doc-summarizer":
            data = {
                "summary": "This document outlines a service agreement between Party A and Party B. Key obligations include monthly payments and confidentiality.",
                "risk_level": "Low",
                "flagged_clauses": []
            }

        elif agent_id == "health-tracker-iot":
            data = {
                "user_id": payload.get("user_id", "anonymous"),
                "heart_rate": {
                    "current": random.randint(60, 100),
                    "avg_resting": 65,
                    "status": "Normal"
                },
                "steps": random.randint(5000, 15000)
            }
            
        else:
            data = {"message": f"Mock response for {agent_id} invoking {skill}", "payload_received": payload}

        return InvocationResult(
            protocol="mock",
            target_url=f"mock://{agent_id}",
            ok=True,
            status_code=200,
            response=data,
            response_headers={"Content-Type": "application/json", "X-Mocked": "true"},
            latency_ms=random.randint(50, 500)
        )

    def get_protocols(self):
        grpc_available = self._has_custom_grpc_invoke or find_spec("grpc") is not None
        websocket_available = self._has_custom_websocket_invoke or find_spec("websockets") is not None
        return {
            "http": {"implemented": True, "available": True, "dependency": None},
            "custom": {"implemented": True, "available": True, "dependency": None},
            "a2a": {"implemented": True, "available": True, "dependency": None},
            "mcp": {"implemented": True, "available": True, "dependency": None},
            "grpc": {
                "implemented": True,
                "available": grpc_available,
                "dependency": "grpcio",
            },
            "websocket": {
                "implemented": True,
                "available": websocket_available,
                "dependency": "websockets",
            },
            "relay": {
                "implemented": True,
                "available": True,
                "dependency": None,
            },
        }
