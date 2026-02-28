"""
Autonomous Agent Handshake Demonstration.

This script demonstrates how an AI Agent can autonomously discover the AgentMesh 
registry, read its protocol manifest, register itself, find a peer, and negotiate
a capability handshake.
"""

import asyncio
import json
import httpx

REGISTRY_BASE = "http://localhost:8000"

async def autonomous_flow():
    async with httpx.AsyncClient(base_url=REGISTRY_BASE) as client:
        print("\n--- 1. Autonomous Discovery ---")
        # Step 1: Discover the protocol manifest
        print(f"Agent probing standard discovery endpoint: /.well-known/agentmesh")
        response = await client.get("/.well-known/agentmesh")
        manifest = response.json()
        print(f"Manifest Found! Version: {manifest.get('version')}")
        
        # Step 2: Read endpoint mappings
        endpoints = manifest.get("endpoints", {})
        print(f"Agent parsed dynamic endpoints: {json.dumps(endpoints, indent=2)}")

        print("\n--- 2. Autonomous Registration ---")
        # Step 3: Self-registration based on internal capabilities
        my_card = {
            "id": "autonomous-researcher-007",
            "name": "ResearchBot",
            "version": "1.0.0",
            "description": "Expert in historical data extraction and summarization.",
            "endpoint": "http://research-bot.internal:5000",
            "protocol": "http",
            "skills": [
                {"name": "extract_facts", "description": "Extract historical facts from text."}
            ],
            "tags": ["research", "nlp"]
        }
        
        reg_url = endpoints.get("register", "/api/v1/agents/register")
        print(f"Registering to {reg_url}...")
        reg_res = await client.post(reg_url, json={"agent_card": my_card})
        print(f"Registration status: {reg_res.status_code} - {reg_res.json().get('message')}")

        print("\n--- 3. Semantic Matchmaking ---")
        # Step 4: Need a partner agent
        task_need = "I need an agent that can translate historical texts from Latin to English."
        match_url = endpoints.get("match", "/api/v1/agents/match")
        print(f"Querying Matchmaker for: '{task_need}'")
        match_res = await client.post(f"{match_url}?q={task_need}")
        
        if match_res.status_code == 200:
            match_data = match_res.json().get("data", {})
            peer_id = match_data.get("agent_id")
            print(f"Best Peer Found: {match_data.get('name')} (Score: {match_data.get('score')})")
            
            # Step 5: Read instructions provided by matchmaker
            instructions = match_data.get("action_instructions", {})
            print(f"Agent-Readable Instructions: {json.dumps(instructions, indent=2)}")

            print("\n--- 4. Digital Handshake (Negotiation) ---")
            # Step 6: Negotiate based on instructions
            neg_url = endpoints.get("negotiate", f"/api/v1/agents/{peer_id}/negotiate").replace("{id}", peer_id)
            proposal = "Can you translate a 500-word Latin document about Roman agriculture?"
            print(f"Sending proposal to peer via {neg_url}...")
            neg_res = await client.post(neg_url, json={"proposal": proposal})
            
            negotiation = neg_res.json().get("data", {})
            if negotiation.get("feasible"):
                print(f"Handshake Successful! Confidence: {negotiation.get('confidence')}")
                print(f"Agent Instructions: {negotiation.get('instructions')}")
                print(f"RESULT: Peer confirmed feasibility. Ready to /invoke.")
            else:
                print("Handshake Failed. Seeking alternative peer.")
        else:
            print("No matching peer found in the mesh.")

if __name__ == "__main__":
    asyncio.run(autonomous_flow())
