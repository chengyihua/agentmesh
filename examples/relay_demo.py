import asyncio
import os
import sys
import time
import subprocess
import signal
import httpx
import json

# Paths
PYTHON = sys.executable
# Run CLI as module
CLI = [PYTHON, "-m", "agentmesh.cli"]

# Ensure src is in PYTHONPATH
ENV = os.environ.copy()
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src"))
ENV["PYTHONPATH"] = src_path
sys.path.append(src_path)

# Import Core Modules
try:
    from agentmesh.core.security import SecurityManager
    from agentmesh.core.agent_card import AgentCard, Skill, ProtocolType
except ImportError as e:
    print(f"Error importing agentmesh modules: {e}")
    sys.exit(1)

def start_server():
    print("Starting AgentMesh Server...")
    # Use memory storage and debug mode
    proc = subprocess.Popen(
        CLI + ["serve", "--port", "8000", "--storage", "memory", "--debug"],
        stdout=sys.stdout,
        stderr=sys.stderr,
        env=ENV
    )
    return proc

def start_local_agent(port=8001):
    print(f"Starting Local Agent on port {port}...")
    # A simple FastAPI server
    code = f"""
from fastapi import FastAPI, Request
import uvicorn
import sys

app = FastAPI()

@app.post("/")
async def handle(request: Request):
    try:
        data = await request.json()
    except:
        data = {{}}
    print(f"Local Agent received: {{data}}", file=sys.stderr)
    return {{"message": "Hello from Local Agent", "echo": data}}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port={port}, log_level="warning")
"""
    proc = subprocess.Popen(
        [PYTHON, "-c", code],
        stdout=sys.stdout,
        stderr=sys.stderr,
        env=ENV
    )
    return proc

def wait_for_port(port, timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        try:
            # Check if port is listening by trying to connect
            with httpx.Client(trust_env=False) as client:
                client.get(f"http://localhost:{port}/health", timeout=1)
            return True
        except httpx.ConnectError:
            pass # Not ready
        except:
            # 404/405 means server is running
            return True
        time.sleep(0.5)
    return False

def wait_for_server_unblock(port, timeout=120):
    print("Waiting for server to unblock (model loading)...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            with httpx.Client(trust_env=False) as client:
                # Use a short timeout to detect blocking
                client.get(f"http://localhost:{port}/health", timeout=1.0)
            print("Server is responsive.")
            return True
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.PoolTimeout):
            pass
        except Exception as e:
            # print(f"Health check error: {e}")
            pass
        time.sleep(1)
    return False

async def register_agent(sm: SecurityManager, keys: dict) -> tuple[str, bool]:
    agent_id = sm.derive_agent_id(keys["public_key"])
    
    agent_card = AgentCard(
        id=agent_id,
        name="RelayDemoAgent",
        version="1.0.0",
        description="Demo agent for relay network",
        skills=[Skill(name="demo", description="Demo skill")],
        public_key=keys["public_key"],
        endpoint=f"relay://{agent_id}",
        protocol=ProtocolType.RELAY
    )
    
    # Sign manifest
    signature = await sm.sign_agent_card(agent_card, keys["private_key"])
    agent_card.manifest_signature = signature
    
    # Convert to JSON dict
    payload = agent_card.model_dump(mode='json')
    
    print(f"Registering Agent {agent_id}...")
    async with httpx.AsyncClient(trust_env=False) as client:
        resp = await client.post(
            "http://localhost:8000/api/v1/agents/register",
            json=payload,
            timeout=10.0
        )
        
    if resp.status_code != 200 and resp.status_code != 201:
        print(f"Registration failed: {resp.text}")
        return agent_id, False
        
    print("Agent Registered.")
    return agent_id, True

def main():
    server_proc = None
    agent_proc = None
    relay_proc = None
    
    try:
        # 1. Start Server
        server_proc = start_server()
        if not wait_for_port(8000):
            print("Server failed to start (timeout)")
            return
        print("Server started.")

        # 2. Register Agent
        sm = SecurityManager()
        keys = sm.generate_key_pair() # Returns dict with private_key, public_key
        
        # Run registration in async loop
        agent_id, success = asyncio.run(register_agent(sm, keys))
        if not success:
            return

        # 3. Wait for server unblock (model loading)
        if not wait_for_server_unblock(8000):
            print("Server failed to unblock (timeout)")
            return

        # 4. Start Local Agent
        agent_proc = start_local_agent()
        if not wait_for_port(8001):
            print("Local Agent failed to start (timeout)")
            return
        print("Local Agent started.")
        
        # 5. Start Relay Client (Connect)
        print("Starting Relay Client...")
        relay_proc = subprocess.Popen(
            CLI + [
                "connect",
                "--relay-url", "ws://localhost:8000",
                "--target-url", "http://127.0.0.1:8001",
                "--agent-id", agent_id,
                "--private-key", keys["private_key"]
            ],
            stdout=sys.stdout,
            stderr=sys.stderr,
            env=ENV
        )
        time.sleep(5) # Wait for connection
        
        # Check if relay client died
        if relay_proc.poll() is not None:
            print("Relay Client died immediately")
            return
            
        # 6. Invoke Agent via Relay
        print("Invoking Agent via Relay...")
        invoke_payload = {"test": "data"}
        
        start_time = time.time()
        try:
            with httpx.Client(trust_env=False) as client:
                resp = client.post(
                    f"http://localhost:8000/api/v1/agents/{agent_id}/invoke",
                    json={"payload": invoke_payload, "skill": "demo"},
                    timeout=60.0
                )
            print(f"Invoke took {time.time() - start_time:.2f}s")
            print("Invoke response code:", resp.status_code)
            print("Invoke response body:", resp.text)
            
            if resp.status_code == 200:
                result = resp.json()
                # The structure is data -> result -> response -> message
                data = result.get("data", {})
                inner_result = data.get("result", {})
                response_body = inner_result.get("response", {})
                
                if response_body.get("message") == "Hello from Local Agent":
                    print("\nSUCCESS: Relay invocation worked! The request went Server -> Relay -> CLI -> Local Agent -> Echo -> CLI -> Relay -> Server.")
                else:
                    print(f"\nFAILURE: Unexpected response content. Got: {response_body}")
            else:
                print("\nFAILURE: Unexpected status code")
        except Exception as e:
            print(f"Invoke failed: {e}")
            
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("Cleaning up...")
        if relay_proc: 
            relay_proc.terminate()
        if agent_proc: 
            agent_proc.terminate()
        if server_proc: 
            server_proc.terminate()

if __name__ == "__main__":
    main()
