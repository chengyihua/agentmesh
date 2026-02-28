from typing import Any, Dict, Optional
from fastapi import HTTPException

class ErrorCode:
    BAD_REQUEST = "BAD_REQUEST"
    UNAUTHORIZED = "UNAUTHORIZED" 
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    
    # Specific application errors
    INVALID_SIGNATURE = "INVALID_SIGNATURE"
    POW_VERIFICATION_FAILED = "POW_VERIFICATION_FAILED"
    CAPABILITY_MISMATCH = "CAPABILITY_MISMATCH"
    RELAY_CONNECTION_FAILED = "RELAY_CONNECTION_FAILED"

class AgentMeshError(HTTPException):
    def __init__(
        self, 
        status_code: int, 
        code: str, 
        message: str, 
        details: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        
        super().__init__(
            status_code=status_code,
            detail={
                "code": code,
                "message": message,
                **self.details
            }
        )

def raise_error(
    status_code: int, 
    code: str, 
    message: str, 
    details: Optional[Dict[str, Any]] = None
):
    raise AgentMeshError(status_code, code, message, details)
