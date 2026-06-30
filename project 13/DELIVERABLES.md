# DELIVERABLES.md — Final Demo Checklist

> This document elaborates on the deliverables listed in `REQUIREMENTS.md` Section 6.
> Check off each item as it is completed. All items must be ✅ before the final demonstration.

---

## 1. Working Application

### Backend (Python / FastAPI)
- [ ] FastAPI app runs on `http://localhost:8000`
- [ ] Health check `GET /` returns `{"status": "ok"}`
- [ ] `POST /api/pipeline/run` — accepts audio file, triggers 5-node pipeline
- [ ] `GET /api/pipeline/{call_id}/status` — returns real-time pipeline status
- [ ] `GET /api/pipeline/{call_id}/result` — returns complete PipelineState JSON
- [ ] `GET /api/sessions` — returns list of all processed sessions
- [ ] All routes return correct HTTP status codes (200, 202, 404, 500)
- [ ] CORS configured for React frontend origin

### Sequential AI Pipeline (LangGraph)
- [ ] Node 1: `transcription_node` — LiteLLM STT → `TranscriptOutput`
- [ ] Node 2: `crm_automation_node` — LiteLLM LLM → `CRMRecord`
- [ ] Node 3: `opportunity_spotting_node` — LiteLLM LLM → `OpportunityReport`
- [ ] Node 4: `email_generation_node` — LiteLLM LLM → `EmailDraft`
- [ ] Node 5: `sales_coach_node` — LiteLLM LLM → `CoachingReport`
- [ ] Pipeline runs nodes in strict sequential order
- [ ] Pipeline state is passed between nodes correctly
- [ ] Error handling: pipeline marks status as "error" on agent failure
- [ ] All LLM agents use structured JSON output mode
- [ ] All outputs validated with Pydantic before saving

### Database (Supabase)
- [ ] `call_sessions` table with all columns
- [ ] `transcripts` table with all columns
- [ ] `crm_records` table with all columns
- [ ] `opportunity_reports` table with all columns
- [ ] `email_drafts` table with all columns
- [ ] `coaching_reports` table with all columns
- [ ] All tables populated after a complete pipeline run
- [ ] ≥ 3 pre-seeded sessions available for demo

### Frontend (React)
- [ ] React app runs on `http://localhost:3000`
- [ ] Session sidebar listing all processed calls
- [ ] Upload modal with file picker
- [ ] Pipeline progress indicator (5 stages)
- [ ] `TranscriptPanel` — speaker labels + timestamps
- [ ] `CRMPanel` — formatted fields + JSON toggle
- [ ] `OpportunityPanel` — signals + opportunities with confidence scores
- [ ] `EmailPanel` — email preview + copy-to-clipboard
- [ ] `CoachPanel` — rubric scores + talk ratio + tips
- [ ] Loading states for API calls
- [ ] Error states for failed API calls

---

## 2. Architecture & Documentation

### Architecture Diagram
- [ ] `docs/architecture.md` contains Mermaid diagram
- [ ] Diagram shows: Frontend → Backend API → LangGraph Pipeline → 5 Nodes → Supabase
- [ ] Diagram is accurate to the actual implementation

### Documentation Files
- [ ] `README.md` — Setup, how to run, current phase status
- [ ] `REQUIREMENTS.md` — Problem, scope, assumptions, success criteria
- [ ] `SPEC.md` — Agent specs, schemas, API contracts, DB schema, folder structure
- [ ] `PLAN.md` — 2-week milestones with task lists
- [ ] `DEPENDENCIES.md` — Dependency graph + critical path
- [ ] `PROMPT_SEQUENCES.md` — Copilot prompts for each phase
- [ ] `CHECKPOINTS.md` — Gate criteria per phase
- [ ] `FUTURE_VISION.md` — MVP + out-of-scope + stretch goals
- [ ] `MVP_PREVIEW.md` — What the product looks like after 2 weeks
- [ ] `BRD.md` — Business Requirements Document
- [ ] `TEST_CASES.md` — Feature-wise test case matrix
- [ ] `.github/copilot-instructions.md` — Copilot guardrails

---

## 3. End-to-End Demo Scenario

The demo must show a complete run using a mock sales call. The following sequence must work live:

### Demo Script Checklist
- [ ] **Step 1:** Open the React dashboard — show 3 pre-seeded sessions in the sidebar
- [ ] **Step 2:** Click any pre-seeded session — show all 5 panels populated with data
- [ ] **Step 3:** Click "Upload New Call" — open the upload modal
- [ ] **Step 4:** Select `mock_data/sample_call.mp3` — click "Process Call"
- [ ] **Step 5:** Watch the 5-stage progress indicator advance in real time
- [ ] **Step 6:** Pipeline completes — dashboard auto-navigates to the new session
- [ ] **Step 7:** Show `TranscriptPanel` — point out speaker labels and timestamps
- [ ] **Step 8:** Show `CRMPanel` — point out extracted contact name, pain points, next steps
- [ ] **Step 9:** Show `OpportunityPanel` — point out ≥ 1 buying signal with confidence score
- [ ] **Step 10:** Show `EmailPanel` — read out the personalized email, demonstrate copy button
- [ ] **Step 11:** Show `CoachPanel` — point out rubric scores and specific coaching tip
- [ ] **Step 12:** Optionally show the Supabase dashboard to prove data is persisted

### Demo Success Criteria
- [ ] Demo completed without any errors or crashes
- [ ] All 5 pipeline outputs are visible and sensible
- [ ] Demo completed in under 5 minutes
- [ ] Questions from reviewers can be answered with reference to documentation

---

## 4. Code Quality Checklist

- [ ] No API keys or secrets committed to the repository
- [ ] `.env` is in `.gitignore`
- [ ] No debug `print()` statements in production code paths
- [ ] All Pydantic models have proper type annotations
- [ ] LangGraph graph compiles without warnings
- [ ] `pytest backend/tests/test_pipeline_smoke.py` passes (0 failures)
- [ ] Feature-wise backend tests pass (transcription, CRM, opportunity, email, coach)
- [ ] `npm run build` in frontend completes without TypeScript errors
- [ ] `requirements.txt` is up to date with pinned versions

---

## Summary Completion Status

| Area | Items | Completed | % |
|---|---|---|---|
| Backend Application | 8 | 0 | 0% |
| AI Pipeline | 11 | 0 | 0% |
| Database | 8 | 0 | 0% |
| Frontend | 11 | 0 | 0% |
| Architecture & Docs | 11 | 0 | 0% |
| Demo Scenario | 12 | 0 | 0% |
| Code Quality | 8 | 0 | 0% |
| **Total** | **69** | **0** | **0%** |

> Update this table as items are checked off to track overall progress.
