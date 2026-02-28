export interface TrustEvent {
  timestamp: string;
  event: "success" | "heartbeat" | "decay" | "failure";
  delta: number;
  score: number;
}

export interface TrustBreakdown {
  availability: number;
  reliability: number;
  performance: number;
  history: TrustEvent[];
}

export interface AgentStats {
  total_invocations: number;
  error_rate: number;
  avg_latency: number;
  trust_breakdown?: TrustBreakdown;
  healthy_agents?: number;
  total_agents?: number;
}

export interface Skill {
  name: string;
  description: string;
  schema?: Record<string, unknown>;
}

export interface Agent {
  id: string;
  name: string;
  version: string;
  description: string;
  endpoint: string;
  protocol?: string;
  auth_required?: boolean;
  permissions?: string[];
  skills?: Skill[];
  species_id?: string;
  trust_score?: number;
  health_status?: "healthy" | "unhealthy" | "degraded";
  last_heartbeat?: string;
  tags: string[];
}

export interface ApiError {
  response?: {
    data?: {
      error?: {
        message?: string;
      };
      detail?: {
        reason?: string;
      };
    };
  };
  message: string;
}
