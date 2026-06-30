# BRD.md — Business Requirements Document
# Intelligent Sales Rep Assistant
### AI-Forge 2026 Capstone Project — Project 13
**Document Version:** 1.0
**Date:** 2026-06-26
**Status:** Approved for Development

---

## 1. Executive Summary

Sales representatives at modern B2B companies spend a significant portion of their productive time on non-revenue-generating administrative tasks: manually logging call notes into the CRM, composing follow-up emails from memory, and reviewing their own performance without structured feedback. These inefficiencies directly reduce pipeline velocity and rep effectiveness.

The **Intelligent Sales Rep Assistant** is an AI-powered application that automates the entire post-call workflow. By processing a sales call recording through a sequential AI pipeline, the system produces a full CRM update, opportunity analysis, personalized follow-up email, and coaching feedback — all within approximately 60 seconds of the call ending. The result is more selling time, higher CRM data quality, and accelerated rep skill development.

---

## 2. Business Context

### 2.1 Industry Problem

| Pain Point | Business Impact |
|---|---|
| Manual CRM data entry after calls | ~40% of rep time lost to admin; data quality degrades |
| Writing follow-up emails from memory | Delayed follow-up reduces close rates by up to 30% |
| No structured real-time performance feedback | Rep skill development is slow and subjective |
| Missed upsell/cross-sell signals during calls | Revenue leakage from unacted commercial opportunities |
| Call notes are inconsistent across reps | Pipeline data is unreliable for forecasting |

### 2.2 Target Users

| User | Role | Primary Need |
|---|---|---|
| Sales Representative | Primary user | Reduce admin time; get instant post-call insights |
| Sales Manager (post-MVP) | Secondary user | Monitor team performance; track pipeline quality |
| RevOps / CRM Admin (post-MVP) | Tertiary user | Ensure CRM data completeness and accuracy |

### 2.3 Business Opportunity

By eliminating manual post-call admin, a sales team of 10 reps could recover an estimated **2–4 hours per rep per week**. At an average rep cost of $80/hour, this represents ~$80,000–$160,000 in recaptured productive capacity per year for a 10-person team.

---

## 3. Project Scope

### 3.1 In Scope

All features listed in `REQUIREMENTS.md` Section 2:
1. Audio file upload and storage
2. Call transcription (LiteLLM proxy STT) with speaker labels
3. CRM data extraction (LiteLLM proxy structured output)
4. Opportunity and buying signal detection (LiteLLM proxy)
5. Follow-up email generation (LiteLLM proxy)
6. Sales coach feedback with rubric scoring (LiteLLM proxy)
7. Sequential LangGraph pipeline orchestrating all 5 agents
8. Supabase persistence for all pipeline outputs
9. React dashboard displaying all outputs per session

### 3.2 Out of Scope (This Release)

All items listed in `REQUIREMENTS.md` Section 3 are excluded from this release, including live call streaming, native CRM API sync, user authentication, and email sending.

---

## 4. Stakeholders

| Stakeholder | Role | Interest |
|---|---|---|
| Project Team (Developers) | Builders | Deliver a working capstone demo in 2 weeks |
| AI-Forge Programme Lead | Evaluator | Assess AI architecture quality and pipeline design |
| Simulated Sales Rep (Demo User) | Primary user persona | Validate that the product solves the admin burden problem |
| OpenAI | API Provider | API usage within rate and cost limits |
| Supabase | Infrastructure Provider | Data persisted correctly within free tier constraints |

---

## 5. Functional Requirements

### FR-01: Audio Upload
**Priority:** Must Have
The system must accept MP3 and WAV audio file uploads via the React dashboard. Maximum file size: 25 MB. The backend must validate the MIME type before processing.

### FR-02: Call Transcription
**Priority:** Must Have
The system must transcribe uploaded audio using a LiteLLM proxy speech-to-text model (`LITELLM_STT_MODEL`). The transcript must include speaker labels ("Rep" / "Customer") and timestamps for each utterance segment. Transcription must complete within 90 seconds for a 5-minute audio file.

### FR-03: CRM Data Extraction
**Priority:** Must Have
The system must extract the following fields from the transcript using the configured LiteLLM LLM model (`LITELLM_LLM_MODEL`):
- Contact full name
- Company name
- Deal stage (one of: Discovery, Proposal Sent, Negotiation, Closed Won, Closed Lost)
- Pain points (list of strings)
- Agreed next steps (string)
- Call date

The output must be a valid JSON object matching the `CRMRecord` schema in `SPEC.md`. The agent must never hallucinate data not present in the transcript.

### FR-04: Opportunity Detection
**Priority:** Must Have
The system must identify buying signals and upsell/cross-sell opportunities from the transcript. Each finding must include:
- Type (buying signal or opportunity flag)
- Supporting evidence (direct quote or paraphrase)
- Confidence score (float 0.0 – 1.0)

### FR-05: Follow-Up Email Generation
**Priority:** Must Have
The system must generate a personalized follow-up email that:
- Addresses the customer by name
- References at least one specific pain point from the call
- Confirms the agreed next steps
- Is written in a professional B2B tone
- Contains a subject line and plain-text body

### FR-06: Sales Coach Feedback
**Priority:** Must Have
The system must evaluate the sales rep's performance on exactly 5 dimensions:
1. Opening & Rapport Building (score 1–10)
2. Discovery & Needs Analysis (score 1–10)
3. Objection Handling (score 1–10)
4. Closing & Next Steps (score 1–10)
5. Active Listening (score 1–10)

The report must also include:
- Talk-to-listen ratio (Rep % vs. Customer %)
- At least 2 specific strengths
- At least 2 areas for improvement
- At least 2 recommended actions

### FR-07: Sequential Pipeline Orchestration
**Priority:** Must Have
All 5 processing stages must run in strict sequential order via a LangGraph `StateGraph`. Output from each stage must be passed as input to the next. The pipeline state must be persisted after each node so that partial results are not lost if a later node fails.

### FR-08: Data Persistence
**Priority:** Must Have
All pipeline outputs must be saved to Supabase within 5 seconds of each agent completing. Data must be retrievable by `call_id`.

### FR-09: Dashboard Display
**Priority:** Must Have
The React dashboard must display all 5 pipeline outputs for any selected call session. A session history list must be displayed in a sidebar. Results must be displayed within 2 seconds of being fetched from the API.

### FR-10: Pipeline Progress Indication
**Priority:** Should Have
The upload modal must display real-time progress through the 5 pipeline stages while processing is in progress. The frontend must poll the status endpoint every 3 seconds.

---

## 6. Non-Functional Requirements

### NFR-01: Response Time
- Audio upload acknowledgment: < 2 seconds
- Full pipeline completion (5-minute audio): < 120 seconds
- Dashboard result display (after pipeline): < 2 seconds

### NFR-02: Reliability
- The pipeline must handle LLM `JSONDecodeError` or `ValidationError` with 1 automatic retry before marking the run as failed.
- The application must not crash on invalid or silent audio input; it must return a structured error response.

### NFR-03: Security
- No API keys committed to version control (`.env` in `.gitignore`).
- File upload validation: MIME type must be `audio/mpeg` or `audio/wav`; max 25 MB.
- Error messages returned to the frontend must be sanitized (no stack traces, no internal paths).
- CORS restricted to `http://localhost:3000` in development.
- All transcript text passed to LLMs must be wrapped in `<transcript>` tags as a prompt injection defense.

### NFR-04: Maintainability
- Each agent is defined in a single file with clear separation of concerns.
- All prompts live exclusively in `backend/prompts/`.
- All data models live exclusively in `backend/models/schemas.py`.
- No hardcoded API keys, model names in agent files (all via env vars or central config).

### NFR-05: Cost Efficiency
- GPT-4o `max_tokens` must be capped to avoid runaway API costs during development.
- Transcripts cached in Supabase — do not re-transcribe the same `call_id` twice.

---

## 7. Constraints

| Constraint | Detail |
|---|---|
| **Time** | 2-week development sprint (14 calendar days) |
| **Budget** | LiteLLM-routed provider usage limited to demo volume; Supabase free tier |
| **Team Size** | 1–2 developers |
| **Technology** | Stack locked per `copilot-instructions.md`; no deviations |
| **Scope** | Golden Rule: if it's not in `SPEC.md`, don't build it |
| **Audio Format** | MP3 and WAV only; max 25 MB; English language only |
| **Demo Mode** | Single-user, no authentication required for MVP |

---

## 8. Assumptions

1. LiteLLM proxy URL, virtual key, STT model, and LLM model are provisioned before Day 1.
2. A Supabase project is created and accessible before Phase 1 begins.
3. Mock sales call audio files (3–5 minutes, clear English) are available for testing by Phase 2.
4. The demo environment has a stable internet connection for API calls.
5. LiteLLM-routed STT transcription accuracy of ≥ 85% is acceptable for demo purposes.
6. LiteLLM-routed LLM structured JSON output is reliable enough for production demo use without custom fine-tuning.
7. The frontend operates exclusively on desktop browsers (Chrome/Edge latest).

---

## 9. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| LiteLLM upstream provider rate limits during demo | Medium | High | Pre-process demo audio files; cache results in Supabase |
| LiteLLM-routed LLM returns invalid JSON despite JSON mode | Low | Medium | Implement 1 automatic retry with error-correction prompt |
| LiteLLM-routed STT quality poor on noisy audio | Medium | Medium | Use clean, high-quality mock audio files for demo |
| Pipeline takes >120s per call | Low | High | Test with short (3-min) audio; optimize prompt token counts |
| Supabase free tier connection limits | Low | Medium | Use connection pooling; limit concurrent test runs |
| Frontend scope creep delays backend completion | Medium | High | Build React with mock JSON fixtures; unblock from backend progress |
| API keys accidentally committed to git | Low | Critical | Pre-commit hook to detect `.env`; review before every push |

---

## 10. Success Metrics

These metrics define when the project is considered complete:

| Metric | Target | Measurement |
|---|---|---|
| Transcription accuracy | ≥ 85% word accuracy | Manual review of mock call transcript |
| CRM field extraction completeness | 100% of 6 fields populated per run | Automated test assertion |
| Opportunity detection | ≥ 1 buying signal per demo call | Manual review |
| Email personalization | Customer name + ≥ 1 pain point referenced | Manual review |
| Coach rubric coverage | Exactly 5 dimensions scored | Automated assertion |
| End-to-end pipeline latency | < 120 seconds per 5-min audio | Timed test run |
| Demo reliability | Zero crashes across 3 rehearsal runs | Rehearsal log |

---

## 11. Acceptance Criteria

The project is accepted when:

1. All gate criteria in `CHECKPOINTS.md` are GREEN (✅) through Gate 7.
2. All items in `DELIVERABLES.md` are checked off.
3. A live end-to-end demo runs without errors using `mock_data/sample_call.mp3`.
4. All 5 pipeline output panels are visible and populated on the React dashboard.
5. No API keys or secrets are present in the git repository.
6. The architecture diagram in `docs/architecture.md` matches the implemented system.

---

## 12. Timeline

| Milestone | Target Date | Phase |
|---|---|---|
| Environment setup complete | Day 1 | Phase 0 |
| Database + API skeleton live | Day 3 | Phase 1 |
| Transcription agent working | Day 4 | Phase 2 |
| CRM + Opportunity pipeline working | Day 6 | Phase 3 |
| Full 5-node pipeline complete | Day 8 | Phase 4 |
| React dashboard complete | Day 11 | Phase 5 |
| Integration tests passing | Day 13 | Phase 6 |
| **Final demo ready** | **Day 14** | **Phase 7** |

> See `PLAN.md` for the detailed task breakdown per phase.

---

## 13. Approval

| Role | Name | Date | Signature |
|---|---|---|---|
| Project Lead | | 2026-06-26 | |
| Technical Lead | | 2026-06-26 | |
| AI-Forge Programme Lead | | 2026-06-26 | |

---

*This document is the source of truth for business requirements. Technical implementation details are defined in `SPEC.md`.*
