import asyncio
import pytest
from datetime import datetime, timezone
from agentmesh.core.negotiation import NegotiationManager, NegotiationStatus
from agentmesh.core.pow import PoWManager

@pytest.mark.asyncio
async def test_negotiation_flow():
    manager = NegotiationManager()
    
    # 1. Create session
    session = manager.create_session(
        target_agent_id="agent-1",
        proposal="Can you process this?",
        initiator_id="agent-2"
    )
    assert session.status == NegotiationStatus.PROPOSED
    assert session.id is not None
    
    # 2. Counter
    session = manager.process_round(
        session.id,
        action="counter",
        content="I can, but it costs 5 credits."
    )
    assert session.status == NegotiationStatus.COUNTERED
    assert len(session.history) == 2
    
    # 3. Accept
    session = manager.process_round(
        session.id,
        action="accept",
        params={"price": 5}
    )
    assert session.status == NegotiationStatus.AGREED
    assert session.commitment == {"price": 5}

@pytest.mark.asyncio
async def test_pow_flow():
    manager = PoWManager(difficulty=2)  # Low difficulty for test
    
    # 1. Challenge
    nonce = manager.create_challenge()
    assert nonce in manager._challenges
    
    # 2. Solve (brute force for test)
    import hashlib
    solution = None
    for i in range(100000):
        s = str(i)
        if hashlib.sha256(f"{nonce}{s}".encode()).hexdigest().startswith("00"):
            solution = s
            break
            
    assert solution is not None
    
    # 3. Verify
    assert manager.verify_solution(nonce, solution) is True
    
    # 4. Replay attack (should fail)
    assert manager.verify_solution(nonce, solution) is False
