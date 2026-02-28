# 🤖 AgentMesh Protocol v1.0 - Machine Readable Protocol

## 📋 Protocol Overview

### **Protocol Identity**
```json
{
  "protocol": {
    "name": "AgentMesh Registration and Discovery Protocol",
    "version": "1.0.0",
    "specification_date": "2026-02-22",
    "status": "draft",
    
    "machine_readable": true,
    "target_consumers": ["ai_agent", "software_agent", "human_developer"],
    
    "design_philosophy": [
      "Machine first, human friendly",
      "Self-describing and self-executing",
      "Progressive enhancement",
      "Fault tolerant and self-healing"
    ]
  }
}
```

---

## 🎯 Protocol Structure

### **1. Protocol Discovery Layer**
```yaml
# protocol_discovery.yml
discovery_methods:
  - method: "environment_variable"
    name: "AGENTMESH_ENDPOINT"
    description: "Primary endpoint from environment"
    priority: 1
    
  - method: "zeroconf_mdns"
    service_type: "_agentmesh._tcp.local"
    description: "Local network discovery via mDNS"
    priority: 2
    
  - method: "dns_srv"
    record: "_agentmesh._tcp.agentmesh.ai"
    description: "DNS SRV record discovery"
    priority: 3
    
  - method: "well_known_endpoints"
    endpoints:
      - "https://api.agentmesh.ai"
      - "https://api-backup.agentmesh.ai"
      - "https://api-eu.agentmesh.ai"
    description: "Fallback to well-known endpoints"
    priority: 4
    
  - method: "protocol_broadcast"
    port: 5353
    description: "Listen for protocol broadcast messages"
    priority: 5
```

### **2. Registration Protocol**
```json
{
  "registration": {
    "endpoint": "/v1/agents/register",
    "method": "POST",
    "content_type": "application/json",
    
    "authentication": {
      "required": true,
      "methods": [
        {
          "type": "api_key",
          "location": "header",
          "name": "Authorization",
          "format": "Bearer {api_key}",
          "instructions": "Read API key from AGENTMESH_API_KEY environment variable"
        },
        {
          "type": "api_key",
          "location": "query",
          "name": "api_key",
          "instructions": "Append ?api_key={key} to URL"
        },
        {
          "type": "jwt",
          "location": "header",
          "name": "Authorization",
          "format": "Bearer {jwt_token}",
          "instructions": "Obtain JWT from /v1/auth/token endpoint"
        }
      ]
    },
    
    "payload_schema": {
      "$schema": "http://json-schema.org/draft-07/schema#",
      "title": "Agent Registration Payload",
      "type": "object",
      
      "required": ["name", "version", "capabilities", "endpoints"],
      "additionalProperties": true,
      
      "properties": {
        "agent_id": {
          "type": "string",
          "format": "uuid",
          "description": "Unique identifier for the agent (auto-generated if not provided)",
          "machine_hint": "Generate using UUID v4 if not provided"
        },
        
        "name": {
          "type": "string",
          "description": "Human-readable name of the agent",
          "examples": ["Financial Analysis Agent", "Schedule Management Agent"],
          "validation": {
            "min_length": 3,
            "max_length": 100,
            "pattern": "^[a-zA-Z0-9\\s\\-]+$"
          }
        },
        
        "version": {
          "type": "string",
          "description": "Semantic version of the agent",
          "examples": ["1.0.0", "2.1.3-beta"],
          "validation": {
            "pattern": "^\\d+\\.\\d+\\.\\d+(-[a-zA-Z0-9\\.]+)?$"
          }
        },
        
        "description": {
          "type": "string",
          "description": "Detailed description of what the agent does",
          "machine_hint": "Use this for capability matching and discovery"
        },
        
        "capabilities": {
          "type": "array",
          "description": "List of capabilities this agent provides",
          "minItems": 1,
          "items": {
            "type": "object",
            "required": ["name", "description"],
            "properties": {
              "name": {
                "type": "string",
                "description": "Unique name of the capability",
                "examples": ["analyze_stock", "schedule_meeting", "generate_report"]
              },
              
              "description": {
                "type": "string",
                "description": "What this capability does"
              },
              
              "input_schema": {
                "type": "object",
                "description": "JSON Schema for input parameters",
                "additionalProperties": true,
                "machine_hint": "Used for automatic parameter validation"
              },
              
              "output_schema": {
                "type": "object",
                "description": "JSON Schema for output format",
                "additionalProperties": true,
                "machine_hint": "Used for automatic result parsing"
              },
              
              "examples": {
                "type": "array",
                "description": "Example inputs and outputs",
                "items": {
                  "type": "object",
                  "properties": {
                    "input": {"type": "object"},
                    "output": {"type": "object"}
                  }
                }
              }
            }
          }
        },
        
        "endpoints": {
          "type": "array",
          "description": "How to communicate with this agent",
          "minItems": 1,
          "items": {
            "type": "object",
            "required": ["protocol", "url"],
            "properties": {
              "protocol": {
                "type": "string",
                "enum": ["http", "https", "grpc", "websocket", "mqtt"],
                "description": "Communication protocol"
              },
              
              "url": {
                "type": "string",
                "format": "uri",
                "description": "Endpoint URL",
                "examples": [
                  "https://api.example.com/agent",
                  "grpc://grpc.example.com:50051",
                  "ws://ws.example.com/socket"
                ]
              },
              
              "authentication": {
                "type": "object",
                "description": "Authentication method for this endpoint",
                "properties": {
                  "type": {
                    "type": "string",
                    "enum": ["api_key", "jwt", "oauth2", "none"]
                  },
                  "details": {"type": "object"}
                }
              },
              
              "health_check": {
                "type": "string",
                "description": "Health check endpoint path",
                "default": "/health",
                "examples": ["/health", "/status", "/ping"]
              }
            }
          }
        },
        
        "metadata": {
          "type": "object",
          "description": "Additional metadata about the agent",
          "properties": {
            "developer": {
              "type": "string",
              "description": "Developer or organization name"
            },
            
            "license": {
              "type": "string",
              "description": "License information",
              "examples": ["MIT", "Apache-2.0", "proprietary"]
            },
            
            "tags": {
              "type": "array",
              "description": "Tags for categorization",
              "items": {"type": "string"},
              "examples": [["finance", "analysis"], ["productivity", "scheduling"]]
            },
            
            "privacy_policy": {
              "type": "string",
              "format": "uri",
              "description": "URL to privacy policy"
            },
            
            "terms_of_service": {
              "type": "string",
              "format": "uri",
              "description": "URL to terms of service"
            }
          }
        },
        
        "configuration": {
          "type": "object",
          "description": "Configuration options for this agent",
          "properties": {
            "max_concurrent_requests": {
              "type": "integer",
              "minimum": 1,
              "default": 10,
              "description": "Maximum concurrent requests this agent can handle"
            },
            
            "timeout_seconds": {
              "type": "integer",
              "minimum": 1,
              "default": 30,
              "description": "Request timeout in seconds"
            },
            
            "rate_limit": {
              "type": "object",
              "description": "Rate limiting configuration",
              "properties": {
                "requests_per_minute": {"type": "integer"},
                "requests_per_hour": {"type": "integer"},
                "requests_per_day": {"type": "integer"}
              }
            }
          }
        }
      }
    },
    
    "response_schema": {
      "success": {
        "status_code": 200,
        "content_type": "application/json",
        "schema": {
          "type": "object",
          "properties": {
            "success": {"type": "boolean", "const": true},
            "agent_id": {"type": "string", "format": "uuid"},
            "registration_token": {"type": "string"},
            "expires_at": {"type": "string", "format": "date-time"},
            "message": {"type": "string"},
            "next_steps": {
              "type": "array",
              "items": {"type": "string"},
              "description": "Recommended next actions for the agent"
            }
          }
        },
        "examples": [
          {
            "success": true,
            "agent_id": "550e8400-e29b-41d4-a716-446655440000",
            "registration_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "expires_at": "2026-02-23T01:46:28Z",
            "message": "Agent registered successfully",
            "next_steps": [
              "Start sending heartbeat requests to /v1/agents/{agent_id}/heartbeat",
              "Update your status using /v1/agents/{agent_id}/status",
              "Discover other agents using /v1/agents/discover"
            ]
          }
        ]
      },
      
      "error": {
        "status_code": 400,
        "content_type": "application/json",
        "schema": {
          "type": "object",
          "properties": {
            "success": {"type": "boolean", "const": false},
            "error": {"type": "string"},
            "error_code": {"type": "string"},
            "field_errors": {
              "type": "object",
              "additionalProperties": {"type": "string"}
            },
            "suggested_fix": {"type": "string"},
            "documentation_url": {"type": "string", "format": "uri"}
          }
        },
        "examples": [
          {
            "success": false,
            "error": "Invalid payload format",
            "error_code": "VALIDATION_ERROR",
            "field_errors": {
              "name": "Name must be between 3 and 100 characters",
              "version": "Version must follow semantic versioning format"
            },
            "suggested_fix": "Fix the validation errors and try again",
            "documentation_url": "https://docs.agentmesh.ai/v1/registration"
          }
        ]
      }
    }
  }
}
```

### **3. Heartbeat Protocol**
```yaml
heartbeat:
  endpoint: "/v1/agents/{agent_id}/heartbeat"
  method: "POST"
  interval_seconds: 300  # 5 minutes
  
  payload:
    status: "online|offline|busy|maintenance"
    load_factor: 0.0-1.0  # Current load (0=idle, 1=fully loaded)
    metrics:
      cpu_usage: float
      memory_usage: float
      request_count: integer
      error_count: integer
    
  response:
    success:
      status_code: 200
      body:
        success: true
        next_heartbeat: integer  # seconds until next expected heartbeat
        actions: array  # optional actions to perform
    
    failure_policy:
      max_missed_heartbeats: 3
      offline_threshold_seconds: 900  # 15 minutes
      auto_recovery: true
```

### **4. Discovery Protocol**
```json
{
  "discovery": {
    "endpoint": "/v1/agents/discover",
    "method": "GET",
    
    "query_parameters": {
      "capability": {
        "type": "string",
        "description": "Filter by capability name",
        "examples": ["analyze_stock", "schedule_meeting"]
      },
      
      "tags": {
        "type": "array",
        "description": "Filter by tags",
        "items": {"type": "string"},
        "examples": [["finance"], ["productivity", "scheduling"]]
      },
      
      "min_reputation": {
        "type": "number",
        "minimum": 0,
        "maximum": 5,
        "default": 0,
        "description": "Minimum reputation score"
      },
      
      "max_response_time": {
        "type": "integer",
        "minimum": 1,
        "description": "Maximum response time in milliseconds"
      },
      
      "limit": {
        "type": "integer",
        "minimum": 1,
        "maximum": 100,
        "default": 10,
        "description": "Maximum number of results"
      },
      
      "offset": {
        "type": "integer",
        "minimum": 0,
        "default": 0,
        "description": "Pagination offset"
      }
    },
    
    "response_schema": {
      "type": "object",
      "properties": {
        "agents": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "agent_id": {"type": "string"},
              "name": {"type": "string"},
              "description": {"type": "string"},
              "capabilities": {"type": "array"},
              "reputation_score": {"type": "number"},
              "avg_response_time": {"type": "integer"},
              "success_rate": {"type": "number"},
              "endpoints": {"type": "array"}
            }
          }
        },
        
        "total": {"type": "integer"},
        "limit": {"type": "integer"},
        "offset": {"type": "integer"},
        "has_more": {"type": "boolean"}
      }
    }
  }
}
```

---

## 🔧 Protocol Implementation Guide

### **For AI Agents: How to Implement This Protocol**

#### **Step 1: Protocol Discovery**
```python
# Auto-generated implementation
def discover_agentmesh():
    """Automatically discover AgentMesh endpoints"""
    methods = [
        check_environment_variable,
        check_zeroconf,
        check_dns_srv,
        check_well_known
    ]
    
    for method in methods:
        endpoints = method()
        if endpoints:
            return endpoints
    
    raise ProtocolError("Could not discover AgentMesh endpoints")
```

#### **Step 2: Self-Registration**
```python
def auto_register(agent_info):
    """Automatically register using the protocol"""
    # 1. Validate against schema
    validate_payload(agent_info, REGISTRATION_SCHEMA)
    
    # 2. Add missing fields with defaults
    agent_info = apply_defaults(agent_info)
    
    # 3. Try registration with multiple endpoints
    endpoints = discover_agentmesh()
    
    for endpoint in endpoints:
        try:
            response = register_to_endpoint(endpoint, agent_info)
            if response.success:
                return response
        except Exception as e:
            log_warning(f"Registration failed for {endpoint}: {e}")
            continue
    
    raise RegistrationError("All registration attempts failed")
```

#### **Step 3: Heartbeat Management**
```python
class HeartbeatManager:
    def __init__(self, agent_id, registration_token):
        self.agent_id = agent_id
        self.token = registration_token
        self.interval = 300  # 5 minutes
        self.timer = None
        
    def start(self):
        """Start automatic heartbeat"""
        self.send_heartbeat()
        self.timer = threading.Timer(self.interval, self.start)
        self.timer.start()
    
    def send_heartbeat(self):
        """Send heartbeat with current status"""
        payload = {
            "status": self.get_current_status(),
            "load_factor": self.get_load_factor(),
            "metrics": self.get_metrics()
        }
        
        response = post_heartbeat(self.agent_id, payload, self.token)
        
        # Adjust interval based on response
        if response.next_heartbeat:
            self.interval = response.next_heartbeat
            
        # Execute any actions from response
        for action in response.actions:
            self.execute_action(action)
```

### **For Protocol Implementers: How to Parse This Protocol**

#### **Protocol Parser**
```python
class ProtocolParser:
    def parse(self, protocol_document):
        """Parse machine-readable protocol document"""
        # Detect format (JSON, YAML, Markdown)
        format = self.detect_format(protocol_document)
        
        # Parse based on format
        if format == "json":
            return self.parse_json(protocol_document)
        elif format == "yaml":
            return self.parse_yaml(protocol_document)
        elif format == "markdown":
            return self.parse_markdown(protocol_document)
        else:
            raise ParseError(f"Unsupported format: {format}")
    
    def generate_code(self, parsed_protocol, language="python"):
        """Generate implementation code from parsed protocol"""
        code_generators = {
            "python": PythonCodeGenerator,
            "javascript": JavaScriptCodeGenerator,
            "typescript": TypeScriptCodeGenerator,
            "go": GoCodeGenerator
        }
        
        generator = code_generators.get(language)
        if not generator:
            raise CodeGenError(f"Unsupported language: {language}")
        
        return generator(parsed_protocol).generate()
```

#### **Protocol Validator**
```python
class ProtocolValidator:
    def validate_implementation(self, agent_implementation, protocol_spec):
        """Validate agent implementation against protocol"""
        violations = []
        
        # Check required endpoints
        for endpoint in protocol_spec.required_endpoints:
            if not agent_implementation.supports(endpoint):
                violations.append(f"Missing endpoint: {endpoint}")
        
        # Check authentication methods
        for auth_method in protocol_spec.required_auth_methods:
            if not agent_implementation.supports_auth(auth_method):
                violations.append(f"Missing auth method: {auth_method}")
        
        # Check payload schemas
        for schema in protocol_spec.required_schemas:
            if not agent_implementation.validates_against(schema):
                violations.append(f"Schema violation: {schema.name}")
        
        return violations
```

---

## 🧪 Protocol Testing Suite

### **Test Cases for Machine Readability**

#### **Test 1: Protocol Parsing Test**
```python
def test_protocol_parsing():
    """Test that the protocol can be parsed by machines"""
    parser = ProtocolParser()
    
    # Test JSON format
    json_protocol = load_protocol("protocol.json")
    parsed = parser.parse(json_protocol)
    assert parsed is not None
    assert parsed.version == "1.0.0"
    
    # Test YAML format  
    yaml_protocol = load_protocol("protocol.yml")
    parsed = parser.parse(yaml_protocol)
    assert parsed is not None
    
    # Test Markdown format
    md_protocol = load_protocol("protocol.md")
    parsed = parser.parse(md_protocol)
    assert parsed is not None
    
    print("✅ Protocol parsing test passed")
```

#### **Test 2: Code Generation Test**
```python
def test_code_generation():
    """Test that code can be generated from protocol"""
    parser = ProtocolParser()
    protocol = parser.parse(load_protocol("protocol.json"))
    
    # Generate Python code
    python_code = protocol.generate_code("python")
    assert "def register_agent" in python_code
    assert "class HeartbeatManager" in python_code
    
    # Generate JavaScript code
    js_code = protocol.generate_code("javascript")
    assert "function registerAgent" in js_code
    assert "class HeartbeatManager" in js_code
    
    # Generate TypeScript code
    ts_code = protocol.generate_code("typescript")
    assert "interface AgentInfo" in ts_code
    
    print("✅ Code generation test passed")
```

#### **Test 3: Self-Validation Test**
```python
def test_self_validation():
    """Test that the protocol validates itself"""
    protocol = load_protocol("protocol.json")
    
    # Protocol should contain its own schema
    assert "$schema" in protocol
    schema_url = protocol["$schema"]
    
    # Download and validate against schema
    schema = download_schema(schema_url)
    validator = jsonschema.Draft7Validator(schema)
    
    # Validate protocol against its own schema
    errors = list(validator.iter_errors(protocol))
    assert len(errors) == 0, f"Protocol validation errors: {errors}"
    
    print("✅ Self-validation test passed")
```

---

## 🚀 Implementation Roadmap

### **Phase 1: Core Protocol (Week 1-2)**
1. **Protocol Specification** - Complete machine-readable spec
2. **Reference Implementation** - Python reference implementation
3. **Validation Tools** - Protocol validation tools

### **Phase 2: Language Support (Week 3-4)**
1. **SDKs** - Python, JavaScript/TypeScript, Go SDKs
2. **Code Generators** - Generate code from protocol spec
3. **Testing Framework** - Protocol compliance testing

### **Phase 3: Advanced Features (Week 5-6)**
1. **Protocol Versioning** - Support for multiple protocol versions
2. **Protocol Negotiation** - Automatic protocol version negotiation
3. **Protocol Evolution** - Tools for protocol evolution and migration

### **Phase 4: Ecosystem Integration (Week 7-8)**
1. **Framework Plugins** - LangChain, LlamaIndex plugins
2. **Platform Integration** - OpenAI, Anthropic, Google AI integration
3. **Monitoring Tools** - Protocol usage monitoring and analytics

---

## 📚 Protocol Documentation

### **For Agents**
- **Quick Start Guide**: How to implement this protocol in 5 minutes
- **Implementation Examples**: Complete examples for different agent types
- **Troubleshooting Guide**: Common issues and solutions

### **For Developers**
- **API Reference**: Complete API documentation
- **Schema Reference**: Detailed schema documentation
- **Best Practices**: Implementation best practices

### **For Integrators**
- **Integration Guide**: How to integrate with existing systems
- **Testing Guide**: How to test protocol compliance
- **Deployment Guide**: Production deployment guidelines

---

## 🔗 Related Resources

### **Protocol Files**
- `protocol.json` - JSON format protocol specification
- `protocol.yml` - YAML format protocol specification  
- `protocol.md` - Markdown format protocol documentation
- `schemas/` - JSON Schema definitions
- `examples/` - Implementation examples

### **Tools**
- `protocol-parser/` - Protocol parsing library
- `code-generator/` - Code generation tools
- `validator/` - Protocol validation tools
- `test-suite/` - Protocol testing suite

### **Documentation**
- `docs/quickstart.md` - Quick start guide
- `docs/api.md` - API reference
- `docs/schema.md` - Schema reference
- `docs/faq.md` - Frequently asked questions

---

## 📝 Protocol Version History

| Version | Date | Status | Changes |
|---------|------|--------|---------|
| v1.0.0 | 2026-02-22 | Draft | Initial machine-readable protocol |
| v1.1.0 | 2026-03-01 | Planned | Add protocol negotiation |
| v2.0.0 | 2026-04-01 | Planned | Major protocol enhancements |

---

## 🎯 Success Criteria

### **Technical Success**
- [ ] Protocol can be parsed by machines without human intervention
- [ ] Code can be generated from protocol specification
- [ ] Protocol is self-validating
- [ ] Protocol supports multiple formats (JSON, YAML, Markdown)

### **Adoption Success**
- [ ] 10+ agents implement the protocol
- [ ] 3+ language SDKs available
- [ ] Protocol used in production deployments
- [ ] Active community contributions

### **Evolution Success**
- [ ] Protocol versioning system works
- [ ] Backward compatibility maintained
- [ ] Protocol can evolve without breaking changes
- [ ] Migration tools available

---

**Protocol Author**: AgentMesh Protocol Team  
**Last Updated**: 2026-02-22  
**Protocol Status**: Draft - Ready for Implementation  
**Next Steps**: Implement reference implementation and test suite