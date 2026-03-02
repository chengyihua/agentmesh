"""FastAPI server wiring for AgentMesh."""

from __future__ import annotations

import logging
import secrets
from contextlib import asynccontextmanager
from typing import Optional, Union

from ..core.protocol import PROTOCOL_MANIFEST_JSON

import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from ..auth import TokenManager
from ..core.registry import AgentRegistry
from ..core.security import SecurityManager
from ..core.federation import FederationManager
from ..core.vector_index import VectorIndexManager
from ..core.rate_limit import AgentRateLimiter
from ..core.telemetry import TelemetryManager
from ..core.errors import AgentMeshError
from ..storage import MemoryStorage, PostgresStorage, RedisStorage, StorageBackend
from ..utils import error_response, success_response, utc_now_iso
from .routes import limiter as routes_limiter
from .routes import router, root_router
from .auth_routes import router as auth_router
from ..relay.routes import router as relay_router
from ..relay.manager import RelayManager
from ..protocols.relay import RelayProtocolHandler
from ..p2p.node import P2PNode

logger = logging.getLogger(__name__)
DEFAULT_AUTH_SECRET = "agentmesh-dev-secret"


class AgentMeshServer:
    """AgentMesh FastAPI server."""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        debug: bool = False,
        storage: Union[str, StorageBackend, None] = None,
        redis_url: str = "redis://localhost:6379",
        postgres_url: str = "postgresql://localhost:5432/agentmesh",
        api_key: Optional[str] = None,
        auth_secret: str = DEFAULT_AUTH_SECRET,
        production: bool = False,
        security_manager: Optional[SecurityManager] = None,
        registry: Optional[AgentRegistry] = None,
        token_manager: Optional[TokenManager] = None,
        require_signed_registration: bool = False,
        seeds: Optional[list[str]] = None,
        vector_index: Optional[VectorIndexManager] = None,
    ):
        self.host = host
        self.port = port
        self.debug = debug
        self.api_key = api_key
        self.production = production
        self.require_signed_registration = require_signed_registration
        self.seeds = seeds or []

        self._validate_security_configuration(api_key=api_key, auth_secret=auth_secret, production=production)

        self.telemetry = TelemetryManager()
        self.security_manager = security_manager or SecurityManager()
        self.storage = self._resolve_storage(storage, redis_url=redis_url, postgres_url=postgres_url)
        
        self.vector_index = vector_index or VectorIndexManager()
        self.registry = registry or AgentRegistry(
            self.security_manager, 
            storage=self.storage,
            require_signed_registration=self.require_signed_registration,
            vector_index=self.vector_index,
            telemetry=self.telemetry
        )
        self.federation = FederationManager(self.registry, seeds=self.seeds)
        self.rate_limiter = AgentRateLimiter(telemetry=self.telemetry, trust_manager=self.registry.trust_manager)
        self.relay_manager = RelayManager(self.registry, self.security_manager)
        
        # Wire RelayManager into Registry and ProtocolGateway
        self.registry.relay_manager = self.relay_manager
        
        # Configure Relay Protocol Handler in the Gateway
        if self.registry.protocol_gateway:
            handler = RelayProtocolHandler(relay_invoke=self.relay_manager.invoke)
            self.registry.protocol_gateway._handlers["relay"] = handler

        token_signing_key = self.security_manager.secret_key or secrets.token_hex(32)
        self.token_manager = token_manager or TokenManager(
            signing_key=token_signing_key,
            expected_secret=auth_secret,
        )

        self.p2p_node = P2PNode(port=self.port + 1, on_request=self._handle_p2p_request)
        self.app = self._create_app()

    async def _handle_p2p_request(self, payload: Any, addr: Tuple[str, int]) -> Any:
        """Handle incoming P2P requests by invoking the target agent via registry."""
        try:
            target_agent_id = payload.get("target_agent_id")
            if not target_agent_id:
                return {"error": "Missing target_agent_id in P2P payload"}
            
            logger.info(f"Received P2P request for agent {target_agent_id} from {addr}")
            
            # Use registry to invoke the agent
            # The registry will resolve the agent's endpoint and invoke it via HTTP
            # This acts as a bridge: P2P -> Local HTTP
            result = await self.registry.invoke_agent(
                target_agent_id,
                skill=payload.get("skill"),
                payload=payload.get("payload"),
                path=payload.get("path"),
                method=payload.get("method", "POST"),
                headers=payload.get("headers"),
                timeout_seconds=30.0
            )
            return {"status": "success", "result": result}
        except Exception as e:
            logger.error(f"P2P invocation failed: {e}")
            return {"error": str(e)}

    def _validate_security_configuration(self, api_key: Optional[str], auth_secret: str, production: bool) -> None:
        if not production:
            return

        if not api_key:
            raise ValueError("Production mode requires --api-key")

        if not auth_secret or auth_secret == DEFAULT_AUTH_SECRET:
            raise ValueError("Production mode requires a non-default --auth-secret")

    def _resolve_storage(
        self,
        storage: Union[str, StorageBackend, None],
        redis_url: str,
        postgres_url: str,
    ) -> StorageBackend:
        if storage is None or storage == "memory":
            return MemoryStorage()
        if storage == "redis":
            return RedisStorage(url=redis_url)
        if storage in {"postgres", "postgresql"}:
            return PostgresStorage(dsn=postgres_url)
        if isinstance(storage, StorageBackend):
            return storage
        raise ValueError(f"Unsupported storage backend: {storage}")

    def _create_app(self) -> FastAPI:
        @asynccontextmanager
        async def lifespan(_: FastAPI):
            import asyncio
            await self.registry.start()
            
            # Start P2P Node
            await self.p2p_node.start()
            logger.info(f"P2P Node started on port {self.p2p_node.local_port}")
            
            # Start federation sync task
            federation_task = asyncio.create_task(self.federation.start_background_sync())
            
            yield
            
            # Stop federation sync task
            federation_task.cancel()
            try:
                await federation_task
            except asyncio.CancelledError:
                pass
            
            self.p2p_node.close()
            await self.registry.stop()

        app = FastAPI(
            title="AgentMesh API",
            description="Open-source, secure, decentralized agent registration and discovery infrastructure",
            version="0.1.0",
            docs_url="/docs",
            redoc_url="/redoc",
            lifespan=lifespan,
        )

        app.state.registry = self.registry
        app.state.security_manager = self.security_manager
        app.state.token_manager = self.token_manager
        app.state.api_key = self.api_key
        app.state.federation = self.federation
        app.state.vector_index = self.vector_index
        app.state.agent_rate_limiter = self.rate_limiter
        app.state.telemetry = self.telemetry
        app.state.relay_manager = self.relay_manager
        app.state.p2p_node = self.p2p_node

        app.state.limiter = routes_limiter
        
        @app.exception_handler(RateLimitExceeded)
        async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=error_response(
                    code="RATE_LIMIT_EXCEEDED",
                    message="Rate limit exceeded",
                    details={"reason": str(exc)},
                ),
            )

        self.telemetry.instrument(app)

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self._add_exception_handlers(app)
        app.include_router(root_router)
        app.include_router(auth_router, prefix="/api/v1")
        app.include_router(router, prefix="/api/v1")
        app.include_router(relay_router)

        @app.get("/")
        async def root():
            return success_response(
                {
                    "name": "AgentMesh",
                    "version": "0.1.0",
                    "docs": "/docs",
                    "health": "/health",
                },
                message="AgentMesh API root",
            )

        @app.get("/.well-known/agentmesh")
        async def well_known_root():
            """W3C-standard discovery endpoint at root path."""
            return PROTOCOL_MANIFEST_JSON

        @app.get("/health")
        async def health_check():
            return success_response(
                {
                    "status": "healthy",
                    "timestamp": utc_now_iso(),
                    "version": "0.1.0",
                    "uptime": self.registry.get_stats().get("uptime_seconds", 0),
                },
                message="Health check passed",
            )

        @app.get("/version")
        async def version():
            return success_response(
                {
                    "version": "0.1.0",
                    "api_version": "v1",
                    "supported_protocols": ["a2a", "mcp", "http", "grpc", "websocket", "custom"],
                },
                message="Version retrieved successfully",
            )

        Instrumentator().instrument(app).expose(app)

        return app

    def _add_exception_handlers(self, app: FastAPI) -> None:
        @app.exception_handler(HTTPException)
        async def http_exception_handler(_: Request, exc: HTTPException):
            if isinstance(exc, AgentMeshError):
                return JSONResponse(
                    status_code=exc.status_code,
                    content=error_response(
                        code=exc.code,
                        message=exc.message,
                        details=exc.details,
                    ),
                )

            details = exc.detail if isinstance(exc.detail, dict) else {"reason": exc.detail}
            
            # Map status codes to protocol error codes
            error_code_map = {
                400: "BAD_REQUEST",
                401: "UNAUTHORIZED",
                403: "FORBIDDEN",
                404: "NOT_FOUND",
                429: "RATE_LIMIT_EXCEEDED",
                500: "INTERNAL_ERROR",
            }
            code = error_code_map.get(exc.status_code, str(exc.status_code))
            
            return JSONResponse(
                status_code=exc.status_code,
                content=error_response(
                    code=code,
                    message=details.get("reason", "Request failed"),
                    details=details,
                ),
            )

        @app.exception_handler(Exception)
        async def general_exception_handler(_: Request, exc: Exception):
            logger.error("Unhandled exception", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_response(
                    code="INTERNAL_ERROR",
                    message="Internal server error",
                    details=str(exc) if self.debug else None,
                ),
            )

    async def start(self) -> None:
        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="debug" if self.debug else "info",
            reload=self.debug,
        )
        server = uvicorn.Server(config)
        await server.serve()

    def run(self, host: Optional[str] = None, port: Optional[int] = None) -> None:
        uvicorn.run(
            self.app,
            host=host or self.host,
            port=port or self.port,
            log_level="debug" if self.debug else "info",
        )


async def run_server(
    host: str = "0.0.0.0", 
    port: int = 8000, 
    debug: bool = False,
    storage: Union[str, StorageBackend, None] = None
) -> None:
    server = AgentMeshServer(host=host, port=port, debug=debug, storage=storage)
    await server.start()


def create_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    debug: bool = False,
    storage: Union[str, StorageBackend, None] = None,
    redis_url: str = "redis://localhost:6379",
    postgres_url: str = "postgresql://localhost:5432/agentmesh",
    api_key: Optional[str] = None,
    auth_secret: str = DEFAULT_AUTH_SECRET,
    production: bool = False,
    require_signed_registration: bool = False,
    seeds: Optional[list[str]] = None,
) -> AgentMeshServer:
    return AgentMeshServer(
        host=host,
        port=port,
        debug=debug,
        storage=storage,
        redis_url=redis_url,
        postgres_url=postgres_url,
        api_key=api_key,
        auth_secret=auth_secret,
        production=production,
        require_signed_registration=require_signed_registration,
        seeds=seeds,
    )


if __name__ == "__main__":
    import asyncio
    import os

    storage_type = os.getenv("STORAGE_TYPE", "redis")
    print(f"Starting server with storage: {storage_type}")
    
    asyncio.run(run_server(storage=storage_type))
