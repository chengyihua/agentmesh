"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import axios from "axios";
import { Agent, AgentStats, LeaderboardAgent } from "@/types/agent";

// Default to local server, but allow overriding via window if needed
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export function useAgents(params?: { limit?: number; skip?: number; sort_by?: string; order?: string; health_status?: string; owner_id?: string }) {
    return useQuery<Agent[]>({
        queryKey: ["agents", params],
        queryFn: async () => {
            const queryParams = new URLSearchParams();
            if (params?.limit) queryParams.append("limit", params.limit.toString());
            if (params?.skip) queryParams.append("skip", params.skip.toString());
            if (params?.sort_by) queryParams.append("sort_by", params.sort_by);
            if (params?.order) queryParams.append("order", params.order);
            if (params?.health_status) queryParams.append("health_status", params.health_status);
            if (params?.owner_id) queryParams.append("owner_id", params.owner_id);
            
            const queryString = queryParams.toString();
            const url = `${API_BASE}/agents${queryString ? `?${queryString}` : ""}`;
            
            const response = await axios.get(url);
            return response.data.data.agents;
        },
    });
}

export function useAgent(id: string) {
    return useQuery<Agent>({
        queryKey: ["agent", id],
        queryFn: async () => {
            const response = await axios.get(`${API_BASE}/agents/${id}`);
            return response.data.data.agent;
        },
        enabled: !!id,
    });
}

export function useAgentStats(id: string) {
    return useQuery<AgentStats>({
        queryKey: ["agent-stats", id],
        queryFn: async () => {
            const response = await axios.get(`${API_BASE}/agents/${id}/stats`);
            return response.data.data;
        },
        enabled: !!id,
    });
}

export function useStats(options?: { refetchInterval?: number }) {
    return useQuery<AgentStats>({
        queryKey: ["stats"],
        queryFn: async () => {
            const response = await axios.get(`${API_BASE}/stats`);
            return response.data.data;
        },
        refetchInterval: options?.refetchInterval,
    });
}

export function useLeaderboard(limit = 5) {
    return useQuery<LeaderboardAgent[]>({
        queryKey: ["leaderboard", limit],
        queryFn: async () => {
            const response = await axios.get(`${API_BASE}/agents/leaderboard?limit=${limit}`);
            return response.data.data.leaderboard;
        },
    });
}

export function useClaim() {
    return useMutation({
        mutationFn: async ({ agentId, claimCode }: { agentId: string; claimCode: string }) => {
            const token = localStorage.getItem("agentmesh_token");
            if (!token) throw new Error("Must be logged in to claim agent");

            const response = await axios.post(
                `${API_BASE}/agents/bind`, 
                {
                    agent_id: agentId,
                    claim_code: claimCode,
                },
                {
                    headers: { Authorization: `Bearer ${token}` }
                }
            );
            return response.data.data;
        },
    });
}

export function useInvoke() {
    return useMutation({
        mutationFn: async ({
            agentId,
            body,
            apiKey
        }: {
            agentId: string;
            body: Record<string, unknown>;
            apiKey?: string;
        }) => {
            const headers: Record<string, string> = {};
            if (apiKey) {
                headers["X-API-Key"] = apiKey;
            }

            const response = await axios.post(
                `${API_BASE}/agents/${agentId}/invoke`,
                body,
                { headers }
            );
            return response.data.data;
        },
    });
}
