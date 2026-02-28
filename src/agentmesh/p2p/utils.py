import asyncio
import logging
from typing import Optional

from agentmesh.core.agent_card import NetworkProfile, NATType
from agentmesh.p2p.node import P2PNode

logger = logging.getLogger(__name__)

async def get_network_profile(stun_timeout: float = 5.0) -> NetworkProfile:
    """
    Detects the current network environment and returns a NetworkProfile.
    
    This function starts a temporary P2P node on an ephemeral port,
    performs STUN discovery to detect NAT type and public endpoint,
    and returns the profile.
    
    Args:
        stun_timeout: Max time to wait for STUN discovery in seconds.
        
    Returns:
        NetworkProfile object containing NAT type and endpoints.
    """
    # Use port 0 for ephemeral port
    node = P2PNode(port=0)
    try:
        # Start node and wait for STUN discovery
        # The node.start() method already awaits discovery internally, 
        # but we can add a timeout safety just in case
        await asyncio.wait_for(node.start(), timeout=stun_timeout)
        
        # Map internal string type to NATType enum
        nat_type_str = node.nat_type.lower()
        try:
            nat_type = NATType(nat_type_str)
        except ValueError:
            nat_type = NATType.UNKNOWN
            
        public_endpoints = []
        if node.public_endpoint:
            public_endpoints.append(f"{node.public_endpoint[0]}:{node.public_endpoint[1]}")
            
        return NetworkProfile(
            nat_type=nat_type,
            local_endpoints=node.local_endpoints,
            public_endpoints=public_endpoints,
            p2p_protocols=["udp-json"]
        )
        
    except asyncio.TimeoutError:
        logger.warning("Network profile detection timed out")
        return NetworkProfile(
            nat_type=NATType.UNKNOWN,
            local_endpoints=node.local_endpoints
        )
    except Exception as e:
        logger.error(f"Failed to detect network profile: {e}")
        return NetworkProfile(nat_type=NATType.UNKNOWN)
    finally:
        if node.transport:
            node.transport.close()
