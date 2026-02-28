"""API response helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def success_response(data: Any, message: str = "Operation successful") -> Dict[str, Any]:
    return {
        "success": True,
        "data": data,
        "message": message,
        "timestamp": utc_now_iso(),
    }


def error_response(
    code: str,
    message: str,
    details: Optional[Any] = None,
) -> Dict[str, Any]:
    payload = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details,
        },
        "timestamp": utc_now_iso(),
    }
    return payload
