# docs/architecture.md — System Architecture

## Intelligent Sales Rep Assistant — In-Scope Architecture

> This diagram represents the **MVP in-scope architecture** only. See `FUTURE_VISION.md` for post-MVP additions.

---

## System Architecture Diagram

```mermaid
graph TB
    subgraph Frontend["Frontend — React + TypeScript + Tailwind CSS"]
        UI["Dashboard Page"]
        SL["Session List\n(sidebar)"]
        UM["Upload Modal\n(file picker + progress)"]
        subgraph Panels["5 Result Panels"]
            TP["TranscriptPanel"]
            CP["CRMPanel"]
            OP["OpportunityPanel"]
            EP["EmailPanel"]
            KP["CoachPanel"]
        end
    end

    subgraph Backend["Backend — Python + FastAPI"]
        API1["POST /api/pipeline/run"]
        API2["GET /api/pipeline/{id}/status"]
        API3["GET /api/pipeline/{id}/result"]
        API4["GET /api/sessions"]
    end

    subgraph Pipeline["Sequential AI Pipeline — LangGraph StateGraph"]
        direction TB
        N1["Node 1\nTranscription Agent\nLiteLLM STT"]
        N2["Node 2\nCRM Automation Agent\nLiteLLM LLM"]
        N3["Node 3\nOpportunity Spotting Agent\nLiteLLM LLM"]
        N4["Node 4\nEmail Generation Agent\nLiteLLM LLM"]
        N5["Node 5\nSales Coach Agent\nLiteLLM LLM"]
        N1 --> N2 --> N3 --> N4 --> N5
    end

    subgraph State["PipelineState (shared)"]
        S1["TranscriptOutput"]
        S2["CRMRecord"]
        S3["OpportunityReport"]
        S4["EmailDraft"]
        S5["CoachingReport"]
    end

    subgraph DB["Database — Supabase (PostgreSQL)"]
        T1["call_sessions"]
        T2["transcripts"]
        T3["crm_records"]
        T4["opportunity_reports"]
        T5["email_drafts"]
        T6["coaching_reports"]
    end

    subgraph External["External APIs"]
        L["LiteLLM Proxy API\n/v1/audio/transcriptions + /v1/chat/completions"]
    end

    %% Frontend → Backend
    UM -->|"multipart/form-data audio file"| API1
    UI -->|"poll every 3s"| API2
    SL -->|"GET"| API4
    Panels -->|"GET on session select"| API3

    %% Backend → Pipeline
    API1 -->|"background task\ninitial PipelineState"| N1

    %% Pipeline → External APIs
    N1 -->|"audio binary"| L
    N2 -->|"transcript text\nJSON mode"| L
    N3 -->|"transcript + CRM\nJSON mode"| L
    N4 -->|"transcript + CRM + opportunities\nJSON mode"| L
    N5 -->|"transcript + CRM\nJSON mode"| L

    %% External → State
    L -->|"TranscriptOutput"| S1
    L -->|"CRMRecord"| S2
    L -->|"OpportunityReport"| S3
    L -->|"EmailDraft"| S4
    L -->|"CoachingReport"| S5

    %% State → DB (after each node)
    S1 -->|"save"| T2
    S2 -->|"save"| T3
    S3 -->|"save"| T4
    S4 -->|"save"| T5
    S5 -->|"save"| T6
    API1 -->|"create session"| T1

    %% DB → Backend (result read)
    T1 & T2 & T3 & T4 & T5 & T6 -->|"join on call_id"| API3

    %% Styling
    classDef node fill:#4f46e5,color:#fff,stroke:#3730a3
    classDef api fill:#0891b2,color:#fff,stroke:#0e7490
    classDef db fill:#059669,color:#fff,stroke:#047857
    classDef ext fill:#d97706,color:#fff,stroke:#b45309
    classDef state fill:#7c3aed,color:#fff,stroke:#6d28d9
    classDef ui fill:#db2777,color:#fff,stroke:#be185d

    class N1,N2,N3,N4,N5 node
    class API1,API2,API3,API4 api
    class T1,T2,T3,T4,T5,T6 db
    class L ext
    class S1,S2,S3,S4,S5 state
    class UI,SL,UM,TP,CP,OP,EP,KP ui
```

---

## Data Flow Sequence

```mermaid
sequenceDiagram
    actor Rep as Sales Rep
    participant FE as React Dashboard
    participant BE as FastAPI Backend
    participant LG as LangGraph Pipeline
    participant LLM as LiteLLM Proxy
    participant SB as Supabase

    Rep->>FE: Upload audio file
    FE->>BE: POST /api/pipeline/run (multipart)
    BE->>SB: create_session() → call_id
    BE-->>FE: 202 {call_id, status: "running"}

    FE->>FE: Start polling GET /status every 3s

    BE->>LG: invoke pipeline (PipelineState)

    LG->>LLM: STT via LiteLLM (audio binary)
    LLM-->>LG: TranscriptOutput
    LG->>SB: save_transcript()

    LG->>LLM: LLM via LiteLLM (transcript → CRM JSON)
    LLM-->>LG: CRMRecord
    LG->>SB: save_crm_record()

    LG->>LLM: LLM via LiteLLM (transcript + CRM → opportunities JSON)
    LLM-->>LG: OpportunityReport
    LG->>SB: save_opportunity_report()

    LG->>LLM: LLM via LiteLLM (transcript + CRM + opp → email)
    LLM-->>LG: EmailDraft
    LG->>SB: save_email_draft()

    LG->>LLM: LLM via LiteLLM (transcript + CRM → coaching JSON)
    LLM-->>LG: CoachingReport
    LG->>SB: save_coaching_report()

    LG->>SB: update session status = "complete"

    FE->>BE: GET /api/pipeline/{call_id}/status
    BE-->>FE: {status: "complete"}

    FE->>BE: GET /api/pipeline/{call_id}/result
    BE->>SB: get_full_result(call_id)
    SB-->>BE: Joined data (all 5 outputs)
    BE-->>FE: PipelineState JSON

    FE->>FE: Render 5 result panels
    FE-->>Rep: Full analysis displayed
```

---

## Component Responsibility Matrix

| Component | Responsibility | Does NOT do |
|---|---|---|
| React Dashboard | Display results; trigger uploads; poll status | Business logic; LLM calls |
| FastAPI Backend | Route handling; file temp storage; background tasks | LLM calls; direct DB writes in routes |
| LangGraph Pipeline | Orchestrate agent sequence; manage PipelineState | HTTP handling; direct DB writes (delegates to CRUD) |
| LangChain Agents | Call LLM; parse response; validate schema | Orchestration; DB operations |
| Supabase CRUD Layer | All database reads/writes | Business logic; LLM calls |
| Pydantic Schemas | Data contracts between all layers | Persistence; HTTP logic |
