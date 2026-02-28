"""AgentMesh command-line interface."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from .api.server import create_server
from .client import SyncAgentMeshClient
from .core.security import SecurityManager
from .core.agent_card import AgentCard

CONFIG_DIR = Path.home() / ".agentmesh"
CONFIG_FILE = CONFIG_DIR / "config.json"


def _load_config() -> Dict[str, Any]:
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text())
    except Exception:
        return {}


def _save_config(config: Dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2, ensure_ascii=False))


def _print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def _parse_headers(raw_headers: List[str]) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    for item in raw_headers:
        if "=" not in item:
            raise ValueError(f"Invalid header format '{item}', expected KEY=VALUE")
        key, value = item.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError("Header key cannot be empty")
        headers[key] = value
    return headers


def _resolve_endpoint(args: argparse.Namespace, config: Dict[str, Any]) -> str:
    return args.endpoint or config.get("endpoint") or "http://localhost:8000"


def _resolve_api_key(args: argparse.Namespace, config: Dict[str, Any]) -> Optional[str]:
    return args.api_key or config.get("api-key")


def _build_client(args: argparse.Namespace, config: Dict[str, Any]) -> SyncAgentMeshClient:
    return SyncAgentMeshClient(
        base_url=_resolve_endpoint(args, config),
        api_key=_resolve_api_key(args, config),
        private_key=config.get("private_key"),
        agent_id=config.get("agent_id"),
    )


def _cmd_config(args: argparse.Namespace) -> int:
    config = _load_config()

    if args.config_action == "set":
        config[args.key] = args.value
        _save_config(config)
        print(f"Set {args.key}={args.value}")
        return 0

    if args.config_action == "get":
        if args.key:
            print(config.get(args.key, ""))
        else:
            _print_json(config)
        return 0

    return 1


def _cmd_serve(args: argparse.Namespace) -> int:
    seeds = args.seeds.split(",") if args.seeds else None
    server = create_server(
        host=args.host,
        port=args.port,
        debug=args.debug,
        storage=args.storage,
        redis_url=args.redis_url,
        postgres_url=args.postgres_url,
        api_key=args.api_key,
        auth_secret=args.auth_secret,
        production=args.production,
        require_signed_registration=args.require_signed_registration,
        seeds=seeds,
    )
    server.run()
    return 0


def _cmd_keygen(args: argparse.Namespace) -> int:
    sm = SecurityManager()
    keys = sm.generate_key_pair(algorithm="ed25519")
    # Also derive ID
    agent_id = sm.derive_agent_id(keys["public_key"])
    
    output = {
        "agent_id": agent_id,
        "public_key": keys["public_key"],
        "private_key": keys["private_key"],
        "algorithm": keys["algorithm"]
    }
    
    if args.save:
        config = _load_config()
        config["agent_id"] = agent_id
        config["public_key"] = keys["public_key"]
        config["private_key"] = keys["private_key"]
        _save_config(config)
        output["saved"] = True
        
    _print_json(output)
    return 0


async def _run_network_check(args: argparse.Namespace) -> None:
    from .p2p.node import P2PNode
    
    print("🕵️  Analyzing Network Configuration...")
    print("   (This may take a few seconds via STUN)")
    
    # Use port 0 for ephemeral port
    node = P2PNode(port=0)
    try:
        await node.start()
        
        print("\n✅ Network Analysis Complete:")
        print(f"   - NAT Type:        {node.nat_type.upper()}")
        
        if node.public_endpoint:
            print(f"   - Public Endpoint: {node.public_endpoint[0]}:{node.public_endpoint[1]}")
        else:
            print("   - Public Endpoint: Unknown (STUN failed)")
            
        print(f"   - Local Endpoints: {', '.join(node.local_endpoints)}")
        
        # Interpret NAT Type
        print("\n📋 Connectivity Report:")
        friendly_nats = ("full_cone", "restricted_cone", "port_restricted_cone", "open_internet")
        
        if node.nat_type in friendly_nats:
             print("   🟢 P2P Friendly: Your network allows direct P2P connections.")
             print("      You can likely communicate directly with other agents.")
        elif node.nat_type == "symmetric":
             print("   🟡 Symmetric NAT: Direct P2P is difficult.")
             print("      You will likely need to rely on the Relay server for connectivity.")
        else:
             print("   🔴 Unknown/Blocked: Could not determine NAT type or blocked.")
             print("      Ensure UDP traffic is allowed.")
             
    except Exception as e:
        print(f"\n❌ Analysis Failed: {e}", file=sys.stderr)
    finally:
        if node.transport:
            node.transport.close()


def _cmd_network_check(args: argparse.Namespace) -> int:
    try:
        asyncio.run(_run_network_check(args))
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


async def _forward_request(target_url: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Forward a relay request to a local HTTP endpoint."""
    async with httpx.AsyncClient(trust_env=False) as client:
        # Construct URL
        path = request_data.get("path")
        # Ensure target_url doesn't end with slash and path doesn't start with slash to avoid double slash issues
        # Or handle it properly. httpx handles it well usually but let's be safe.
        url = target_url.rstrip("/")
        if path:
            url += f"/{path.lstrip('/')}"
            
        method = request_data.get("method", "POST")
        headers = request_data.get("headers") or {}
        # Remove Host header to avoid conflicts
        if "host" in headers:
            del headers["host"]
        if "Host" in headers:
            del headers["Host"]
            
        payload = request_data.get("payload") or {}
        
        try:
            print(f"Forwarding to {method} {url}")
            response = await client.request(
                method=method,
                url=url,
                json=payload,
                headers=headers,
                timeout=30.0
            )
            try:
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                print(f"Forward request failed with status {response.status_code}: {response.text}")
                return {"error": str(e), "status": "error", "details": response.text}
        except Exception as e:
            print(f"Forward request exception: {e}")
            return {"error": str(e), "status": "error"}


async def _run_connect_agent(args: argparse.Namespace, config: Dict[str, Any], client_config: Any) -> None:
    from .client import AgentMeshClient
    
    agent_id = args.agent_id or config.get("agent_id")
    private_key = args.private_key or config.get("private_key")
    
    if not agent_id or not private_key:
        print("Error: Agent ID and private key are required. Use 'agentmesh config set' or pass via arguments.", file=sys.stderr)
        return

    print(f"🔗 Connecting Agent {agent_id} to Mesh...")
    
    async with AgentMeshClient(
        base_url=client_config.base_url,
        api_key=client_config.api_key,
        agent_id=agent_id,
        private_key=private_key
    ) as client:
        
        # 1. Start P2P Node (Step 2: Network Detect)
        print(f"📡 Starting P2P Node on port {args.port}...")
        p2p_profile = await client.start_p2p(port=args.port, update_registry=False)
        print(f"   ✅ P2P Started: {p2p_profile.get('public_endpoints')}")
        print(f"   ℹ️ NAT Type: {p2p_profile.get('nat_type')}")
        
        # 2. Connect Relay (Step 3: Connect Relay)
        print(f"🔌 Connecting to Relay: {args.relay_url}...")
        
        async def relay_handler(data: Dict[str, Any]) -> Dict[str, Any]:
            print(f"📨 Received Relay Request: {data.get('method')} {data.get('path')}")
            if args.target_url:
                return await _forward_request(args.target_url, data)
            return {"status": "success", "message": "Request received by AgentMesh CLI (no target URL)"}

        relay_connected = await client.connect_relay(
            args.relay_url,
            on_request=relay_handler,
            update_registry=False
        )
        
        if relay_connected:
            print("   ✅ Relay Connected! Secure tunnel established.")
            p2p_profile["relay_endpoint"] = args.relay_url
        else:
            print("   ⚠️ Relay Connection Failed! Proceeding with P2P only.", file=sys.stderr)
            
        # 3. Register/Update (Step 4: Register)
        if not args.no_register:
            print("📝 Updating Registry...")
            update_payload = {"network_profile": p2p_profile}
            if args.webhook_url:
                 update_payload["webhook_url"] = args.webhook_url
                 print(f"   🔔 Webhook configured: {args.webhook_url}")
            
            # Exponential Backoff Retry Logic
            max_retries = 5
            base_delay = 1.0
            
            for attempt in range(max_retries):
                try:
                    await client.update_agent(agent_id, update_payload)
                    print("   ✅ Registry Updated Successfully!")
                    break
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        print(f"   ⚠️ Agent {agent_id} not found in registry. Please run 'agentmesh agents register' first.", file=sys.stderr)
                        break
                    
                    if attempt == max_retries - 1:
                        print(f"   ❌ Registry Update Failed after {max_retries} attempts: {e}", file=sys.stderr)
                    else:
                        delay = base_delay * (2 ** attempt)
                        print(f"   ⚠️ Update failed (HTTP {e.response.status_code}). Retrying in {delay}s...", file=sys.stderr)
                        await asyncio.sleep(delay)
                        
                except Exception as e:
                    if attempt == max_retries - 1:
                        print(f"   ❌ Registry Update Failed after {max_retries} attempts: {e}", file=sys.stderr)
                    else:
                        delay = base_delay * (2 ** attempt)
                        print(f"   ⚠️ Update failed: {e}. Retrying in {delay}s...", file=sys.stderr)
                        await asyncio.sleep(delay)
        
        # 4. Heartbeat Loop (Step 5: Health Monitoring)
        print("💓 Starting Heartbeat Loop...")
        async def heartbeat_loop():
            while True:
                try:
                    await asyncio.sleep(client.health_check_interval)
                    await client.send_heartbeat(agent_id)
                except asyncio.CancelledError:
                    break
                except Exception:
                    pass
        
        heartbeat_task = asyncio.create_task(heartbeat_loop())
        
        print(f"🚀 Agent {agent_id} is ONLINE and ready!")
        print("   Press Ctrl+C to stop.")
        
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            heartbeat_task.cancel()


def _cmd_connect(args: argparse.Namespace) -> int:
    try:
        # Check dependencies
        from .relay.client import RelayClient
    except ImportError:
        print("Error: 'websockets' package is required for relay functionality.", file=sys.stderr)
        print("Install it with: pip install websockets>=11.0", file=sys.stderr)
        return 1

    config = _load_config()
    # We use _build_client just to resolve base_url/api_key
    client_config = _build_client(args, config)
    
    try:
        asyncio.run(_run_connect_agent(args, config, client_config))
        return 0
    except KeyboardInterrupt:
        print("\n🛑 Stopping Agent...")
        return 0
    except Exception as e:
        print(f"Fatal Error: {e}", file=sys.stderr)
        return 1


def _cmd_agents(args: argparse.Namespace) -> int:
    config = _load_config()
    client = _build_client(args, config)

    try:
        if args.agent_action == "register":
            if args.file:
                payload = json.loads(Path(args.file).read_text())
            else:
                skills = [{"name": skill, "description": skill.replace("_", " ")} for skill in args.skill]
                if not skills:
                    skills = [{"name": "default_skill", "description": "Default skill"}]

                payload = {
                    "id": args.id,
                    "name": args.name,
                    "version": args.version,
                    "description": args.description,
                    "skills": skills,
                    "endpoint": args.endpoint_url,
                    "protocol": args.protocol,
                    "tags": args.tag,
                    "health_status": "healthy",
                    "qps_budget": args.qps_budget,
                    "concurrency_limit": args.concurrency_limit,
                    "vector_desc": args.vector_desc or args.description,
                }

            # Signing Logic
            signing_key = args.private_key or client.private_key
            if signing_key:
                sm = SecurityManager()
                try:
                    # 1. Derive public key
                    public_key = sm.get_public_key_from_private(signing_key)
                    payload["public_key"] = public_key
                    
                    # 2. Derive Agent ID
                    derived_id = sm.derive_agent_id(public_key)
                    if "id" in payload and payload["id"] != derived_id:
                        print(f"Warning: Overriding provided ID '{payload['id']}' with derived ID '{derived_id}'", file=sys.stderr)
                    payload["id"] = derived_id
                    
                    # 3. Sign Manifest
                    # Create AgentCard to ensure correct field ordering/normalization for signing
                    # We might need to handle extra fields if payload has them but AgentCard doesn't
                    # For now assume payload matches AgentCard schema
                    card = AgentCard(**payload)
                    
                    # sign_agent_card is async, but CLI is sync here.
                    # SecurityManager.sign_agent_card is async because it might use async KMS?
                    # The implementation uses _generate_ed25519_signature which is async but implementation is sync code.
                    # We can run it in loop or just call the sync helper if available.
                    # SecurityManager has sign_agent_card as async.
                    # But it has sign_data as sync helper!
                    # And _prepare_signature_data is sync.
                    
                    sig_data = sm._prepare_signature_data(card).decode("utf-8")
                    signature = sm.sign_data(sig_data, signing_key)
                    payload["manifest_signature"] = signature
                    
                except Exception as e:
                    print(f"Error signing agent card: {e}", file=sys.stderr)
                    return 1

            response = client.register_agent(payload)
            _print_json(response)
            return 0

        if args.agent_action == "list":
            response = client.list_agents(skip=args.skip, limit=args.limit)
            _print_json(response)
            return 0

        if args.agent_action == "search":
            response = client.search_agents(skill=args.skill, q=args.query)
            _print_json(response)
            return 0

        if args.agent_action == "discover":
            response = client.discover_agents(
                q=args.query,
                skill=args.skill,
                tags=args.tag if args.tag else None,
                protocol=args.protocol,
                min_trust=args.min_trust,
                limit=args.limit
            )
            _print_json(response)
            return 0

        if args.agent_action == "get":
            response = client.get_agent(args.agent_id)
            _print_json(response)
            return 0

        if args.agent_action == "trust":
            response = client.get_trust_score(args.agent_id)
            _print_json(response)
            return 0

        if args.agent_action == "update":
            payload: Dict[str, Any] = {}
            if args.name is not None:
                payload["name"] = args.name
            if args.description is not None:
                payload["description"] = args.description
            if args.endpoint_url is not None:
                payload["endpoint"] = args.endpoint_url
            if args.tags:
                payload["tags"] = args.tags
            if args.qps_budget is not None:
                payload["qps_budget"] = args.qps_budget
            if args.concurrency_limit is not None:
                payload["concurrency_limit"] = args.concurrency_limit
            if args.vector_desc:
                payload["vector_desc"] = args.vector_desc
            if args.protocol:
                payload["protocol"] = args.protocol
            response = client.update_agent(args.agent_id, payload)
            _print_json(response)
            return 0

        if args.agent_action == "delete":
            response = client.deregister_agent(args.agent_id)
            _print_json(response)
            return 0

        if args.agent_action == "invoke":
            if args.payload_file:
                payload = json.loads(Path(args.payload_file).read_text())
            else:
                payload = json.loads(args.payload) if args.payload else {}

            headers = _parse_headers(args.header)
            response = client.invoke_agent(
                args.agent_id,
                payload=payload,
                skill=args.skill,
                path=args.path,
                method=args.method,
                timeout_seconds=args.timeout,
                headers=headers or None,
            )
            _print_json(response)
            return 0

        print("Unsupported agent command", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON payload: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        client.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentmesh", description="AgentMesh CLI")
    parser.add_argument("--endpoint", default=None, help="AgentMesh API endpoint (e.g. http://localhost:8000)")
    parser.add_argument("--api-key", default=None, help="API key for authenticated requests")

    subparsers = parser.add_subparsers(dest="command", required=True)

    serve_parser = subparsers.add_parser("serve", help="Run AgentMesh API server")
    serve_parser.add_argument("--host", default="0.0.0.0")
    serve_parser.add_argument("--port", type=int, default=8000)
    serve_parser.add_argument("--debug", action="store_true")
    serve_parser.add_argument("--storage", choices=["memory", "redis", "postgres"], default="memory")
    serve_parser.add_argument("--redis-url", default="redis://localhost:6379")
    serve_parser.add_argument("--postgres-url", default="postgresql://localhost:5432/agentmesh")
    serve_parser.add_argument("--auth-secret", default="agentmesh-dev-secret")
    serve_parser.add_argument("--api-key", default=None, help="Require this API key for protected routes")
    serve_parser.add_argument(
        "--production",
        action="store_true",
        help="Enable production safety checks (requires --api-key and non-default --auth-secret)",
    )
    serve_parser.add_argument(
        "--require-signed-registration",
        action="store_true",
        help="Enforce signature verification for agent registration",
    )
    serve_parser.add_argument(
        "--seeds",
        default=None,
        help="Comma-separated list of seed nodes (e.g. http://seed1:8000,http://seed2:8000)",
    )
    serve_parser.set_defaults(handler=_cmd_serve)

    config_parser = subparsers.add_parser("config", help="Manage CLI configuration")
    config_sub = config_parser.add_subparsers(dest="config_action", required=True)

    config_set = config_sub.add_parser("set", help="Set config key")
    config_set.add_argument("key")
    config_set.add_argument("value")
    config_set.set_defaults(handler=_cmd_config)

    config_get = config_sub.add_parser("get", help="Get config key")
    config_get.add_argument("key", nargs="?")
    config_get.set_defaults(handler=_cmd_config)

    keygen = subparsers.add_parser("keygen", help="Generate new agent identity keys")
    keygen.add_argument("--save", action="store_true", help="Save keys to local config")
    keygen.set_defaults(handler=_cmd_keygen)

    connect_parser = subparsers.add_parser("connect", help="Connect agent to the mesh network (P2P + Relay)")
    connect_parser.add_argument("--relay-url", required=True, help="Relay server URL (e.g. ws://localhost:8000)")
    connect_parser.add_argument("--target-url", default=None, help="Local agent URL to forward requests to (Reverse Proxy mode)")
    connect_parser.add_argument("--agent-id", default=None, help="Agent ID")
    connect_parser.add_argument("--private-key", default=None, help="Private key for authentication")
    connect_parser.add_argument("--port", type=int, default=0, help="Local UDP port for P2P (0 for random)")
    connect_parser.add_argument("--webhook-url", default=None, help="Webhook URL for task notifications")
    connect_parser.add_argument("--no-register", action="store_true", help="Skip registering/updating with the Registry")
    connect_parser.set_defaults(handler=_cmd_connect)

    agents_parser = subparsers.add_parser("agents", help="Agent management")
    agent_sub = agents_parser.add_subparsers(dest="agent_action", required=True)

    register = agent_sub.add_parser("register", help="Register agent")
    register.add_argument("--file", default=None, help="JSON file containing full agent payload")
    register.add_argument("--id", default="cli-agent-001")
    register.add_argument("--name", default="CLIAgent")
    register.add_argument("--version", default="1.0.0")
    register.add_argument("--description", default="Command line interface agent")
    register.add_argument("--endpoint-url", default="http://localhost:8001")
    register.add_argument("--protocol", default="http")
    register.add_argument("--skill", action="append", default=[])
    register.add_argument("--tag", action="append", default=[])
    register.add_argument("--private-key", default=None, help="Base64 encoded private key to sign the registration")
    
    # Phase 1 & 5 Fields
    register.add_argument("--qps-budget", type=float, default=None, help="Global QPS budget (e.g. 10.0 or 0.5)")
    register.add_argument("--concurrency-limit", type=int, default=None, help="Max concurrent requests")
    register.add_argument("--vector-desc", default=None, help="Description for vector embedding (if different from description)")
    
    register.set_defaults(handler=_cmd_agents)

    list_cmd = agent_sub.add_parser("list", help="List agents")
    list_cmd.add_argument("--skip", type=int, default=0)
    list_cmd.add_argument("--limit", type=int, default=100)
    list_cmd.set_defaults(handler=_cmd_agents)

    search = agent_sub.add_parser("search", help="Search agents")
    search.add_argument("--skill", default=None)
    search.add_argument("--query", default=None)
    search.set_defaults(handler=_cmd_agents)

    discover = agent_sub.add_parser("discover", help="Discover agents using semantic search")
    discover.add_argument("query", nargs="?", default=None, help="Natural language query")
    discover.add_argument("--skill", default=None, help="Filter by skill")
    discover.add_argument("--tag", action="append", default=[], help="Filter by tags")
    discover.add_argument("--protocol", default=None, help="Filter by protocol")
    discover.add_argument("--min-trust", type=float, default=None, help="Minimum trust score")
    discover.add_argument("--limit", type=int, default=10, help="Limit results")
    discover.set_defaults(handler=_cmd_agents)

    get_cmd = agent_sub.add_parser("get", help="Get one agent")
    get_cmd.add_argument("agent_id")
    get_cmd.set_defaults(handler=_cmd_agents)

    update = agent_sub.add_parser("update", help="Update agent")
    update.add_argument("agent_id")
    update.add_argument("--name", default=None)
    update.add_argument("--description", default=None)
    update.add_argument("--endpoint-url", default=None)
    update.add_argument("--tags", action="append", default=[])
    update.add_argument("--qps-budget", type=float, default=None)
    update.add_argument("--concurrency-limit", type=int, default=None)
    update.add_argument("--vector-desc", default=None)
    update.add_argument("--protocol", default=None)
    update.set_defaults(handler=_cmd_agents)

    trust = agent_sub.add_parser("trust", help="Get agent trust score")
    trust.add_argument("agent_id")
    trust.set_defaults(handler=_cmd_agents)

    delete = agent_sub.add_parser("delete", help="Delete agent")
    delete.add_argument("agent_id")
    delete.set_defaults(handler=_cmd_agents)

    invoke = agent_sub.add_parser("invoke", help="Invoke agent through protocol gateway")
    invoke.add_argument("agent_id")
    invoke.add_argument("--skill", default=None, help="Skill name hint for protocol adapters")
    invoke.add_argument("--payload", default="{}", help="JSON payload string")
    invoke.add_argument("--payload-file", default=None, help="JSON file containing payload")
    invoke.add_argument("--path", default=None, help="Optional protocol-specific path override")
    invoke.add_argument("--method", default="POST", help="HTTP method (default: POST)")
    invoke.add_argument("--timeout", type=float, default=30.0, help="Timeout in seconds")
    invoke.add_argument("--header", action="append", default=[], help="Extra header in KEY=VALUE format")
    invoke.set_defaults(handler=_cmd_agents)

    p2p_parser = subparsers.add_parser("p2p", help="P2P Network Tools (Debugging)")
    p2p_sub = p2p_parser.add_subparsers(dest="p2p_action", required=True)
    
    # Note: 'p2p start' is deprecated in favor of 'connect' command
    
    p2p_connect = p2p_sub.add_parser("connect", help="Connect to agent via P2P (One-off)")
    p2p_connect.add_argument("agent_id")
    p2p_connect.add_argument("--payload", default="{}", help="JSON payload")
    p2p_connect.add_argument("--timeout", type=float, default=10.0)
    p2p_connect.add_argument("--relay-url", help="Connect to Relay Network for signaling (e.g. ws://localhost:8000)")
    p2p_connect.set_defaults(handler=_cmd_p2p)
    
    p2p_ping = p2p_sub.add_parser("ping", help="Ping agent via P2P")
    p2p_ping.add_argument("agent_id")
    p2p_ping.add_argument("--timeout", type=float, default=5.0)
    p2p_ping.add_argument("--relay-url", help="Connect to Relay Network for signaling (e.g. ws://localhost:8000)")
    p2p_ping.set_defaults(handler=_cmd_p2p)

    return parser



async def _run_p2p_logic(args: argparse.Namespace, config: Dict[str, Any], client_config: Any) -> None:
    from .client import AgentMeshClient

    async with AgentMeshClient(
        base_url=client_config.base_url,
        api_key=client_config.api_key,
        agent_id=config.get("agent_id"),
        private_key=config.get("private_key")
    ) as async_client:
        
        if args.p2p_action == "connect":
            print(f"Starting P2P node (ephemeral)...")
            await async_client.start_p2p(port=0) # Ephemeral port
            
            if args.relay_url:
                print(f"Connecting to Relay: {args.relay_url}...")
                success = await async_client.connect_relay(args.relay_url, update_registry=False)
                if success:
                    print("Relay Connected! Ready for P2P signaling.")
                else:
                    print("Relay Connection Failed!", file=sys.stderr)
            
            print(f"Connecting to {args.agent_id}...")
            payload = json.loads(args.payload) if args.payload else {}
            
            try:
                response = await async_client.invoke_agent_p2p(
                    args.agent_id,
                    payload=payload,
                    timeout=args.timeout
                )
                _print_json(response)
            except Exception as e:
                print(f"P2P Connection failed: {e}", file=sys.stderr)
                sys.exit(1)

        elif args.p2p_action == "ping":
            print(f"Starting P2P node (ephemeral)...")
            await async_client.start_p2p(port=0)
            
            if args.relay_url:
                print(f"Connecting to Relay: {args.relay_url}...")
                success = await async_client.connect_relay(args.relay_url, update_registry=False)
                if success:
                    print("Relay Connected! Ready for P2P signaling.")
                else:
                    print("Relay Connection Failed!", file=sys.stderr)
            
            print(f"Pinging {args.agent_id}...")
            latency = await async_client.ping_agent_p2p(args.agent_id, timeout=args.timeout)
            
            if latency is not None:
                print(f"Pong! Latency: {latency*1000:.2f}ms")
            else:
                print("Ping timeout or unreachable.", file=sys.stderr)
                sys.exit(1)


def _cmd_p2p(args: argparse.Namespace) -> int:
    config = _load_config()
    client_config = _build_client(args, config)
    
    try:
        asyncio.run(_run_p2p_logic(args, config, client_config))
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1



def main(argv: Optional[List[str]] = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
