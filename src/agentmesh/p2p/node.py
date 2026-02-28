import asyncio
import json
import logging
import socket
import uuid
from typing import Dict, Optional, Tuple, Callable, Any, List

from .stun import build_stun_request, parse_stun_response, STUN_SERVERS

logger = logging.getLogger(__name__)

class P2PNode(asyncio.DatagramProtocol):
    def __init__(self, port: int = 0, on_message: Optional[Callable] = None, on_request: Optional[Callable] = None):
        self.local_port = port
        self.transport = None
        self.public_endpoint: Optional[Tuple[str, int]] = None
        self.local_endpoints: List[str] = []
        self.nat_type = "unknown"
        self.peers: Dict[str, Tuple[str, int]] = {} # peer_id -> (ip, port)
        self.on_message = on_message
        self.on_request = on_request
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.pending_connections: Dict[Tuple[str, int], asyncio.Future] = {}
        self.pending_pings: Dict[str, asyncio.Future] = {}
        self.stun_transactions: Dict[bytes, asyncio.Future] = {}
        self.loop = None

    def connection_made(self, transport):
        self.transport = transport
        # Update local port if it was 0 (ephemeral)
        sock = transport.get_extra_info('socket')
        if sock:
            self.local_port = sock.getsockname()[1]
        logger.info(f"P2P Node listening on UDP port {self.local_port}")

    def datagram_received(self, data, addr):
        # Check for STUN packet first
        if len(data) >= 20 and data[0] in (0x00, 0x01):
             # Extract Transaction ID manually to look up future
             # Header: Type(2) + Length(2) + MagicCookie(4) + TransactionID(12)
             transaction_id = data[8:20]
             if transaction_id in self.stun_transactions:
                 result = parse_stun_response(data, expected_tid=transaction_id)
                 if result:
                     future = self.stun_transactions.pop(transaction_id)
                     if not future.done():
                         future.set_result(result)
                 return

        try:
            message = json.loads(data.decode())
            msg_type = message.get("type")
            
            if msg_type == "punch":
                logger.info(f"Received PUNCH from {addr}")
                # Respond with ACK to confirm hole punching
                self.send_message(addr, {"type": "ack", "payload": "punch_ack"})
                
                # If we were also trying to connect to them, mark as success
                if addr in self.pending_connections and not self.pending_connections[addr].done():
                    self.pending_connections[addr].set_result(True)
                
            elif msg_type == "ack":
                logger.info(f"Received ACK from {addr}, connection established")
                if addr in self.pending_connections and not self.pending_connections[addr].done():
                    self.pending_connections[addr].set_result(True)

            elif msg_type == "ping":
                # Respond with PONG
                self.send_message(addr, {"type": "pong", "id": message.get("id")})

            elif msg_type == "pong":
                # Handle PONG
                ping_id = message.get("id")
                if ping_id and ping_id in self.pending_pings:
                    future = self.pending_pings.pop(ping_id)
                    if not future.done():
                        future.set_result(True)
                
            elif msg_type == "data":
                if self.on_message:
                    asyncio.create_task(self.on_message(message.get("payload"), addr))

            elif msg_type == "request":
                # Handle incoming request
                request_id = message.get("request_id")
                payload = message.get("payload")
                if self.on_request and request_id:
                    asyncio.create_task(self._handle_request(request_id, payload, addr))
            
            elif msg_type == "response":
                # Handle incoming response
                request_id = message.get("request_id")
                payload = message.get("payload")
                if request_id and request_id in self.pending_requests:
                    future = self.pending_requests.pop(request_id)
                    if not future.done():
                        future.set_result(payload)
                    
        except json.JSONDecodeError:
            logger.warning(f"Received invalid JSON from {addr}")
        except Exception as e:
            logger.error(f"Error processing UDP packet: {e}")

    async def _handle_request(self, request_id: str, payload: Any, addr: Tuple[str, int]):
        try:
            if self.on_request:
                response_payload = await self.on_request(payload, addr)
            else:
                response_payload = {"error": "No handler registered"}
                
            self.send_message(addr, {
                "type": "response",
                "request_id": request_id,
                "payload": response_payload
            })
        except Exception as e:
            logger.error(f"Error handling request {request_id}: {e}")
            self.send_message(addr, {
                "type": "response",
                "request_id": request_id,
                "payload": {"error": str(e)}
            })

    def error_received(self, exc):
        logger.error(f"P2P UDP error: {exc}")

    async def start(self):
        """Start the P2P node."""
        self.loop = asyncio.get_running_loop()
        
        # Create UDP endpoint
        transport, protocol = await self.loop.create_datagram_endpoint(
            lambda: self,
            local_addr=('0.0.0.0', self.local_port)
        )
        self.transport = transport
        
        # Update local port if it was 0 (ephemeral)
        sock = transport.get_extra_info('socket')
        if sock:
            self.local_port = sock.getsockname()[1]
            
        # Discover local IPs
        self.local_endpoints = self._get_local_ips()
        
        # Start STUN discovery
        # We await this so that start() returns with a populated network profile
        try:
            await self.discover_public_endpoint()
        except Exception as e:
            logger.warning(f"Initial NAT discovery failed: {e}")
        
        logger.info(f"P2P Node started on port {self.local_port}, local endpoints: {self.local_endpoints}, NAT: {self.nat_type}")

    def _get_local_ips(self) -> List[str]:
        """Get all local non-loopback IP addresses."""
        ips = []
        try:
            # Use hostname to get IPs
            hostname = socket.gethostname()
            # Get all addresses for hostname
            for info in socket.getaddrinfo(hostname, None):
                ip = info[4][0]
                if ip not in ips and not ip.startswith('127.'):
                    ips.append(f"{ip}:{self.local_port}")
            
            # Fallback: connect to a public DNS to get primary interface IP
            # This doesn't actually send data
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                endpoint = f"{ip}:{self.local_port}"
                if endpoint not in ips:
                    ips.append(endpoint)
        except Exception as e:
            logger.warning(f"Failed to detect local IPs: {e}")
            
        return ips

    async def discover_public_endpoint(self, timeout: float = 2.0) -> Optional[Tuple[str, int]]:
        """
        Discover public endpoint using STUN servers.
        Uses the existing transport socket to ensure mapping validity.
        Determines NAT type by checking multiple servers.
        """
        endpoints = []
        
        # Select 2 distinct STUN servers for NAT type detection
        servers = STUN_SERVERS[:2]
        
        for server_host, server_port in servers:
            try:
                # Resolve IP (run in executor to avoid blocking loop)
                addr_info = await self.loop.run_in_executor(
                    None, 
                    socket.getaddrinfo, 
                    server_host, server_port, 
                    socket.AF_INET, socket.SOCK_DGRAM
                )
                if not addr_info:
                    continue
                    
                target_ip = addr_info[0][4][0]
                target_port = addr_info[0][4][1]
                
                pkt, tid = build_stun_request()
                future = self.loop.create_future()
                self.stun_transactions[tid] = future
                
                self.transport.sendto(pkt, (target_ip, target_port))
                
                try:
                    result = await asyncio.wait_for(future, timeout)
                    endpoints.append(result)
                except asyncio.TimeoutError:
                    self.stun_transactions.pop(tid, None)
                    continue
            except Exception as e:
                logger.warning(f"STUN failed with {server_host}: {e}")
                continue
                
        if not endpoints:
            return None
            
        # Determine NAT type
        primary = endpoints[0]
        self.public_endpoint = primary
        
        if len(endpoints) > 1:
            secondary = endpoints[1]
            if primary == secondary:
                self.nat_type = "full_cone" # Consistent mapping
            else:
                self.nat_type = "symmetric" # Port/IP changed
        else:
            # Fallback heuristic if only 1 server responded
            if primary[1] == self.local_port:
                 self.nat_type = "full_cone"
            else:
                 self.nat_type = "restricted"
                 
        return primary

    def send_message(self, addr: Tuple[str, int], message: dict):
        if self.transport:
            data = json.dumps(message).encode()
            self.transport.sendto(data, addr)

    async def send_request(self, addr: Tuple[str, int], payload: Any, timeout: float = 10.0) -> Any:
        request_id = str(uuid.uuid4())
        future = self.loop.create_future()
        self.pending_requests[request_id] = future
        
        self.send_message(addr, {
            "type": "request",
            "request_id": request_id,
            "payload": payload
        })
        
        try:
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            self.pending_requests.pop(request_id, None)
            raise TimeoutError(f"Request {request_id} to {addr} timed out")

    async def connect_to_peer(self, peer_ip: str, peer_port: int, timeout: float = 5.0) -> bool:
        """
        Initiate hole punching to a peer.
        Returns True if connection established (ACK received), False otherwise.
        """
        addr = (peer_ip, peer_port)
        logger.info(f"Initiating hole punching to {addr}")
        
        if addr in self.pending_connections:
            # Already connecting or connected? 
            # If future is done, it might be an old one, but we pop it in finally.
            # So if it's here, it's in progress.
            try:
                await asyncio.wait_for(asyncio.shield(self.pending_connections[addr]), timeout=timeout)
                return True
            except asyncio.TimeoutError:
                return False

        future = self.loop.create_future()
        self.pending_connections[addr] = future
        
        try:
            # Send punch packets in a loop until ACK or timeout
            start_time = self.loop.time()
            while self.loop.time() - start_time < timeout:
                if future.done():
                    return True
                
                self.send_message(addr, {"type": "punch"})
                
                # Wait a bit before next punch, but return immediately if future is done
                try:
                    await asyncio.wait_for(asyncio.shield(future), timeout=0.5)
                    return True
                except asyncio.TimeoutError:
                    pass # Continue punching
                    
            logger.warning(f"Hole punching to {addr} timed out")
            return False
        finally:
            self.pending_connections.pop(addr, None)

    async def ping(self, peer_ip: str, peer_port: int, timeout: float = 2.0) -> Optional[float]:
        """
        Send a ping to peer and return round-trip time in seconds.
        Returns None if timeout.
        """
        ping_id = str(uuid.uuid4())
        addr = (peer_ip, peer_port)
        future = self.loop.create_future()
        self.pending_pings[ping_id] = future
        
        start_time = self.loop.time()
        self.send_message(addr, {"type": "ping", "id": ping_id})
        
        try:
            await asyncio.wait_for(future, timeout)
            return self.loop.time() - start_time
        except asyncio.TimeoutError:
            return None
        finally:
            self.pending_pings.pop(ping_id, None)

    def close(self):
        if self.transport:
            self.transport.close()
