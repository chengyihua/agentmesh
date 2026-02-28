"""Security helpers for signatures, permissions, and HMAC."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import hmac
import json
import logging
from base64 import b64decode, b64encode
from typing import Any, Dict, List, Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, padding, rsa

from .agent_card import AgentCard, PermissionLevel

logger = logging.getLogger(__name__)


class SecurityManager:
    """Security manager for AgentMesh."""

    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or self._generate_secret_key()
        self.signature_algorithm = "ed25519"
        self.permission_cache: Dict[str, Dict[str, Any]] = {}

    def derive_agent_id(self, public_key: str) -> str:
        """Derive Agent ID from public key using SHA256 and Hex encoding (Legacy)."""
        # Clean the key
        key_bytes = public_key.encode('utf-8')
        digest = hashlib.sha256(key_bytes).digest()
        # Take first 20 bytes
        truncated = digest[:20]
        # Encode to hex to ensure it's safe for URLs and IDs
        return truncated.hex()

    def derive_did(self, public_key: str) -> str:
        """Derive DID from public key (Standard)."""
        # SHA256 hash of the public key
        key_bytes = public_key.encode('utf-8')
        digest = hashlib.sha256(key_bytes).hexdigest()
        return f"did:agent:{digest}"

    def validate_agent_id(self, agent_id: str, public_key: str) -> bool:
        """Validate if the agent_id matches the public_key."""
        if not public_key:
            return False
            
        # Support DID format
        if agent_id.startswith("did:agent:"):
            return agent_id == self.derive_did(public_key)
            
        # Support Legacy format
        expected_id = self.derive_agent_id(public_key)
        return agent_id == expected_id

    def hash_body(self, payload: Any) -> str:
        """SHA256 hash of the request body string."""
        if payload is None:
            payload = ""
        if not isinstance(payload, str):
            # Sort keys to ensure deterministic JSON
            payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def create_handshake_token(self, method: str, path: str, timestamp: str, body_hash: str, private_key: str) -> str:
        """Create a signature for the request (handshake token)."""
        # Canonical string: method|path|timestamp|body_hash
        canonical_str = f"{method.upper()}|{path}|{timestamp}|{body_hash}"
        
        try:
            private_bytes = b64decode(private_key)
            if len(private_bytes) == 32:
                private_obj = ed25519.Ed25519PrivateKey.from_private_bytes(private_bytes)
                signature = private_obj.sign(canonical_str.encode("utf-8"))
                return b64encode(signature).decode("utf-8")
            
            # Try RSA
            if b"BEGIN" in private_bytes and b"PRIVATE KEY" in private_bytes:
                private_obj = serialization.load_pem_private_key(private_bytes, password=None)
                signature = private_obj.sign(
                    canonical_str.encode("utf-8"),
                    padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                    hashes.SHA256(),
                )
                return b64encode(signature).decode("utf-8")

            raise ValueError("Unknown key format")
        except Exception as e:
            logger.error(f"Failed to sign request: {e}")
            raise

    def verify_handshake_token(self, method: str, path: str, timestamp: str, body_hash: str, signature: str, public_key: str) -> bool:
        """Verify the request signature."""
        canonical_str = f"{method.upper()}|{path}|{timestamp}|{body_hash}"
        
        try:
            # Check timestamp freshness (e.g. 60s window)
            # Timestamp format: ISO 8601 (YYYY-MM-DDTHH:MM:SS.mmmmmm)
            ts_str = timestamp.replace('Z', '+00:00')
            try:
                req_time = datetime.fromisoformat(ts_str)
            except ValueError:
                # Fallback for formats without offset (assume UTC)
                req_time = datetime.fromisoformat(ts_str).replace(tzinfo=timezone.utc)

            if req_time.tzinfo is None:
                req_time = req_time.replace(tzinfo=timezone.utc)
                
            now = datetime.now(timezone.utc)
            diff = abs((now - req_time).total_seconds())
            if diff > 60:
                logger.warning(f"Request timestamp expired: {diff}s diff")
                return False

            public_bytes = b64decode(public_key)
            sig_bytes = b64decode(signature)
            data_bytes = canonical_str.encode("utf-8")

            # Try Ed25519 first (32 bytes)
            if len(public_bytes) == 32:
                public_key_obj = ed25519.Ed25519PublicKey.from_public_bytes(public_bytes)
                public_key_obj.verify(sig_bytes, data_bytes)
                return True
            
            # Try RSA
            if b"BEGIN" in public_bytes or b"ssh-rsa" in public_bytes or len(public_bytes) > 32:
                try:
                    pub = serialization.load_pem_public_key(public_bytes)
                    pub.verify(
                        sig_bytes,
                        data_bytes,
                        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                        hashes.SHA256(),
                    )
                    return True
                except Exception:
                    pass

            return False
        except InvalidSignature:
            logger.warning("Invalid signature for request")
            return False
        except Exception as e:
            logger.error(f"Verification error: {e}")
            return False

    def get_public_key_from_private(self, private_key: str) -> str:
        """Derive public key from private key string (base64)."""
        try:
            private_bytes = b64decode(private_key)
            # Try Ed25519 (32 bytes raw)
            if len(private_bytes) == 32:
                private_obj = ed25519.Ed25519PrivateKey.from_private_bytes(private_bytes)
                public_bytes = private_obj.public_key().public_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PublicFormat.Raw
                )
                return b64encode(public_bytes).decode("utf-8")
            
            # Try RSA (PEM)
            if b"BEGIN" in private_bytes and b"PRIVATE KEY" in private_bytes:
                private_obj = serialization.load_pem_private_key(private_bytes, password=None)
                public_pem = private_obj.public_key().public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
                return b64encode(public_pem).decode("utf-8")

            raise ValueError("Unknown key format")
        except Exception as e:
            raise ValueError(f"Invalid private key: {e}")

    async def verify_signature(self, agent_card: AgentCard) -> bool:
        signature = agent_card.manifest_signature or agent_card.signature
        
        if not signature or not agent_card.public_key:
            logger.warning("Agent %s has no signature/public key", agent_card.id)
            return False

        try:
            signature_data = self._prepare_signature_data(agent_card)
            
            if signature.startswith("ed25519:"):
                return await self._verify_ed25519_signature(signature[8:], signature_data, agent_card.public_key)
            if signature.startswith("rsa:"):
                return await self._verify_rsa_signature(signature[4:], signature_data, agent_card.public_key)

            logger.error("Unsupported signature algorithm for %s", agent_card.id)
            return False
        except Exception as exc:
            logger.error("Signature verification failed for %s: %s", agent_card.id, exc)
            return False

    async def sign_agent_card(self, agent_card: AgentCard, private_key: str) -> str:
        signature_data = self._prepare_signature_data(agent_card)
        if self.signature_algorithm == "ed25519":
            signature = await self._generate_ed25519_signature(signature_data, private_key)
            return f"ed25519:{signature}"
        if self.signature_algorithm == "rsa":
            signature = await self._generate_rsa_signature(signature_data, private_key)
            return f"rsa:{signature}"
        raise ValueError(f"Unsupported signature algorithm: {self.signature_algorithm}")

    async def check_permission(self, agent_card: AgentCard, resource: str, required_level: PermissionLevel) -> bool:
        for permission in agent_card.permissions:
            if self._resource_matches(permission.resource, resource):
                if self._permission_level_sufficient(permission.level, required_level):
                    return True
        return False

    async def validate_agent_card(self, agent_card: AgentCard) -> List[str]:
        errors: List[str] = []

        if not agent_card.id:
            errors.append("Agent ID is required")
        if not agent_card.name:
            errors.append("Agent name is required")
        if not agent_card.skills:
            errors.append("At least one skill is required")
        if not agent_card.endpoint:
            errors.append("Endpoint is required")

        names = [skill.name for skill in agent_card.skills]
        if len(names) != len(set(names)):
            errors.append("Skill names must be unique")

        for permission in agent_card.permissions:
            if not permission.resource:
                errors.append("Permission resource is required")
            if permission.level not in list(PermissionLevel):
                errors.append(f"Invalid permission level: {permission.level}")

        if agent_card.rate_limit and not self._validate_rate_limit_format(agent_card.rate_limit):
            errors.append(f"Invalid rate limit format: {agent_card.rate_limit}")

        if agent_card.max_execution_time is not None and agent_card.max_execution_time <= 0:
            errors.append("max_execution_time must be > 0")

        return errors

    def generate_key_pair(self, algorithm: str = "ed25519") -> Dict[str, str]:
        if algorithm == "ed25519":
            return self._generate_ed25519_key_pair()
        if algorithm == "rsa":
            return self._generate_rsa_key_pair()
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    # Backward-compatible helper used in demos
    def generate_keypair(self, algorithm: str = "ed25519") -> Any:
        keys = self.generate_key_pair(algorithm)
        return keys["private_key"], keys["public_key"]

    # Backward-compatible helper used in demos/scripts
    def sign_data(self, data: str, private_key: str) -> str:
        payload = data.encode("utf-8")
        try:
            private_bytes = b64decode(private_key)
            
            # Try Ed25519 (32 bytes raw)
            if len(private_bytes) == 32:
                private_obj = ed25519.Ed25519PrivateKey.from_private_bytes(private_bytes)
                signature = private_obj.sign(payload)
                return f"ed25519:{b64encode(signature).decode('utf-8')}"
            
            # Try RSA (PEM)
            if b"BEGIN" in private_bytes and b"PRIVATE KEY" in private_bytes:
                private_obj = serialization.load_pem_private_key(private_bytes, password=None)
                signature = private_obj.sign(
                    payload,
                    padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                    hashes.SHA256(),
                )
                return f"rsa:{b64encode(signature).decode('utf-8')}"
            
            # Fallback to configured algorithm if detection fails (or for legacy reasons)
            if self.signature_algorithm == "ed25519":
                # Likely to fail if key is not 32 bytes, but try anyway
                private_obj = ed25519.Ed25519PrivateKey.from_private_bytes(private_bytes)
                signature = private_obj.sign(payload)
                return f"ed25519:{b64encode(signature).decode('utf-8')}"
            
            raise ValueError("Unknown key format")
            
        except Exception as e:
            logger.error(f"Failed to sign data: {e}")
            raise

    def verify_data_signature(self, data: str, signature: str, public_key: str) -> bool:
        payload = data.encode("utf-8")
        try:
            if signature.startswith("ed25519:"):
                sig = b64decode(signature[8:])
                pub = ed25519.Ed25519PublicKey.from_public_bytes(b64decode(public_key))
                pub.verify(sig, payload)
                return True

            if signature.startswith("rsa:"):
                sig = b64decode(signature[4:])
                pub = serialization.load_pem_public_key(b64decode(public_key))
                pub.verify(
                    sig,
                    payload,
                    padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                    hashes.SHA256(),
                )
                return True

            return False
        except Exception:
            return False

    def _prepare_signature_data(self, agent_card: AgentCard) -> bytes:
        signature_dict = agent_card.model_dump(
            mode="json",
            exclude={
                "signature", 
                "public_key", 
                "manifest_signature",
                "created_at", 
                "updated_at",
                "trust_score",
                "health_status",
                "last_health_check",
                "last_heartbeat",
                "species_id",
                "claim_code"
            },
            exclude_none=True,
        )
        signature_json = json.dumps(signature_dict, sort_keys=True, separators=(",", ":"))
        return signature_json.encode("utf-8")

    async def _verify_ed25519_signature(self, signature: str, data: bytes, public_key_str: str) -> bool:
        try:
            signature_bytes = b64decode(signature)
            public_key_bytes = b64decode(public_key_str)
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
            public_key.verify(signature_bytes, data)
            return True
        except (InvalidSignature, ValueError):
            return False

    async def _verify_rsa_signature(self, signature: str, data: bytes, public_key_str: str) -> bool:
        try:
            signature_bytes = b64decode(signature)
            public_key_bytes = b64decode(public_key_str)
            public_key = serialization.load_pem_public_key(public_key_bytes)
            public_key.verify(
                signature_bytes,
                data,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256(),
            )
            return True
        except (InvalidSignature, ValueError):
            return False

    async def _generate_ed25519_signature(self, data: bytes, private_key: str) -> str:
        private_key_bytes = b64decode(private_key)
        private_key_obj = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)
        signature_bytes = private_key_obj.sign(data)
        return b64encode(signature_bytes).decode("utf-8")

    async def _generate_rsa_signature(self, data: bytes, private_key: str) -> str:
        private_key_bytes = b64decode(private_key)
        private_key_obj = serialization.load_pem_private_key(private_key_bytes, password=None)
        signature_bytes = private_key_obj.sign(
            data,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256(),
        )
        return b64encode(signature_bytes).decode("utf-8")

    def _generate_ed25519_key_pair(self) -> Dict[str, str]:
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )

        return {
            "private_key": b64encode(private_bytes).decode("utf-8"),
            "public_key": b64encode(public_bytes).decode("utf-8"),
            "algorithm": "ed25519",
        }

    def _generate_rsa_key_pair(self) -> Dict[str, str]:
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        return {
            "private_key": b64encode(private_pem).decode("utf-8"),
            "public_key": b64encode(public_pem).decode("utf-8"),
            "algorithm": "rsa",
        }

    def _resource_matches(self, permission_resource: str, requested_resource: str) -> bool:
        return permission_resource == requested_resource

    def _permission_level_sufficient(self, agent_level: PermissionLevel, required_level: PermissionLevel) -> bool:
        level_order = {
            PermissionLevel.READ: 1,
            PermissionLevel.WRITE: 2,
            PermissionLevel.EXECUTE: 3,
            PermissionLevel.ADMIN: 4,
        }
        return level_order.get(agent_level, 0) >= level_order.get(required_level, 0)

    def _validate_rate_limit_format(self, rate_limit: str) -> bool:
        try:
            count_str, unit = rate_limit.split("/")
            count = int(count_str)
            if count <= 0:
                return False
            return unit.lower() in {"second", "minute", "hour", "day", "week", "month"}
        except Exception:
            return False

    def _generate_secret_key(self) -> str:
        import secrets

        return secrets.token_hex(32)

    def generate_hmac_signature(self, data: str) -> str:
        return hmac.new(self.secret_key.encode("utf-8"), data.encode("utf-8"), hashlib.sha256).hexdigest()

    def verify_hmac_signature(self, data: str, signature: str) -> bool:
        expected_signature = self.generate_hmac_signature(data)
        return hmac.compare_digest(expected_signature, signature)
