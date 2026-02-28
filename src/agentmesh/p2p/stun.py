import asyncio
import socket
import struct
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# STUN Protocol constants
STUN_SERVERS = [
    ("stun.l.google.com", 19302),
    ("stun1.l.google.com", 19302),
    ("stun2.l.google.com", 19302),
    ("stun3.l.google.com", 19302),
    ("stun4.l.google.com", 19302),
]

BINDING_REQUEST = 0x0001
BINDING_RESPONSE = 0x0101
MAGIC_COOKIE = 0x2112A442

def build_stun_request() -> Tuple[bytes, bytes]:
    """
    Builds a STUN Binding Request packet.
    Returns (packet_bytes, transaction_id).
    """
    transaction_id = b''.join([struct.pack("!B", i) for i in range(12)]) # Should be random in prod
    # Header: Type(2) + Length(2) + MagicCookie(4) + TransactionID(12)
    pkt = struct.pack("!HHI12s", BINDING_REQUEST, 0, MAGIC_COOKIE, transaction_id)
    return pkt, transaction_id

def parse_stun_response(data: bytes, expected_tid: bytes = None) -> Optional[Tuple[str, int]]:
    """
    Parses a STUN Binding Response packet.
    Returns (ip, port) or None if invalid.
    """
    try:
        if len(data) < 20:
            return None
            
        msg_type, msg_len, magic_cookie, transaction_id = struct.unpack("!HHI12s", data[:20])
        
        # Verify STUN response properties
        if msg_type != BINDING_RESPONSE:
            return None
            
        if magic_cookie != MAGIC_COOKIE:
            return None
            
        if expected_tid and transaction_id != expected_tid:
            return None
            
        # Parse attributes
        idx = 20
        while idx < len(data):
            attr_type, attr_len = struct.unpack("!HH", data[idx:idx+4])
            val_start = idx + 4
            val_end = val_start + attr_len
            
            # MAPPED-ADDRESS (0x0001)
            if attr_type == 0x0001:
                # Family(1) + Port(2) + Address(4)
                # Skip first byte (zero) and family
                port = struct.unpack("!H", data[val_start+2:val_start+4])[0]
                ip_octets = data[val_start+4:val_start+8]
                ip = socket.inet_ntoa(ip_octets)
                return (ip, port)
                
            # XOR-MAPPED-ADDRESS (0x0020)
            elif attr_type == 0x0020:
                # Family(1) + X-Port(2) + X-Address(4)
                xport = struct.unpack("!H", data[val_start+2:val_start+4])[0]
                port = xport ^ (MAGIC_COOKIE >> 16)
                
                xip = struct.unpack("!I", data[val_start+4:val_start+8])[0]
                ip_int = xip ^ MAGIC_COOKIE
                ip = socket.inet_ntoa(struct.pack("!I", ip_int))
                return (ip, port)
                
            idx = val_end
            
        return None
    except Exception as e:
        logger.error(f"Error parsing STUN response: {e}")
        return None
