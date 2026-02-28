"""Token issuance and verification helpers."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt


class TokenManager:
    """Simple JWT access token + opaque refresh token manager."""

    def __init__(
        self,
        signing_key: str,
        expected_secret: str,
        algorithm: str = "HS256",
        access_token_ttl_seconds: int = 3600,
        refresh_token_ttl_seconds: int = 86400,
    ):
        self.signing_key = signing_key
        self.expected_secret = expected_secret
        self.algorithm = algorithm
        self.access_token_ttl_seconds = access_token_ttl_seconds
        self.refresh_token_ttl_seconds = refresh_token_ttl_seconds
        self._refresh_tokens: Dict[str, Dict[str, Any]] = {}

    def _utcnow(self) -> datetime:
        return datetime.now(timezone.utc)

    def _create_access_token(self, agent_id: str) -> str:
        now = self._utcnow()
        payload = {
            "sub": agent_id,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=self.access_token_ttl_seconds)).timestamp()),
            "scope": "agent",
        }
        return jwt.encode(payload, self.signing_key, algorithm=self.algorithm)

    def issue_tokens(self, agent_id: str, secret: str) -> Dict[str, Any]:
        if secret != self.expected_secret:
            raise ValueError("Invalid agent secret")

        access_token = self._create_access_token(agent_id)
        refresh_token = secrets.token_urlsafe(32)
        expires_at = self._utcnow() + timedelta(seconds=self.refresh_token_ttl_seconds)

        self._refresh_tokens[refresh_token] = {
            "agent_id": agent_id,
            "expires_at": expires_at,
        }

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.access_token_ttl_seconds,
        }

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        data = self._refresh_tokens.get(refresh_token)
        if not data:
            raise ValueError("Invalid refresh token")

        if data["expires_at"] < self._utcnow():
            del self._refresh_tokens[refresh_token]
            raise ValueError("Refresh token expired")

        access_token = self._create_access_token(data["agent_id"])
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": self.access_token_ttl_seconds,
        }

    def verify_token(self, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, self.signing_key, algorithms=[self.algorithm])
            expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
            return {
                "valid": True,
                "agent_id": payload.get("sub"),
                "expires_at": expires_at.isoformat(),
            }
        except JWTError:
            return {
                "valid": False,
                "agent_id": None,
                "expires_at": None,
            }

    def purge_expired_refresh_tokens(self) -> int:
        now = self._utcnow()
        before = len(self._refresh_tokens)
        expired = [token for token, data in self._refresh_tokens.items() if data["expires_at"] < now]
        for token in expired:
            del self._refresh_tokens[token]
        return before - len(self._refresh_tokens)
