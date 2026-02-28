# AgentMesh Architecture Diagrams

Visual representations of AgentMesh architecture and data flow.

## 🏗️ System Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "AgentMesh Network"
        AM[AgentMesh Server]
        DB[(Storage)]
        LB[Load Balancer]
        Cache[(Cache)]
    end
    
    subgraph "AI Agents"
        A1[WeatherBot]
        A2[TranslationBot]
        A3[ImageGenerator]
        A4[DataAnalyzer]
    end
    
    subgraph "Clients"
        C1[Web App]
        C2[Mobile App]
        C3[CLI Tool]
        C4[Other Services]
    end
    
    A1 -->|Register| AM
    A2 -->|Register| AM
    A3 -->|Register| AM
    A4 -->|Register| AM
    
    AM -->|Store| DB
    AM -->|Cache| Cache
    
    C1 -->|Discover| LB
    C2 -->|Discover| LB
    C3 -->|Discover| LB
    C4 -->|Discover| LB
    
    LB -->|Route| AM
```

### Component Architecture

```mermaid
graph LR
    subgraph "AgentMesh Server"
        API[API Layer]
        Registry[Agent Registry]
        Discovery[Discovery Engine]
        Health[Health Monitor]
        Auth[Authentication]
        CacheMgr[Cache Manager]
    end
    
    subgraph "Storage Layer"
        Primary[(Primary DB)]
        Replica[(Read Replica)]
        Cache[(Redis Cache)]
    end
    
    subgraph "External Services"
        Metrics[Monitoring]
        Logging[Logging]
        Alerting[Alerting]
    end
    
    API --> Registry
    API --> Discovery
    API --> Health
    API --> Auth
    
    Registry --> Primary
    Discovery --> CacheMgr
    CacheMgr --> Cache
    Health --> Primary
    
    API --> Metrics
    API --> Logging
    Health --> Alerting
```

## 🔄 Data Flow

### Agent Registration Flow

```mermaid
sequenceDiagram
    participant A as Agent
    participant API as API Gateway
    participant V as Validator
    participant R as Registry
    participant DB as Database
    participant C as Cache
    
    A->>API: POST /agents/register
    API->>V: Validate AgentCard
    V-->>API: Validation Result
    
    alt Validation Failed
        API-->>A: 400 Bad Request
    else Validation Passed
        API->>R: Register Agent
        R->>DB: Store AgentCard
        DB-->>R: Storage Confirmation
        R->>C: Update Cache
        C-->>R: Cache Updated
        R-->>API: Registration Success
        API-->>A: 201 Created
    end
```

### Agent Discovery Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant API as API Gateway
    participant D as Discovery Engine
    participant Cache as Cache
    participant DB as Database
    
    C->>API: GET /agents/discover?skill=weather
    API->>D: Discover Agents
    
    D->>Cache: Check Cache
    alt Cache Hit
        Cache-->>D: Cached Results
        D-->>API: Return Results
        API-->>C: 200 OK
    else Cache Miss
        Cache-->>D: Cache Miss
        D->>DB: Query Database
        DB-->>D: Query Results
        D->>Cache: Update Cache
        Cache-->>D: Cache Updated
        D-->>API: Return Results
        API-->>C: 200 OK
    end
```

### Health Monitoring Flow

```mermaid
sequenceDiagram
    participant A as Agent
    participant HM as Health Monitor
    participant R as Registry
    participant DB as Database
    participant Alert as Alerting System
    
    loop Every 30 seconds
        A->>HM: POST /heartbeat
        HM->>R: Update Health Status
        R->>DB: Update last_seen
        DB-->>R: Update Confirmed
        R-->>HM: Status Updated
        HM-->>A: 200 OK
    end
    
    Note over HM,DB: Health Check Logic
    HM->>DB: Check Stale Agents
    DB-->>HM: Stale Agents List
    
    loop For each stale agent
        HM->>Alert: Send Alert
        Alert-->>HM: Alert Sent
        HM->>R: Mark as Unhealthy
        R->>DB: Update Status
    end
```

## 🏢 Deployment Architecture

### Single Server Deployment

```mermaid
graph TB
    subgraph "Single Server"
        Web[Web Server<br/>Nginx/Apache]
        App[AgentMesh App]
        DB[(Database)]
        Cache[(Redis)]
    end
    
    Client1[Client 1] --> Web
    Client2[Client 2] --> Web
    Agent1[Agent 1] --> Web
    Agent2[Agent 2] --> Web
    
    Web --> App
    App --> DB
    App --> Cache
```

### High Availability Deployment

```mermaid
graph TB
    subgraph "Load Balancer Layer"
        LB[Load Balancer]
    end
    
    subgraph "Application Layer"
        App1[App Server 1]
        App2[App Server 2]
        App3[App Server 3]
    end
    
    subgraph "Database Layer"
        Primary[(Primary DB)]
        Replica1[(Read Replica 1)]
        Replica2[(Read Replica 2)]
    end
    
    subgraph "Cache Layer"
        Redis1[Redis Master]
        Redis2[Redis Slave]
        Redis3[Redis Slave]
    end
    
    Client --> LB
    Agent --> LB
    
    LB --> App1
    LB --> App2
    LB --> App3
    
    App1 --> Primary
    App2 --> Primary
    App3 --> Primary
    
    App1 --> Redis1
    App2 --> Redis1
    App3 --> Redis1
    
    Primary --> Replica1
    Primary --> Replica2
    
    Redis1 --> Redis2
    Redis1 --> Redis3
```

### Kubernetes Deployment

```mermaid
graph TB
    subgraph "Kubernetes Cluster"
        subgraph "Namespace: agentmesh"
            subgraph "Deployment: agentmesh"
                Pod1[Pod: agentmesh-1]
                Pod2[Pod: agentmesh-2]
                Pod3[Pod: agentmesh-3]
            end
            
            subgraph "Service: agentmesh"
                SVC[LoadBalancer Service]
            end
            
            subgraph "ConfigMap"
                Config[Configuration]
            end
            
            subgraph "Secret"
                Secrets[Sensitive Data]
            end
        end
        
        subgraph "StatefulSet: redis"
            Redis1[Redis Pod 1]
            Redis2[Redis Pod 2]
            Redis3[Redis Pod 3]
        end
        
        subgraph "StatefulSet: postgres"
            PG1[Postgres Primary]
            PG2[Postgres Replica]
        end
    end
    
    External[External Traffic] --> Ingress[Ingress]
    Ingress --> SVC
    SVC --> Pod1
    SVC --> Pod2
    SVC --> Pod3
    
    Pod1 --> Config
    Pod2 --> Config
    Pod3 --> Config
    
    Pod1 --> Secrets
    Pod2 --> Secrets
    Pod3 --> Secrets
    
    Pod1 --> Redis1
    Pod2 --> Redis2
    Pod3 --> Redis3
    
    Pod1 --> PG1
    Pod2 --> PG2
    Pod3 --> PG1
```

## 📊 Data Models Relationship

### AgentCard Relationships

```mermaid
erDiagram
    AGENT_CARD ||--o{ SKILL : contains
    AGENT_CARD ||--o{ TAG : has
    AGENT_CARD ||--|| ENDPOINT : uses
    AGENT_CARD ||--|| PROTOCOL : uses
    
    AGENT_CARD {
        string id PK
        string name
        string version
        string description
        datetime created_at
        datetime updated_at
        string health_status
    }
    
    SKILL {
        string name
        string description
        json parameters
        json returns
        json examples
    }
    
    TAG {
        string name
    }
    
    ENDPOINT {
        string url
        string protocol
    }
    
    PROTOCOL {
        string name
        string version
    }
```

### Database Schema

```mermaid
erDiagram
    AGENTS ||--o{ AGENT_SKILLS : has
    AGENTS ||--o{ AGENT_TAGS : has
    AGENTS ||--o{ HEARTBEATS : receives
    
    AGENTS {
        string id PK
        string name
        string version
        text description
        text endpoint
        string protocol
        string health_status
        datetime created_at
        datetime updated_at
        datetime last_seen
        boolean is_active
        json metadata
    }
    
    AGENT_SKILLS {
        string agent_id FK
        string skill_name
        text description
        json parameters
        json returns
        json examples
    }
    
    AGENT_TAGS {
        string agent_id FK
        string tag
    }
    
    HEARTBEATS {
        string agent_id FK
        datetime timestamp
        string status
        json metrics
    }
    
    SKILL_INDEX {
        string skill_name
        string agent_id FK
        datetime indexed_at
    }
```

## 🔐 Security Architecture

### Authentication Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant API as API Gateway
    participant Auth as Auth Service
    participant DB as User Database
    participant Token as Token Service
    
    C->>API: Request with Credentials
    API->>Auth: Validate Credentials
    Auth->>DB: Check User
    DB-->>Auth: User Found
    Auth->>Token: Generate Token
    Token-->>Auth: JWT Token
    Auth-->>API: Authentication Success
    API-->>C: Return Token
    
    Note over C,API: Subsequent Requests
    C->>API: Request with Token
    API->>Token: Validate Token
    Token-->>API: Token Valid
    API->>DB: Check Permissions
    DB-->>API: Permissions Granted
    API-->>C: Return Data
```

### Network Security Zones

```mermaid
graph TB
    subgraph "Internet"
        Public[Public Clients]
    end
    
    subgraph "DMZ"
        WAF[Web Application Firewall]
        LB[Load Balancer]
        Bastion[Bastion Host]
    end
    
    subgraph "Application Zone"
        API[API Servers]
        Auth[Auth Servers]
        Cache[Cache Servers]
    end
    
    subgraph "Data Zone"
        DB[(Database)]
        Backup[(Backup Storage)]
        Audit[(Audit Logs)]
    end
    
    Public --> WAF
    WAF --> LB
    LB --> API
    LB --> Auth
    
    Bastion --> API
    Bastion --> Auth
    
    API --> Cache
    API --> DB
    Auth --> DB
    
    DB --> Backup
    API --> Audit
    Auth --> Audit
```

## 📈 Monitoring Architecture

### Monitoring Stack

```mermaid
graph TB
    subgraph "AgentMesh Application"
        App1[App Instance 1]
        App2[App Instance 2]
        App3[App Instance 3]
    end
    
    subgraph "Metrics Collection"
        Export1[Metrics Exporter]
        Export2[Metrics Exporter]
        Export3[Metrics Exporter]
    end
    
    subgraph "Log Collection"
        LogAgent1[Log Agent]
        LogAgent2[Log Agent]
        LogAgent3[Log Agent]
    end
    
    subgraph "Central Monitoring"
        Prometheus[Prometheus]
        Loki[Loki]
        Grafana[Grafana]
        AlertManager[Alert Manager]
    end
    
    App1 --> Export1
    App2 --> Export2
    App3 --> Export3
    
    App1 --> LogAgent1
    App2 --> LogAgent2
    App3 --> LogAgent3
    
    Export1 --> Prometheus
    Export2 --> Prometheus
    Export3 --> Prometheus
    
    LogAgent1 --> Loki
    LogAgent2 --> Loki
    LogAgent3 --> Loki
    
    Prometheus --> Grafana
    Loki --> Grafana
    
    Prometheus --> AlertManager
    AlertManager --> Slack[Slack]
    AlertManager --> Email[Email]
    AlertManager --> PagerDuty[PagerDuty]
```

## 🔄 CI/CD Pipeline

### Deployment Pipeline

```mermaid
graph LR
    subgraph "Development"
        Code[Code Changes]
        PR[Pull Request]
        Review[Code Review]
    end
    
    subgraph "CI Pipeline"
        Test[Run Tests]
        Lint[Code Linting]
        Build[Build Image]
        Scan[Security Scan]
    end
    
    subgraph "CD Pipeline"
        Stage[Staging Deployment]
        TestStage[Staging Tests]
        Prod[Production Deployment]
        Monitor[Production Monitoring]
    end
    
    Code --> PR
    PR --> Review
    Review --> Test
    Test --> Lint
    Lint --> Build
    Build --> Scan
    Scan --> Stage
    Stage --> TestStage
    TestStage --> Prod
    Prod --> Monitor
```

## 🎨 Color Legend

### Diagram Color Coding

| Color | Meaning | Example |
|-------|---------|---------|
| 🔵 **Blue** | External Components | Clients, Users |
| 🟢 **Green** | Core Components | AgentMesh Server, Database |
| 🟡 **Yellow** | Supporting Services | Cache, Load Balancer |
| 🔴 **Red** | Security Components | Firewall, Auth Service |
| 🟣 **Purple** | Monitoring Components | Metrics, Logging |
| 🟠 **Orange** | Deployment Components | Kubernetes, Docker |

### Line Style Legend

| Style | Meaning | Example |
|-------|---------|---------|
| **Solid** | Primary Data Flow | API Requests |
| **Dashed** | Secondary Data Flow | Cache Updates |
| **Dotted** | Control Flow | Health Checks |
| **Thick** | High Priority | Critical Alerts |

## 📝 How to Use These Diagrams

### For Documentation
```markdown
Include diagrams in your documentation:

```mermaid
graph LR
    A[Agent] --> B[AgentMesh]
    B --> C[(Database)]
```

### For Presentations
1. Use high-level architecture diagrams for executive summaries
2. Use detailed flow diagrams for technical discussions
3. Use deployment diagrams for operations teams

### For Development
1. Reference data model diagrams when designing schemas
2. Use sequence diagrams for API design
3. Reference security diagrams for threat modeling

## 🔧 Generating Diagrams

### Tools
1. **Mermaid.js**: Used in these diagrams
2. **PlantUML**: Alternative diagram tool
3. **Draw.io**: Visual diagram editor
4. **Excalidraw**: Hand-drawn style diagrams

### Integration
```yaml
# In mkdocs.yml for documentation site
markdown_extensions:
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
```

## 📚 Related Documentation

- [Protocol Specification](protocol_specification.md)
- [API Reference](api_reference.md)
- [Data Models](data_models.md)
- [Deployment Guide](../deployment/guide.md)

---

*Diagrams last updated: February 23, 2026*