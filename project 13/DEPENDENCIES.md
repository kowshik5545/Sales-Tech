# DEPENDENCIES.md - Intelligent Sales Rep Assistant

## Phase 1: Foundation Dependencies

### Phase 1.1: Core Infrastructure
```mermaid
graph LR
    A[Docker Infrastructure] --> B[Database Layer]
    A --> C[Backend Services]
    A --> D[Frontend App]
    
    B --> E[Supabase PostgreSQL]
    B --> F[Redis Cache]
    
    C --> G[FastAPI Gateway]
    C --> H[Auth Service]
    C --> I[Whisper Service]
    C --> J[CRM Service]
    C --> K[LLM Service]
    C --> L[Coaching Service]
    
    D --> M[React/Vite]
    D --> N[TanStack Query]
    D --> O[WebSocket Client]
```

**Required Before Phase 2:**
- [ ] Docker Compose deployed
- [ ] Database schema initialized
- [ ] JWT + bcrypt auth working
- [ ] RBAC implemented
- [ ] Demo users seeded
- [ ] Environment variables configured

## Phase 2: Pipeline Dependencies

### Phase 2.1: Agent Service Integration
```mermaid
graph TD
    A[Phase 2 Complete] --> B[Pipeline Orchestration]
    
    subgraph "Before Phase 2"
        G[Database] --> H[Agent Interfaces]
        I[Whisper ASR] --> H
        J[OpenAI LLM] --> H
        K[LangGraph] --> H
    end
    
    subgraph "Phase 2 New"
        H --> L[Transcription Agent]
        H --> M[CRM Agent]
        H --> N[Opportunity Agent]
        H --> O[Email Agent]
        H --> P[Coaching Agent]
        L --> Q[Stage Gateway]
        M --> Q
        N --> Q
        O --> Q
        P --> Q
        Q --> R[Database Service]
        R --> G
    end
    
    G --> S[Frontend Polling]
    S --> T[Dashboard UI]
```

**Required Before Phase 3:**
- [ ] All agent interfaces defined
- [ ] Whisper transcription working
- [ ] OpenAI LLM integration
- [ ] LangGraph workflow engine
- [ ] Database agent client functions
- [ ] Basic pipeline orchestration

## Phase 3: Enhanced Pipeline Features

### Phase 3.1: Advanced Pipeline Capabilities
```mermaid
graph TB
    A[Phase 3 Complete] --> B[Advanced Features]
    
    subgraph "Before Phase 3"
        F[Basic Pipeline] --> G[Sequential Processing]
        G --> H[Stage Results Save]
        H --> I[Progress Tracking]
        I --> J[Error Handling]
    end
    
    subgraph "Phase 3 New"
        F --> K[State Management]
        F --> L[Checkpoint/Restart]
        F --> M[Retry Logic]
        F --> N[Progress Streaming]
        F --> O[WebSocket Updates]
        F --> P[Performance Monitoring]
        
        K --> Q[Session State]
        K --> R[Stage State]
        L --> S[Auto-save Points]
        L --> T[Resume Points]
        M --> U[Exponential Backoff]
        M --> V[Failure Classification]
        N --> W[Real-time Progress]
        N --> X[Stage-specific Updates]
        O --> Y[WebSocket Hub]
        P --> Z[Metrics Collection]
        P --> AA[Error Rate Tracking]
    end
    
    B --> BB[Advanced Dashboard]
    B --> BC[Analytics Views]
    B --> BD[Export Features]
```

**Required Before Phase 4:**
- [ ] Agent state management implemented
- [ ] Checkpoint/restore functionality
- [ ] Exponential backoff retry logic
- [ ] Real-time progress streaming
- [ ] WebSocket communication layer
- [ ] Performance monitoring
- [ ] Advanced error classification

## Phase 4: Production Features

### Phase 4.1: Production Hardening
```mermaid
graph LR
    A[Phase 4 Complete] --> B[Production Readiness]
    
    subgraph "Before Phase 4"
        C[Basic Features] --> D[Core Functionality]
        D --> E[Security Basics]
        E --> F[Monitoring Basics]
        F --> G[Deployment Scripts]
    end
    
    subgraph "Phase 4 New"
        C --> H[Load Balancing]
        C --> I[Health Checks]
        C --> J[Logging Enhancement]
        C --> K[Alerting]
        C --> L[Database Optimization]
        C --> M[Performance Tuning]
        C --> N[Security Hardening]
        C --> O[Backup/Restore]
        
        H --> P[API Gateway]
        H --> Q[Load Balancer]
        I --> R[Health Checks]
        I --> S[Dependency Checks]
        J --> T[Structured Logging]
        J --> U[Audit Logs]
        K --> V[Sentry Integration]
        K --> W[Slack/Discord Alerts]
        L --> X[Query Optimization]
        L --> Y[Index Management]
        N --> Z[Rate Limiting]
        N --> AA[Input Validation]
        O --> BB[Automated Backups]
        O --> BC[Recovery Testing]
    end
    
    B --> BD[Cloud Infrastructure]
    B --> BE[Kubernetes]
    B --> BF[CI/CD Pipeline]
```

**Required Before Launch:**
- [ ] Load balancing and scaling
- [ ] Comprehensive health checks
- [ ] Structured logging and audit trails
- [ ] Error tracking and alerting
- [ ] Database optimization
- [ ] Performance tuning
- [ ] Security hardening
- [ ] Backup and recovery
- [ ] Cloud deployment setup
- [ ] CI/CD pipeline automation

## Implementation Dependencies Summary

### Matrix: What Must Be In Place Before What

| Feature | Prerequisites | Dependencies |
|---------|---------------|--------------|
| Trans Transcription | Docker + Auth | Database, Whisper API |
| CRM Extraction | Basic Pipeline | LLM API, Database |
| Opportunity Analysis | CRM Stage | LLM API, CRM Data |
| Email Generation | Opportunity | LLM API, Call Context |
| Coaching Feedback | Email Stage | LLM API, Performance Metrics |
| Checkpoint/Restart | State Mgmt | Database, Session ID |
| Retry Logic | Exponential Backoff | State Mgmt, Error Handling |
| WebSocket Updates | Progress Streaming | WS Hub, Frontend |
| Performance Monitoring | Metrics Collection | Database, Error Tracking |

### Critical Path

1. **Week 1**: Core pipeline + basic auth + database seed
2. **Week 2**: Enhanced pipeline + error handling + WebSocket
3. **Week 3**: Production features + monitoring + deployment
4. **Week 4**: Final hardening + testing + production launch

**Key Blocking Items:**
- [ ] Whisper API key configuration
- [ ] OpenAI API key configuration  
- [ ] Supabase credentials
- [ ] SSL certificates
- [ ] Domain/DNS setup
- [ ] Monitoring service credentials

**Risk Mitigation:**
- Local Whisper fallback for transcription
- API retry with exponential backoff
- Database connection pooling
- Circuit breaker patterns for external APIs
- Comprehensive logging for debugging

This dependency graph ensures that each phase builds upon a solid foundation and prevents building features that cannot work without their prerequisites in place.