# AgentMesh Security Guide

Comprehensive security guidelines for deploying and using AgentMesh in production environments.

## 🛡️ Security Overview

AgentMesh is designed with security as a first-class concern. This guide covers security best practices, threat models, and mitigation strategies.

## 🔐 Threat Model

### Potential Threats

1. **Unauthorized Access**
   - Unauthenticated agents registering in the network
   - Malicious agents impersonating legitimate ones
   - API key/token theft

2. **Data Breaches**
   - Sensitive agent information exposure
   - Skill details and capabilities leakage
   - Endpoint URLs revealing internal infrastructure

3. **Denial of Service**
   - Resource exhaustion attacks
   - Rate limit bypass
   - Malicious heartbeat flooding

4. **Man-in-the-Middle Attacks**
   - Interception of agent communications
   - Tampering with registration/discovery data
   - SSL/TLS vulnerabilities

5. **Privilege Escalation**
   - Agents gaining unauthorized access to other agents
   - Bypassing skill-based access controls
   - Exploiting protocol vulnerabilities

## 🔒 Authentication & Authorization

### 1. API Key Authentication

**Best Practices:**
```python
# Generate secure API keys
import secrets
import hashlib

def generate_api_key():
    # Generate cryptographically secure key
    key = secrets.token_urlsafe(32)
    
    # Store hash, not the key itself
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    
    return key, key_hash

# Usage
api_key, api_key_hash = generate_api_key()
print(f"API Key: {api_key}")  # Give this to the user
print(f"Key Hash: {api_key_hash}")  # Store this in your database
```

**Implementation:**
```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from agentmesh.security import validate_api_key

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_current_agent(
    api_key: str = Security(api_key_header)
) -> Agent:
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required"
        )
    
    agent = await validate_api_key(api_key)
    if not agent:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    return agent

@app.post("/agents/register")
async def register_agent(
    agent_card: AgentCard,
    current_agent: Agent = Depends(get_current_agent)
):
    # Only authenticated agents can register
    if not current_agent.can_register_agents:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions"
        )
    
    # Process registration
    return await registry.register_agent(agent_card)
```

### 2. JWT Token Authentication

**Implementation:**
```python
import jwt
from datetime import datetime, timedelta
from typing import Optional

class JWTManager:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def create_token(
        self,
        agent_id: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        to_encode = {
            "sub": agent_id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + (expires_delta or timedelta(hours=1))
        }
        
        return jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.algorithm
        )
    
    def verify_token(self, token: str) -> Optional[str]:
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload.get("sub")
        except jwt.PyJWTError:
            return None

# Usage
jwt_manager = JWTManager(secret_key="your-secret-key")
token = jwt_manager.create_token(agent_id="weather-bot-001")
agent_id = jwt_manager.verify_token(token)
```

### 3. OAuth 2.0 Integration

**Example with GitHub OAuth:**
```python
from authlib.integrations.starlette_client import OAuth

oauth = OAuth()
oauth.register(
    name='github',
    client_id='your-client-id',
    client_secret='your-client-secret',
    authorize_url='https://github.com/login/oauth/authorize',
    authorize_params=None,
    access_token_url='https://github.com/login/oauth/access_token',
    access_token_params=None,
    refresh_token_url=None,
    redirect_uri='http://localhost:8000/auth/callback',
    client_kwargs={'scope': 'read:user'},
)

@app.get("/auth/login")
async def login(request: Request):
    redirect_uri = request.url_for('auth_callback')
    return await oauth.github.authorize_redirect(request, redirect_uri)

@app.get("/auth/callback")
async def auth_callback(request: Request):
    token = await oauth.github.authorize_access_token(request)
    user = await oauth.github.get('user', token=token)
    
    # Create or update agent based on GitHub user
    agent_id = f"github-{user['id']}"
    # ... create agent card
```

## 🛡️ Data Protection

### 1. Encryption at Rest

**Database Encryption:**
```python
from cryptography.fernet import Fernet
import json

class EncryptedStorage:
    def __init__(self, storage_backend, encryption_key):
        self.storage = storage_backend
        self.cipher = Fernet(encryption_key)
    
    async def save_agent(self, agent: AgentCard):
        # Serialize and encrypt
        agent_data = agent.json()
        encrypted_data = self.cipher.encrypt(agent_data.encode())
        
        # Store encrypted data
        await self.storage.save(agent.id, encrypted_data)
    
    async def get_agent(self, agent_id: str) -> Optional[AgentCard]:
        # Retrieve encrypted data
        encrypted_data = await self.storage.get(agent_id)
        if not encrypted_data:
            return None
        
        # Decrypt and deserialize
        agent_data = self.cipher.decrypt(encrypted_data).decode()
        return AgentCard.parse_raw(agent_data)
```

### 2. Field-Level Encryption

**Sensitive Field Protection:**
```python
from pydantic import BaseModel, Field, SecretStr
from typing import Optional

class SecureAgentCard(BaseModel):
    id: str
    name: str
    description: str
    
    # Encrypted fields
    api_key: Optional[SecretStr] = Field(None, description="API key for external services")
    webhook_secret: Optional[SecretStr] = Field(None, description="Webhook verification secret")
    database_url: Optional[SecretStr] = Field(None, description="Database connection string")
    
    # Regular fields
    endpoint: str
    skills: List[Skill]
    
    class Config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None
        }
```

### 3. Data Masking

**Logging and Debugging:**
```python
import re

def mask_sensitive_data(data: dict) -> dict:
    """Mask sensitive information in logs."""
    masked = data.copy()
    
    sensitive_fields = [
        'api_key', 'token', 'secret', 'password',
        'private_key', 'database_url', 'redis_url'
    ]
    
    for field in sensitive_fields:
        if field in masked:
            value = str(masked[field])
            if len(value) > 8:
                masked[field] = value[:4] + '***' + value[-4:]
            else:
                masked[field] = '***'
    
    return masked

# Usage in logging
logger.info("Agent registered", extra={
    "agent_data": mask_sensitive_data(agent.dict())
})
```

## 🚫 Input Validation & Sanitization

### 1. Schema Validation

```python
from pydantic import BaseModel, validator, HttpUrl, constr
import re

class SecureAgentCard(BaseModel):
    id: constr(regex=r'^[a-zA-Z0-9_-]{1,100}$')
    name: constr(min_length=1, max_length=100)
    endpoint: HttpUrl
    
    @validator('endpoint')
    def validate_endpoint(cls, v):
        # Reject internal endpoints
        if re.match(r'^(http://|https://)(localhost|127\.|192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.)', str(v)):
            raise ValueError('Internal endpoints are not allowed')
        
        # Require HTTPS in production
        if not str(v).startswith('https://'):
            raise ValueError('HTTPS is required for production endpoints')
        
        return v
    
    @validator('skills')
    def validate_skills(cls, v):
        if len(v) > 20:
            raise ValueError('Maximum 20 skills allowed')
        
        # Check for dangerous skill names
        dangerous_skills = ['exec', 'system', 'eval', 'shell']
        for skill in v:
            if skill.name.lower() in dangerous_skills:
                raise ValueError(f'Dangerous skill name: {skill.name}')
        
        return v
```

### 2. SQL Injection Prevention

```python
# Using parameterized queries with SQLAlchemy
from sqlalchemy import text

async def get_agent_safe(agent_id: str):
    # SAFE: Parameterized query
    query = text("SELECT * FROM agents WHERE id = :agent_id")
    result = await database.execute(query, {"agent_id": agent_id})
    return result.fetchone()

# NEVER do this (vulnerable to SQL injection)
async def get_agent_unsafe(agent_id: str):
    # UNSAFE: String concatenation
    query = f"SELECT * FROM agents WHERE id = '{agent_id}'"
    result = await database.execute(query)
    return result.fetchone()
```

### 3. XSS Prevention

```python
from markupsafe import escape

def render_agent_details(agent: AgentCard) -> str:
    # SAFE: Escape all user input
    html = f"""
    <div class="agent-card">
        <h2>{escape(agent.name)}</h2>
        <p>{escape(agent.description)}</p>
        <ul>
    """
    
    for skill in agent.skills:
        html += f"<li>{escape(skill.name)}: {escape(skill.description)}</li>"
    
    html += "</ul></div>"
    return html
```

## 🛡️ Network Security

### 1. TLS/SSL Configuration

**Production TLS Setup:**
```python
import ssl
from agentmesh.server import AgentMeshServer

# Generate certificates (example with mkcert)
# mkcert -install
# mkcert localhost 127.0.0.1 ::1

ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain(
    certfile="cert.pem",
    keyfile="key.pem"
)

server = AgentMeshServer(
    ssl_context=ssl_context,
    port=443
)
```

### 2. CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://agentmesh.example.com",
        "https://dashboard.agentmesh.example.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-API-Key",
        "X-Requested-With"
    ],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
    max_age=600
)
```

### 3. Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/agents/register")
@limiter.limit("10/minute")
async def register_agent(request: Request, agent_card: AgentCard):
    # Registration logic
    pass

@app.get("/agents/discover")
@limiter.limit("60/minute")
async def discover_agents(request: Request):
    # Discovery logic
    pass
```

## 🔍 Security Monitoring

### 1. Audit Logging

```python
import logging
from datetime import datetime
from typing import Dict, Any

class AuditLogger:
    def __init__(self):
        self.logger = logging.getLogger("audit")
        handler = logging.FileHandler("audit.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_event(
        self,
        event_type: str,
        agent_id: str,
        details: Dict[str, Any],
        success: bool = True
    ):
        audit_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "agent_id": agent_id,
            "details": details,
            "success": success,
            "ip_address": self._get_client_ip(),
            "user_agent": self._get_user_agent()
        }
        
        self.logger.info(json.dumps(audit_record))
    
    def _get_client_ip(self) -> str:
        # Implementation depends on your framework
        pass
    
    def _get_user_agent(self) -> str:
        # Implementation depends on your framework
        pass

# Usage
audit_logger = AuditLogger()

@app.post("/agents/register")
async def register_agent(agent_card: AgentCard):
    try:
        result = await registry.register_agent(agent_card)
        audit_logger.log_event(
            event_type="agent_registered",
            agent_id=agent_card.id,
            details={"skills": [s.name for s in agent_card.skills]},
            success=True
        )
        return result
    except Exception as e:
        audit_logger.log_event(
            event_type="agent_registration_failed",
            agent_id=agent_card.id,
            details={"error": str(e)},
            success=False
        )
        raise
```

### 2. Intrusion Detection

```python
from datetime import datetime, timedelta
import asyncio

class IntrusionDetectionSystem:
    def __init__(self):
        self.failed_attempts = {}
        self.lock = asyncio.Lock()
    
    async def check_suspicious_activity(
        self,
        agent_id: str,
        event_type: str
    ) -> bool:
        async with self.lock:
            key = f"{agent_id}:{event_type}"
            now = datetime.now()
            
            # Clean old entries
            self._clean_old_entries(now)
            
            # Check rate
            if key not in self.failed_attempts:
                self.failed_attempts[key] = []
            
            self.failed_attempts[key].append(now)
            
            # Check if suspicious (more than 10 attempts in 1 minute)
            recent_attempts = [
                t for t in self.failed_attempts[key]
                if now - t < timedelta(minutes=1)
            ]
            
            if len(recent_attempts) > 10:
                # Alert and block
                await self._alert_admin(agent_id, event_type, len(recent_attempts))
                return False
            
            return True
    
    def _clean_old_entries(self, now: datetime):
        cutoff = now - timedelta(minutes=5)
        for key in list(self.failed_attempts.keys()):
            self.failed_attempts[key] = [
                t for t in self.failed_attempts[key]
                if t > cutoff
            ]
            if not self.failed_attempts[key]:
                del self.failed_attempts[key]
    
    async def _alert_admin(self, agent_id: str, event_type: str, count: int):
        # Send alert (email, Slack, etc.)
        print(f"ALERT: Suspicious activity from {agent_id}")
        print(f"Event: {event_type}, Attempts: {count}")
```

### 3. Security Headers

```python
from fastapi import FastAPI
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI()

# Redirect HTTP to HTTPS
app.add_middleware(HTTPSRedirectMiddleware)

# Validate host headers
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["agentmesh.example.com", "*.agentmesh.example.com"]
)

# Add security headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    
    # HSTS (only in production with HTTPS)
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response
```

## 🚨 Incident Response

### 1. Incident Response Plan

```python
class IncidentResponse:
    def __init__(self):
        self.incidents = []
    
    async def handle_security_incident(
        self,
        incident_type: str,
        severity: str,
        details: Dict[str, Any]
    ):
        incident = {
            "type": incident_type,
            "severity": severity,
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "open"
        }
        
        self.incidents.append(incident)
        
        # Log incident
        await self._log_incident(incident)
        
        # Notify based on severity
        if severity in ["critical", "high"]:
            await self._notify_security_team(incident)
        
        if severity == "critical":
            await self._escalate_to_management(incident)
        
        # Take immediate action
        await self._take_immediate_action(incident)
    
    async def _take_immediate_action(self, incident: dict):
        actions = {
            "unauthorized_access": self._block_ip,
            "data_breach": self._isolate_system,
            "dos_attack": self._enable_rate_limiting,
            "malware_detection": self._quarantine_agent
        }
        
        if incident["type"] in actions:
            await actions[incident["type"]](incident)
    
    async def _block_ip(self, incident: dict):
        ip = incident["details"].get("ip_address")
        if ip:
            # Add to firewall block list
            print(f"Blocking IP: {ip}")
    
    async def _quarantine_agent(self, incident: dict):
        agent_id = incident["details"].get("agent_id")
        if agent_id:
            # Mark agent as quarantined
            await registry.update_agent_status(agent_id, "quarantined")
```

### 2. Forensic Analysis

```python
import hashlib
import json
from datetime import datetime, timedelta

class ForensicAnalyzer:
    def __init__(self, log_dir: str = "/var/log/agentmesh"):
        self.log_dir = log_dir
    
    async def analyze_incident(
        self,
        incident_id: str,
        time_range: tuple
    ) -> Dict[str, Any]:
        start_time, end_time = time_range
        
        # Collect logs
        logs = await self._collect_logs(start_time, end_time)
        
        # Analyze patterns
        analysis = {
            "incident_id": incident_id,
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "total_logs": len(logs),
            "suspicious_activities": [],
            "affected_agents": set(),
            "timeline": []
        }
        
        # Analyze each log entry
        for log in logs:
            if self._is_suspicious(log):
                analysis["suspicious_activities"].append(log)
                if "agent_id" in log:
                    analysis["affected_agents"].add(log["agent_id"])
            
            analysis["timeline"].append({
                "timestamp": log.get("timestamp"),
                "event": log.get("event_type"),
                "agent": log.get("agent_id")
            })
        
        analysis["affected_agents"] = list(analysis["affected_agents"])
        
        return analysis
    
    def _is_suspicious(self, log: dict) -> bool:
        suspicious_patterns = [
            "failed_login",
            "unauthorized",
            "malformed",
            "injection",
            "brute_force"
        ]
        
        event_type = log.get("event_type", "").lower()
        message = log.get("message", "").lower()
        
        for pattern in suspicious_patterns:
            if pattern in event_type or pattern in message:
                return True
        
        return False
```

## 📚 Security Checklist

### Before Deployment
- [ ] Enable HTTPS with valid certificates
- [ ] Configure proper CORS settings
- [ ] Set up rate limiting
- [ ] Implement authentication and authorization
- [ ] Encrypt sensitive data at rest
- [ ] Set up audit logging
- [ ] Configure security headers
- [ ] Create backup and recovery plan

### Regular Maintenance
- [ ] Rotate API keys and tokens regularly
- [ ] Update dependencies and security patches
- [ ] Review and update firewall rules
- [ ] Monitor security logs
- [ ] Conduct security audits
- [ ] Test incident response procedures
- [ ] Update security policies

### Incident Response
- [ ] Document incident response plan
- [ ] Train team on security procedures
- [ ] Establish communication channels
- [ ] Prepare forensic analysis tools
- [ ] Set up alerting system
- [ ] Create recovery procedures

## 🔗 Additional Resources

### Security Tools
- **Static Analysis**: Bandit, Safety, Trivy
- **Dynamic Analysis**: OWASP ZAP, Burp Suite
- **Dependency Scanning**: Snyk, Dependabot
- **Secret Detection**: GitGuardian, TruffleHog

### Security Standards
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [ISO/IEC 27001](https://www.iso.org/isoiec-27001-information-security.html)

### Learning Resources
- [OWASP Cheat Sheets](https://cheatsheetseries.owasp.org/)
- [Security Engineering Book](https://www.cl.cam.ac.uk/~rja14/book.html)
- [Cloud Security Alliance](https://cloudsecurityalliance.org/)

## 🆘 Getting Security Help

If you discover a security vulnerability:

1. **DO NOT** disclose publicly
2. **DO** report to security@agentmesh.io
3. **DO** include detailed reproduction steps
4. **DO** allow time for investigation and fix

For security questions or concerns:
- Email: security@agentmesh.io
- Security Advisory: https://github.com/agentmesh/agentmesh/security/advisories
- PGP Key: Available on security page

Remember: Security is an ongoing process, not a one-time setup. Regular reviews and updates are essential for maintaining a secure AgentMesh deployment.