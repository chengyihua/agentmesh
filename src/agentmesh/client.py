"""AgentMesh SDK clients."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union

import httpx

from .core.agent_card import AgentCard
from .core.security import SecurityManager


class _BaseClient:
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        token: Optional[str] = None,
        private_key: Optional[str] = None,
        agent_id: Optional[str] = None,
        timeout: float = 30.0,
        health_check_interval: int = 30,
        health_check_timeout: int = 10,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.token = token
        self.private_key = private_key
        self.agent_id = agent_id
        self.timeout = timeout
        self.health_check_interval = health_check_interval
        self.health_check_timeout = health_check_timeout
        self.security_manager = SecurityManager() if private_key else None

    def _headers(self, token_override: Optional[str] = None) -> Dict[str, str]:
        headers: Dict[str, str] = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        bearer = token_override or self.token
        if bearer:
            headers["Authorization"] = f"Bearer {bearer}"
        return headers
        
    def _get_auth_headers(self, method: str, path: str, json_body: Optional[Dict[str, Any]]) -> Dict[str, str]:
        if not self.private_key or not self.agent_id or not self.security_manager:
            return {}
            
        timestamp = datetime.now(timezone.utc).isoformat()
        body_hash = self.security_manager.hash_body(json_body)
        
        signature = self.security_manager.create_handshake_token(
            method=method,
            path=path,
            timestamp=timestamp,
            body_hash=body_hash,
            private_key=self.private_key
        )
        
        return {
            "X-Agent-ID": self.agent_id,
            "X-Agent-Timestamp": timestamp,
            "X-Agent-Signature": signature,
        }

    @staticmethod
    def _normalize_agent_payload(agent: Union[AgentCard, Dict[str, Any]]) -> Dict[str, Any]:
        if isinstance(agent, AgentCard):
            return agent.to_dict()
        return agent


class AgentMeshClient(_BaseClient):
    """Async AgentMesh client used in documentation examples."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._client = httpx.AsyncClient(timeout=self.timeout)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        token_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        headers = self._headers(token_override=token_override)
        headers.update(self._get_auth_headers(method, path, json_body))
        
        response = await self._client.request(
            method,
            f"{self.base_url}{path}",
            headers=headers,
            params=params,
            json=json_body,
        )
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        if hasattr(self, "p2p_node"):
            self.p2p_node.close()
        await self._client.aclose()

    async def __aenter__(self) -> "AgentMeshClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    async def start_p2p(
        self, 
        port: int = 0,
        on_request: Optional[Callable[[Any, Tuple[str, int]], Awaitable[Any]]] = None,
        update_registry: bool = False
    ) -> Dict[str, Any]:
        """
        Start P2P node and discover NAT type.
        Returns the network profile dictionary.
        
        :param update_registry: If True and agent_id is set, updates the agent's network profile in the registry.
        """
        from .p2p.node import P2PNode
        
        self.p2p_node = P2PNode(port=port, on_request=on_request)
        await self.p2p_node.start()
        
        profile = {
            "nat_type": self.p2p_node.nat_type,
            "public_endpoints": [f"{self.p2p_node.public_endpoint[0]}:{self.p2p_node.public_endpoint[1]}"] if self.p2p_node.public_endpoint else [],
            "local_endpoints": self.p2p_node.local_endpoints,
            "p2p_protocols": ["udp-json"],
        }
        
        if update_registry and self.agent_id:
            try:
                await self.update_agent(self.agent_id, {"network_profile": profile})
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Failed to update registry with P2P profile: {e}")
        
        return profile

    async def invoke_agent_p2p(
        self,
        agent_id: str,
        payload: Optional[Dict[str, Any]] = None,
        timeout: float = 10.0,
    ) -> Dict[str, Any]:
        """
        Invoke an agent directly via P2P UDP connection.
        Attempts hole punching and waits for a response.
        Uses HTTP handshake to coordinate hole punching first.
        """
        if not hasattr(self, "p2p_node"):
            raise RuntimeError("P2P node not started. Call start_p2p() first.")
            
        # 1. Get agent details to find endpoint
        agent_resp = await self.get_agent(agent_id)
        agent_data = agent_resp.get("agent", agent_resp)
        
        network_profile = agent_data.get("network_profile")
        if not network_profile:
             raise RuntimeError(f"Target agent {agent_id} has no network profile")
             
        public_endpoints = network_profile.get("public_endpoints", [])
        if not public_endpoints:
             raise RuntimeError(f"Target agent {agent_id} has no public endpoints")
             
        # Parse endpoint (assume first one is valid)
        try:
            ip, port_str = public_endpoints[0].split(":")
            port = int(port_str)
        except ValueError:
            raise RuntimeError(f"Invalid endpoint format: {public_endpoints[0]}")
            
        # 2. Perform Signaling Handshake via HTTP/Relay
        # This tells the target to start punching back to us
        target_endpoint = (ip, port)
        try:
            handshake_payload = {
                "endpoint": f"{self.p2p_node.public_endpoint[0]}:{self.p2p_node.public_endpoint[1]}"
            }
            # We use invoke_agent to send this control message
            # The target node (AgentMeshServer) should intercept this skill
            handshake_resp = await self.invoke_agent(
                agent_id, 
                skill="sys.p2p.handshake", 
                payload=handshake_payload,
                timeout_seconds=5.0
            )
            
            # If handshake returned a fresh endpoint, use it!
            if handshake_resp.get("status") == "success" and handshake_resp.get("endpoint"):
                try:
                    fresh_ip, fresh_port_str = handshake_resp["endpoint"].split(":")
                    target_endpoint = (fresh_ip, int(fresh_port_str))
                    import logging
                    logging.getLogger(__name__).info(f"Using fresh P2P endpoint from handshake: {target_endpoint}")
                except ValueError:
                    pass
                    
        except Exception as e:
            # Handshake failed? Maybe target doesn't support it or is offline.
            # We can try to proceed anyway if we think NAT is open, but likely will fail.
            import logging
            logging.getLogger(__name__).warning(f"P2P Handshake failed: {e}. Proceeding with blind punch.")
        
        # 3. Punch hole / Connect
        # Wait for handshake to propagate and target to start punching
        connected = await self.p2p_node.connect_to_peer(target_endpoint[0], target_endpoint[1])
        if not connected:
             raise TimeoutError(f"Failed to establish P2P connection to {target_endpoint[0]}:{target_endpoint[1]}")
             
        # 4. Send Request
        return await self.p2p_node.send_request(target_endpoint, payload, timeout=timeout)

    async def ping_agent_p2p(self, agent_id: str, timeout: float = 2.0) -> Optional[float]:
        """
        Ping an agent via P2P and return latency in seconds.
        Returns None if P2P unavailable or timeout.
        """
        if not hasattr(self, "p2p_node") or not self.p2p_node.transport:
            return None
            
        try:
            # 1. Get agent details to find endpoint
            agent_resp = await self.get_agent(agent_id)
            agent_data = agent_resp.get("agent", agent_resp)
            
            network_profile = agent_data.get("network_profile")
            if not network_profile:
                 return None
                 
            public_endpoints = network_profile.get("public_endpoints", [])
            if not public_endpoints:
                 return None
                 
            # Parse endpoint (assume first one is valid)
            try:
                ip, port_str = public_endpoints[0].split(":")
                port = int(port_str)
            except ValueError:
                return None
                
            # 2. Ping
            return await self.p2p_node.ping(ip, port, timeout=timeout)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"P2P Ping failed: {e}")
            return None

    async def connect_relay(
        self,
        relay_url: str,
        on_request: Optional[Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] = None,
        update_registry: bool = True
    ) -> bool:
        """
        Connect to the Relay Network to receive incoming requests (Signaling).
        This is crucial for P2P handshake reception if behind NAT.
        """
        try:
            from .relay.client import RelayClient
        except ImportError:
            import logging
            logging.getLogger(__name__).warning("RelayClient not available (websockets not installed?)")
            return False

        if not self.private_key:
             raise ValueError("Private key required for Relay connection")
             
        self._user_relay_handler = on_request
        
        self.relay_client = RelayClient(
            relay_url=relay_url,
            agent_id=self.agent_id,
            private_key=self.private_key,
            request_handler=self._handle_relay_request
        )
        
        try:
            # Start relay client in background
            self._relay_task = asyncio.create_task(self.relay_client.connect())
            
            # Wait briefly to ensure connection initiation doesn't crash immediately
            await asyncio.sleep(0.1)
            
            if update_registry:
                # Update agent profile with relay endpoint
                # The presence of relay_endpoint triggers the ProtocolGateway fallback
                await self.update_agent(self.agent_id, {
                    "network_profile": {
                        "relay_endpoint": relay_url
                    }
                })
                
            return True
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to start relay client: {e}")
            return False

    async def _handle_relay_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Internal handler for relay requests, intercepting P2P handshake."""
        skill = payload.get("skill")
        if skill == "sys.p2p.handshake":
            # Payload from invoke_agent_p2p contains: 
            # { "peer_id": ..., "endpoint": ... }
            peer_endpoint = payload.get("payload", {}).get("endpoint")
            
            if peer_endpoint and hasattr(self, "p2p_node"):
                try:
                    ip, port_str = peer_endpoint.split(":")
                    port = int(port_str)
                    # Start hole punching to peer
                    # Run in background to avoid blocking the response
                    asyncio.create_task(self.p2p_node.connect_to_peer(ip, port))
                    
                    my_endpoint = f"{self.p2p_node.public_endpoint[0]}:{self.p2p_node.public_endpoint[1]}"
                    return {
                        "status": "success", 
                        "message": "P2P Handshake accepted, punching started",
                        "endpoint": my_endpoint
                    }
                except Exception as e:
                    return {"status": "error", "message": str(e)}
        
        if hasattr(self, "_user_relay_handler") and self._user_relay_handler:
            return await self._user_relay_handler(payload)
            
        return {"status": "ignored", "message": "No handler for this request"}

    async def register_agent(self, agent: Union[AgentCard, Dict[str, Any]]) -> Dict[str, Any]:
        payload = self._normalize_agent_payload(agent)
        return await self._request("POST", "/api/v1/agents/register", json_body=payload)

    async def register_agent_with_retry(
        self, 
        agent: Union[AgentCard, Dict[str, Any]], 
        max_retries: int = 5,
        base_delay: float = 1.0
    ) -> Dict[str, Any]:
        """
        Register agent with exponential backoff retry.
        Handles temporary failures or network issues.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        for attempt in range(max_retries):
            try:
                return await self.register_agent(agent)
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Registration failed after {max_retries} attempts: {e}")
                    raise e
                
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    f"Registration failed (attempt {attempt+1}/{max_retries}): {e}. Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)
        return {} # Should not reach here

    async def register_or_update_agent_with_retry(
        self,
        agent: Union[AgentCard, Dict[str, Any]],
        max_retries: int = 5,
        base_delay: float = 1.0
    ) -> Dict[str, Any]:
        """
        Register or update agent with exponential backoff retry.
        If registration fails because agent exists, it updates instead.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        agent_payload = self._normalize_agent_payload(agent)
        agent_id = agent_payload.get("id") or self.agent_id
        
        if not agent_id:
            raise ValueError("Agent ID required for registration/update")

        for attempt in range(max_retries):
            try:
                # Try to register first
                try:
                    return await self.register_agent(agent_payload)
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 400 and "already exists" in e.response.text:
                        # Agent exists, update instead
                        logger.info(f"Agent {agent_id} already exists, updating...")
                        # For update, we might need to filter payload to allowed fields?
                        # But update_agent takes dict, registry handles filtering.
                        # However, register payload has everything.
                        # We should probably only update relevant fields if we want to be safe,
                        # but update_agent implementation in registry replaces fields present in update_data.
                        # So sending full payload is effectively a full update (except immutable fields like created_at).
                        return await self.update_agent(agent_id, agent_payload)
                    raise e
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Register/Update failed after {max_retries} attempts: {e}")
                    raise e
                
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    f"Register/Update failed (attempt {attempt+1}/{max_retries}): {e}. Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)
        return {}

    async def get_agent(self, agent_id: str) -> Dict[str, Any]:
        return await self._request("GET", f"/api/v1/agents/{agent_id}")

    async def list_agents(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        return await self._request("GET", "/api/v1/agents", params={"skip": skip, "limit": limit})

    async def update_agent(self, agent_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request("PUT", f"/api/v1/agents/{agent_id}", json_body=update_data)

    async def deregister_agent(self, agent_id: str) -> Dict[str, Any]:
        return await self._request("DELETE", f"/api/v1/agents/{agent_id}")

    async def delete_agent(self, agent_id: str) -> Dict[str, Any]:
        return await self.deregister_agent(agent_id)

    async def search_agents(
        self,
        q: Optional[str] = None,
        skill: Optional[str] = None,
        tags: Optional[List[str]] = None,
        protocol: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "limit": limit,
            "offset": offset,
        }
        if q:
            params["q"] = q
        if skill:
            params["skill"] = skill
        if tags:
            params["tags"] = tags
        if protocol:
            params["protocol"] = protocol
        return await self._request("GET", "/api/v1/agents/search", params=params)

    async def discover_agents(
        self,
        q: Optional[str] = None,
        skill: Optional[str] = None,
        tags: Optional[List[str]] = None,
        protocol: Optional[str] = None,
        min_trust: Optional[float] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Discover agents using semantic search."""
        params: Dict[str, Any] = {
            "limit": limit,
            "offset": offset,
        }
        if q:
            params["q"] = q
        if skill:
            params["skill"] = skill
        if tags:
            params["tags"] = tags
        if protocol:
            params["protocol"] = protocol
        if min_trust is not None:
            params["min_trust"] = min_trust
        return await self._request("GET", "/api/v1/agents/discover", params=params)

    async def send_heartbeat(
        self,
        agent_id: str,
        status: str = "healthy",
        timestamp: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"status": status}
        if timestamp is not None:
            payload["timestamp"] = timestamp.isoformat()
        return await self._request("POST", f"/api/v1/agents/{agent_id}/heartbeat", json_body=payload)

    async def check_agent_health(self, agent_id: str) -> Dict[str, Any]:
        return await self._request("GET", f"/api/v1/agents/{agent_id}/health")

    async def batch_health_check(self, agent_ids: List[str]) -> Dict[str, Any]:
        return await self._request("POST", "/api/v1/agents/health/check", json_body={"agent_ids": agent_ids})

    async def get_stats(self) -> Dict[str, Any]:
        return await self._request("GET", "/api/v1/stats")

    async def get_trust_score(self, agent_id: str) -> Dict[str, Any]:
        return await self._request("GET", f"/api/v1/agents/{agent_id}/trust")

    async def get_agent_stats(self, agent_id: str) -> Dict[str, Any]:
        return await self._request("GET", f"/api/v1/agents/{agent_id}/stats")

    async def invoke_agent(
        self,
        agent_id: str,
        payload: Optional[Dict[str, Any]] = None,
        *,
        skill: Optional[str] = None,
        path: Optional[str] = None,
        method: str = "POST",
        timeout_seconds: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        # Smart Routing: Try P2P if available
        # Skip P2P for handshake messages to avoid infinite recursion
        if skill != "sys.p2p.handshake" and hasattr(self, "p2p_node") and self.p2p_node.transport:
            try:
                # Prepare payload wrapper for P2P
                p2p_payload = {
                    "target_agent_id": agent_id,
                    "skill": skill,
                    "payload": payload,
                    "path": path,
                    "method": method,
                    "headers": headers
                }
                return await self.invoke_agent_p2p(agent_id, p2p_payload, timeout=timeout_seconds)
            except Exception:
                # P2P attempt failed, falling back to Relay/HTTP
                pass

        request_body: Dict[str, Any] = {
            "payload": payload or {},
            "method": method,
            "timeout_seconds": timeout_seconds,
        }
        if skill:
            request_body["skill"] = skill
        if path:
            request_body["path"] = path
        if headers:
            request_body["headers"] = headers
        return await self._request("POST", f"/api/v1/agents/{agent_id}/invoke", json_body=request_body)

    async def get_token(self, agent_id: str, secret: str) -> Dict[str, Any]:
        return await self._request("POST", "/api/v1/auth/token", json_body={"agent_id": agent_id, "secret": secret})

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        return await self._request("POST", "/api/v1/auth/refresh", json_body={"refresh_token": refresh_token})

    async def verify_token(self, token: Optional[str] = None) -> Dict[str, Any]:
        return await self._request("GET", "/api/v1/auth/verify", token_override=token)

    async def clear_cache(self) -> Dict[str, Any]:
        return await self._request("POST", "/api/v1/cache/clear")


class SyncAgentMeshClient(_BaseClient):
    """Synchronous convenience client for scripts/CLI."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        # Disable trust_env to avoid proxy issues with localhost
        self._client = httpx.Client(timeout=self.timeout, trust_env=False)

    def close(self) -> None:
        self._client.close()

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        token_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        headers = self._headers(token_override=token_override)
        headers.update(self._get_auth_headers(method, path, json_body))

        response = self._client.request(
            method,
            f"{self.base_url}{path}",
            headers=headers,
            params=params,
            json=json_body,
        )
        response.raise_for_status()
        return response.json()

    def register_agent(self, agent: Union[AgentCard, Dict[str, Any]]) -> Dict[str, Any]:
        return self._request("POST", "/api/v1/agents/register", json_body=self._normalize_agent_payload(agent))

    def list_agents(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        return self._request("GET", "/api/v1/agents", params={"skip": skip, "limit": limit})

    def get_agent(self, agent_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/api/v1/agents/{agent_id}")

    def update_agent(self, agent_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("PUT", f"/api/v1/agents/{agent_id}", json_body=update_data)

    def deregister_agent(self, agent_id: str) -> Dict[str, Any]:
        return self._request("DELETE", f"/api/v1/agents/{agent_id}")

    def get_trust_score(self, agent_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/api/v1/agents/{agent_id}/trust")

    def invoke_agent(
        self,
        agent_id: str,
        payload: Optional[Dict[str, Any]] = None,
        *,
        skill: Optional[str] = None,
        path: Optional[str] = None,
        method: str = "POST",
        timeout_seconds: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        request_body: Dict[str, Any] = {
            "payload": payload or {},
            "method": method,
            "timeout_seconds": timeout_seconds,
        }
        if skill:
            request_body["skill"] = skill
        if path:
            request_body["path"] = path
        if headers:
            request_body["headers"] = headers
        return self._request("POST", f"/api/v1/agents/{agent_id}/invoke", json_body=request_body)

    def search_agents(
        self,
        q: Optional[str] = None,
        skill: Optional[str] = None,
        tags: Optional[List[str]] = None,
        protocol: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "limit": limit,
            "offset": offset,
        }
        if q:
            params["q"] = q
        if skill:
            params["skill"] = skill
        if tags:
            params["tags"] = tags
        if protocol:
            params["protocol"] = protocol
        return self._request("GET", "/api/v1/agents/search", params=params)

    def discover_agents(
        self,
        q: Optional[str] = None,
        skill: Optional[str] = None,
        tags: Optional[List[str]] = None,
        protocol: Optional[str] = None,
        min_trust: Optional[float] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Discover agents using semantic search."""
        params: Dict[str, Any] = {
            "limit": limit,
            "offset": offset,
        }
        if q:
            params["q"] = q
        if skill:
            params["skill"] = skill
        if tags:
            params["tags"] = tags
        if protocol:
            params["protocol"] = protocol
        if min_trust is not None:
            params["min_trust"] = min_trust
        return self._request("GET", "/api/v1/agents/discover", params=params)
