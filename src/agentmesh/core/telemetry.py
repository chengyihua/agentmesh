
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Gauge, Histogram
import logging
from typing import Optional
from fastapi import FastAPI

logger = logging.getLogger(__name__)

class TelemetryManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TelemetryManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.instrumentator = Instrumentator(
            should_group_status_codes=True,
            should_ignore_untemplated=True,
            should_respect_env_var=True,
            should_instrument_requests_inprogress=True,
            excluded_handlers=["/metrics", "/health"],
            env_var_name="ENABLE_METRICS",
            inprogress_name="agentmesh_inprogress_requests",
            inprogress_labels=True,
        )
        
        # Custom Metrics
        self.agent_registrations = Counter(
            "agentmesh_agent_registrations_total",
            "Total number of agent registrations",
            ["status"]
        )
        self.active_agents = Gauge(
            "agentmesh_active_agents",
            "Number of currently active agents"
        )
        self.agent_invocations = Counter(
            "agentmesh_agent_invocations_total",
            "Total number of agent invocations",
            ["agent_id", "protocol", "status"]
        )
        self.agent_discovery_requests = Counter(
            "agentmesh_discovery_requests_total",
            "Total number of discovery requests",
            ["type"] # semantic, keyword, etc.
        )
        self.trust_score_updates = Counter(
            "agentmesh_trust_score_updates_total",
            "Total number of trust score updates",
            ["agent_id", "event_type"]
        )
        self.federation_sync_ops = Counter(
            "agentmesh_federation_sync_ops_total",
            "Total number of federation sync operations",
            ["status", "seed"]
        )
        self.federated_agents_synced = Counter(
            "agentmesh_federated_agents_synced_total",
            "Number of agents synced from federation",
            ["status"]
        )
        self.signature_verifications = Counter(
            "agentmesh_signature_verifications_total",
            "Total number of signature verifications",
            ["status", "algorithm"]
        )
        self.rate_limit_rejections = Counter(
            "agentmesh_rate_limit_rejections_total",
            "Total number of rate limit rejections",
            ["agent_id", "limit_type"]
        )
        
        self._initialized = True

    def instrument(self, app: FastAPI):
        """Instrument the FastAPI app with Prometheus metrics."""
        self.instrumentator.instrument(app).expose(app)
        logger.info("Telemetry instrumented and /metrics endpoint exposed")
