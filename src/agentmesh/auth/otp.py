"""OTP Manager for handling phone verification."""

import random
import logging
import asyncio
from typing import Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class OTPManager:
    def __init__(self):
        self._codes: Dict[str, Dict] = {}  # phone -> {code, expires_at}
        self._lock = asyncio.Lock()
        
    async def generate_otp(self, phone_number: str) -> str:
        """Generate a 6-digit OTP and store it."""
        code = f"{random.randint(0, 999999):06d}"
        expires_at = datetime.now() + timedelta(minutes=5)
        
        async with self._lock:
            self._codes[phone_number] = {
                "code": code,
                "expires_at": expires_at
            }
            
        # In a real app, send SMS here.
        # For now, we log it for simulation/dev.
        logger.info(f"OTP generated for {phone_number}: {code}")
        return code

    async def verify_otp(self, phone_number: str, code: str) -> bool:
        """Verify the OTP code."""
        async with self._lock:
            data = self._codes.get(phone_number)
            if not data:
                return False
                
            if datetime.now() > data["expires_at"]:
                del self._codes[phone_number]
                return False
                
            if data["code"] == code:
                del self._codes[phone_number]
                return True
                
            return False
