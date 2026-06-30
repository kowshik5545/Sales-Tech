# CHECKPOINTS.md — Phase Gate Criteria

> **Rule:** You cannot start the next phase until every gate criterion for the current phase is GREEN.
> Mark each criterion with ✅ (pass) or ❌ (fail) as you verify it.

---

## Gate 0 — Environment Ready
*Must pass before writing any source code*

| # | Criterion | How to Verify | Status |
|---|---|---|---|
| 0.1 | Python 3.11+ installed | `python --version` | ⬜ |
| 0.2 | Node.js 20+ installed | `node --version` | ⬜ |
| 0.3 | `backend/` venv active and `pip install -r requirements.txt` succeeds | No pip errors | ⬜ |
| 0.4 | `uvicorn main:app --reload` starts without errors | Terminal shows "Uvicorn running on http://127.0.0.1:8000" | ⬜ |
| 0.5 | `GET http://localhost:8000/` returns `{"status": "ok"}` | curl or browser | ⬜ |
| 0.6 | `npm run dev` in `frontend/` starts without errors | Browser shows placeholder page | ⬜ |
| 0.7 | `.env` file exists (copied from `.env.example`) with real LiteLLM + Supabase keys | `cat .env` shows all required keys | ⬜ |
| 0.8 | Supabase project is provisioned | Supabase dashboard accessible | ⬜ |
| 0.9 | LiteLLM proxy credentials work | `curl {LITELLM_PROXY_URL}/v1/models` with bearer key returns model list | ⬜ |

**Gate 0 Decision:** All 9 criteria ✅ → Proceed to Phase 1

---

## Gate 1 — Database & API Skeleton
*Must pass before building any agent*

| # | Criterion | How to Verify | Status |
|---|---|---|---|
| 1.1 | All 6 Supabase tables exist (`call_sessions`, `transcripts`, `crm_records`, `opportunity_reports`, `email_drafts`, `coaching_reports`) | Supabase dashboard → Table Editor | ⬜ |
| 1.2 | All tables have the correct columns matching `SPEC.md` Section 5 | Compare columns manually | ⬜ |
| 1.3 | `backend/models/schemas.py` imports without error | `python -c "from models.schemas import PipelineState"` | ⬜ |
| 1.4 | `backend/db/supabase_client.py` — `create_session()` inserts a row into `call_sessions` | Call function; check Supabase table | ⬜ |
| 1.5 | `GET http://localhost:8000/api/sessions` returns `[]` or a seeded list without error | curl | ⬜ |
| 1.6 | `POST http://localhost:8000/api/pipeline/run` returns `202` with `{call_id, status}` | curl with dummy body | ⬜ |

**Gate 1 Decision:** All 6 criteria ✅ → Proceed to Phase 2

---

## Gate 2 — Transcription Working
*Must pass before building CRM agent*

| # | Criterion | How to Verify | Status |
|---|---|---|---|
| 2.1 | `transcribe_audio("mock_data/sample_call.mp3")` returns a `TranscriptOutput` object without error | Run in Python REPL | ⬜ |
| 2.2 | `transcript.segments` has ≥ 5 items | Check length in REPL | ⬜ |
| 2.3 | Every segment has `speaker` set to either `"Rep"` or `"Customer"` | Inspect segments | ⬜ |
| 2.4 | `transcript.full_text` is non-empty and contains recognizable words from the audio | Visual check | ⬜ |
| 2.5 | Uploading the audio via `POST /api/pipeline/run` creates a row in the `call_sessions` table | Check Supabase | ⬜ |
| 2.6 | A corresponding row appears in the `transcripts` table after upload | Check Supabase | ⬜ |

**Gate 2 Decision:** All 6 criteria ✅ → Proceed to Phase 3

---

## Gate 3 — CRM + Opportunity Pipeline Working
*Must pass before building email and coach agents*

| # | Criterion | How to Verify | Status |
|---|---|---|---|
| 3.1 | `extract_crm_data(transcript)` returns a valid `CRMRecord` without Pydantic validation errors | Run in REPL | ⬜ |
| 3.2 | `crm_record.contact_name` is a non-empty string (not "Unknown") | Inspect output | ⬜ |
| 3.3 | `crm_record.pain_points` is a list with ≥ 1 item | Inspect output | ⬜ |
| 3.4 | `spot_opportunities(transcript, crm)` returns a valid `OpportunityReport` | Run in REPL | ⬜ |
| 3.5 | `opportunity_report.buying_signals` has ≥ 1 item | Inspect output | ⬜ |
| 3.6 | All `confidence` scores are between 0.0 and 1.0 | Inspect output | ⬜ |
| 3.7 | 3-node LangGraph pipeline runs end-to-end without error on sample audio | Run `sales_pipeline.invoke(initial_state)` | ⬜ |
| 3.8 | CRM record and opportunity report rows appear in Supabase | Check tables | ⬜ |

**Gate 3 Decision:** All 8 criteria ✅ → Proceed to Phase 4

---

## Gate 4 — Full 5-Node Pipeline Complete
*Must pass before starting the frontend*

| # | Criterion | How to Verify | Status |
|---|---|---|---|
| 4.1 | `generate_email(transcript, crm, opportunities)` returns valid `EmailDraft` | Run in REPL | ⬜ |
| 4.2 | `email_draft.subject` is non-empty and mentions the customer's name or company | Visual check | ⬜ |
| 4.3 | `email_draft.body` references at least one pain point from the transcript | Visual check | ⬜ |
| 4.4 | `generate_coaching_report(transcript, crm)` returns valid `CoachingReport` | Run in REPL | ⬜ |
| 4.5 | `coaching_report.rubric_scores` has exactly 5 items | Check length | ⬜ |
| 4.6 | `coaching_report.talk_ratio_rep + coaching_report.talk_ratio_customer ≈ 100.0` (within ±1%) | Check math | ⬜ |
| 4.7 | Full 5-node pipeline `sales_pipeline.invoke(initial_state)` completes with `state.status == "complete"` | Run full pipeline | ⬜ |
| 4.8 | All 5 Supabase output tables have rows after a full pipeline run | Check Supabase | ⬜ |
| 4.9 | `GET /api/pipeline/{call_id}/result` returns a JSON object with all 5 output keys non-null | curl | ⬜ |

**Gate 4 Decision:** All 9 criteria ✅ → Proceed to Phase 5

---

## Gate 5 — React Dashboard Complete
*Must pass before integration testing*

| # | Criterion | How to Verify | Status |
|---|---|---|---|
| 5.1 | Dashboard loads at `http://localhost:3000` without console errors | Browser DevTools | ⬜ |
| 5.2 | Session list in sidebar shows existing sessions from Supabase | Visual check | ⬜ |
| 5.3 | Clicking a session displays all 5 panels with the correct data | Visual check | ⬜ |
| 5.4 | Upload modal opens, accepts an audio file, and shows progress indicators | Manual test | ⬜ |
| 5.5 | After pipeline completes, dashboard auto-navigates to the new session result | Manual test | ⬜ |
| 5.6 | TranscriptPanel shows Rep/Customer labels and timestamps | Visual check | ⬜ |
| 5.7 | CRMPanel shows all 6 fields; JSON toggle works | Visual check | ⬜ |
| 5.8 | OpportunityPanel shows ≥ 1 signal and ≥ 1 opportunity with confidence bars | Visual check | ⬜ |
| 5.9 | EmailPanel shows subject + body; copy-to-clipboard works | Manual test | ⬜ |
| 5.10 | CoachPanel shows 5 rubric scores and talk ratio bars | Visual check | ⬜ |

**Gate 5 Decision:** All 10 criteria ✅ → Proceed to Phase 6

---

## Gate 6 — Integration Tests Passing
*Must pass before demo preparation*

| # | Criterion | How to Verify | Status |
|---|---|---|---|
| 6.1 | `pytest backend/tests/test_pipeline_smoke.py` passes all assertions | Terminal: 0 failures | ⬜ |
| 6.2 | Feature-wise test suite exists for all in-scope features (see `TEST_CASES.md`) | Verify mapped test files are present | ⬜ |
| 6.3 | Feature-wise backend tests pass (transcription, CRM, opportunity, email, coach) | `pytest backend/tests/test_*_feature.py` | ⬜ |
| 6.4 | End-to-end flow works on 2 different mock audio files | Manual test both files | ⬜ |
| 6.5 | Pipeline handles a missing/silent audio file gracefully (returns error, not crash) | Test with empty file | ⬜ |
| 6.6 | Supabase has ≥ 3 seeded sessions for demo (pre-processed, ready to view) | Check Supabase | ⬜ |
| 6.7 | No sensitive data (API keys, `.env`) is committed to the repository | `git log --all` check | ⬜ |

**Gate 6 Decision:** All 7 criteria ✅ → Proceed to Phase 7

---

## Gate 7 — Demo Ready
*Final gate before submission*

| # | Criterion | How to Verify | Status |
|---|---|---|---|
| 7.1 | `README.md` includes setup instructions that a new developer can follow | Dry-run setup | ⬜ |
| 7.2 | All documentation files are complete (`SPEC.md`, `PLAN.md`, `DEPENDENCIES.md`, etc.) | File list check | ⬜ |
| 7.3 | Live demo runs without errors from audio upload through all 5 panels | Rehearsal run | ⬜ |
| 7.4 | Demo completes in under 5 minutes | Timed rehearsal | ⬜ |
| 7.5 | Architecture diagram in `docs/architecture.md` matches the actual implementation | Visual comparison | ⬜ |
| 7.6 | All DELIVERABLES.md items are checked off | Review checklist | ⬜ |

**Gate 7 Decision:** All 6 criteria ✅ → **PROJECT COMPLETE — DEMO READY**
