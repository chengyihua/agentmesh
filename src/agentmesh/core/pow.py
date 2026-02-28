"""Proof of Work (PoW) manager for Sybil defense."""

import hashlib
import secrets
import time
from typing import Dict, Optional, Tuple

class PoWManager:
    """Manages Proof of Work challenges and verification."""

    def __init__(self, difficulty: int = 4, ttl_seconds: int = 60):
        """
        Initialize PoW Manager.
        
        Args:
            difficulty: Number of leading zeros required in hex hash.
            ttl_seconds: Time-to-live for a challenge in seconds.
        """
        self.difficulty = difficulty
        self.ttl_seconds = ttl_seconds
        self._challenges: Dict[str, float] = {}  # nonce -> timestamp

    def create_challenge(self) -> str:
        """Generate a new challenge nonce."""
        nonce = secrets.token_hex(16)
        self._challenges[nonce] = time.time()
        self._cleanup()
        return nonce

    def verify_solution(self, nonce: str, solution: str) -> bool:
        """
        Verify a PoW solution.
        
        Args:
            nonce: The challenge nonce provided by the server.
            solution: The solution provided by the client.
            
        Returns:
            True if valid, False otherwise.
        """
        # Check if nonce exists and is not expired
        timestamp = self._challenges.get(nonce)
        if not timestamp:
            return False
            
        if time.time() - timestamp > self.ttl_seconds:
            del self._challenges[nonce]
            return False

        # Verify hash
        data = f"{nonce}{solution}".encode("utf-8")
        digest = hashlib.sha256(data).hexdigest()
        
        if digest.startswith("0" * self.difficulty):
            # Consume nonce to prevent replay
            del self._challenges[nonce]
            return True
            
        return False

    def _cleanup(self):
        """Remove expired challenges."""
        now = time.time()
        expired = [n for n, t in self._challenges.items() if now - t > self.ttl_seconds]
        for n in expired:
            del self._challenges[n]
