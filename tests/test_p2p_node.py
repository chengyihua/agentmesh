import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from agentmesh.p2p.node import P2PNode

@pytest.mark.asyncio
async def test_p2p_node_loopback():
    received = asyncio.Future()

    async def on_message(payload, addr):
        if payload == "hello":
            received.set_result(True)

    with patch("agentmesh.p2p.node.P2PNode.discover_public_endpoint", new_callable=AsyncMock) as mock_discover:
        mock_discover.return_value = ("1.2.3.4", 1234)
        
        node = P2PNode(port=0, on_message=on_message)
        await node.start()
        
        port = node.transport.get_extra_info('sockname')[1]
        assert port > 0
        
        # Send message to self
        node.send_message(("127.0.0.1", port), {"type": "data", "payload": "hello"})
        
        try:
            await asyncio.wait_for(received, timeout=2.0)
        except asyncio.TimeoutError:
            pytest.fail("Did not receive loopback message")
        finally:
            node.close()

@pytest.mark.asyncio
async def test_p2p_hole_punch_simulation():
    # Simulate two nodes trying to punch each other
    # In loopback, NAT is not involved, but we can verify the handshake logic
    
    with patch("agentmesh.p2p.node.P2PNode.discover_public_endpoint", new_callable=AsyncMock) as mock_discover:
        mock_discover.return_value = ("1.2.3.4", 1234)
    
        node_a = P2PNode(port=0)
        node_b = P2PNode(port=0)
        
        await node_a.start()
        await node_b.start()
        
        port_b = node_b.transport.get_extra_info('sockname')[1]
        
        # Monkey patch datagram_received on A to detect ACK
        ack_received = asyncio.Future()
        original_datagram_received_a = node_a.datagram_received
        
        def spied_datagram_received_a(data, addr):
            original_datagram_received_a(data, addr)
            import json
            try:
                msg = json.loads(data.decode())
                if msg.get("type") == "ack":
                    if not ack_received.done():
                        ack_received.set_result(True)
            except:
                pass
                
        node_a.datagram_received = spied_datagram_received_a
        
        # Send PUNCH from A to B
        node_a.send_message(("127.0.0.1", port_b), {"type": "punch"})
        
        try:
            await asyncio.wait_for(ack_received, timeout=2.0)
        except asyncio.TimeoutError:
            pytest.fail("Node A did not receive ACK from Node B")
        finally:
            node_a.close()
            node_b.close()

@pytest.mark.asyncio
async def test_p2p_connect_to_peer_success():
    # Test that connect_to_peer returns True when ACK is received
    with patch("agentmesh.p2p.node.P2PNode.discover_public_endpoint", new_callable=AsyncMock) as mock_discover:
        mock_discover.return_value = ("127.0.0.1", 1234)
        
        node_a = P2PNode(port=0)
        node_b = P2PNode(port=0) # Acts as peer
        
        await node_a.start()
        await node_b.start()
        
        port_b = node_b.transport.get_extra_info('sockname')[1]
        
        # When A calls connect_to_peer(B), A sends punch.
        # B receives punch, sends ACK.
        # A receives ACK, connect_to_peer returns True.
        
        connected = await node_a.connect_to_peer("127.0.0.1", port_b, timeout=2.0)
        assert connected is True
        
        node_a.close()
        node_b.close()

@pytest.mark.asyncio
async def test_p2p_connect_to_peer_timeout():
    # Test that connect_to_peer returns False when no ACK is received
    with patch("agentmesh.p2p.node.P2PNode.discover_public_endpoint", new_callable=AsyncMock) as mock_discover:
        mock_discover.return_value = ("127.0.0.1", 1234)
        
        node_a = P2PNode(port=0)
        # No node_b, so no one to reply
        
        await node_a.start()
        
        # Should timeout
        connected = await node_a.connect_to_peer("127.0.0.1", 12345, timeout=1.0)
        assert connected is False
        
        node_a.close()
