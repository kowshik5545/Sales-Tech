# TEST_CASES.md — Feature-Wise Test Cases

Document Version: 1.0
Date: 2026-06-26
Scope: In-scope MVP features from REQUIREMENTS.md

---

## 1. Test Strategy

Test levels:
- Unit tests: validate schema parsing, helper logic, and transformations.
- Integration tests: validate agent behavior against LiteLLM proxy and Supabase boundaries.
- End-to-end tests: validate upload to dashboard output flow.

Execution policy:
- Every in-scope feature has positive, negative, and boundary cases.
- Every LLM JSON response path has at least one invalid-JSON retry case.
- Every feature must include at least one persistence verification case.

---

## 2. Feature 1 — Audio Upload

Feature goal:
- Accept MP3/WAV uploads up to 25 MB and create a pipeline session.

Test cases:

| ID | Type | Scenario | Input | Expected Result |
|---|---|---|---|---|
| F1-01 | Positive | Valid MP3 upload | MP3, 5 MB | API returns 202 with call_id and status=running |
| F1-02 | Positive | Valid WAV upload | WAV, 10 MB | API returns 202 with call_id and status=running |
| F1-03 | Boundary | Max size accepted | WAV, exactly 25 MB | Accepted; pipeline starts |
| F1-04 | Negative | Size exceeds max | MP3, 25.1 MB | 400/413 with sanitized error |
| F1-05 | Negative | Unsupported type | TXT file | 400 with validation error |
| F1-06 | Negative | Missing file field | multipart without audio_file | 422 validation error |
| F1-07 | Integration | Session row created | Valid upload | call_sessions has new row with matching call_id |
| F1-08 | Security | Path traversal filename | ../../evil.mp3 | Stored safely; no path traversal; request handled safely |

---

## 3. Feature 2 — Call Transcription (LiteLLM STT)

Feature goal:
- Convert uploaded audio into TranscriptOutput with segments, speaker labels, and full_text.

Test cases:

| ID | Type | Scenario | Input | Expected Result |
|---|---|---|---|---|
| F2-01 | Positive | Clear 3-min call transcription | sample_call.mp3 | TranscriptOutput returned; duration_seconds > 0 |
| F2-02 | Positive | Segment parsing | Provider response with segments | segments parsed into schema correctly |
| F2-03 | Boundary | Minimal audio | 5-second audio | Non-empty transcript or graceful no-speech message |
| F2-04 | Negative | Corrupt audio file | invalid binary | Error status saved; no crash |
| F2-05 | Negative | STT provider timeout | simulated timeout | Retry/fallback path triggered; final status set correctly |
| F2-06 | Negative | STT provider 5xx | simulated 503 | Retry/fallback path triggered |
| F2-07 | Integration | Transcript persisted | successful transcription | transcripts table row exists with full_text and segments |
| F2-08 | Data quality | Speaker labeling fallback | no speaker labels from provider | heuristic labels assigned (Rep/Customer only) |

---

## 4. Feature 3 — CRM Automation

Feature goal:
- Extract CRMRecord with six required fields from transcript.

Test cases:

| ID | Type | Scenario | Input | Expected Result |
|---|---|---|---|---|
| F3-01 | Positive | Complete transcript extraction | transcript with all details | CRMRecord valid with all required fields |
| F3-02 | Positive | Missing date fallback | transcript without explicit date | call_date defaults to ISO date policy |
| F3-03 | Negative | Invalid JSON from LLM on first try | mocked invalid JSON then valid JSON | one retry performed; final CRMRecord valid |
| F3-04 | Negative | Persistent invalid JSON | mocked invalid JSON twice | node sets error status and sanitized message |
| F3-05 | Boundary | Empty pain points mention | transcript with weak discovery | pain_points still valid list type |
| F3-06 | Security | Prompt injection in transcript text | transcript contains injection text | output constrained to schema; no rule leakage |
| F3-07 | Integration | Persistence check | valid CRM output | crm_records row created for call_id |
| F3-08 | Validation | Deal stage enum-like control | ambiguous stage in text | deal_stage mapped to allowed set |

---

## 5. Feature 4 — Opportunity Spotting

Feature goal:
- Detect buying signals and upsell/cross-sell opportunities with confidence scores.

Test cases:

| ID | Type | Scenario | Input | Expected Result |
|---|---|---|---|---|
| F4-01 | Positive | Strong buying signals present | transcript with budget + urgency | buying_signals has at least 1 item |
| F4-02 | Positive | Upsell/cross-sell extraction | transcript mentions adjacent need | opportunity_flags has at least 1 item |
| F4-03 | Validation | Confidence bounds | model output confidence values | all confidence values between 0.0 and 1.0 |
| F4-04 | Negative | Invalid JSON once | mocked malformed output then valid | retry succeeds; report valid |
| F4-05 | Negative | Evidence missing | output missing evidence field | schema validation fails and retries |
| F4-06 | Boundary | Low-signal conversation | neutral transcript | valid response with empty or low-confidence lists |
| F4-07 | Integration | Persistence check | successful report | opportunity_reports row created |
| F4-08 | Quality | Quote traceability | signal quote not in transcript | case fails QA rule and flagged |

---

## 6. Feature 5 — Email Generation

Feature goal:
- Generate personalized follow-up email with subject and body.

Test cases:

| ID | Type | Scenario | Input | Expected Result |
|---|---|---|---|---|
| F5-01 | Positive | Standard follow-up draft | transcript + crm + opportunities | subject and body non-empty |
| F5-02 | Quality | Personalization check | known customer name and pain point | body references customer and at least one pain point |
| F5-03 | Quality | Next step inclusion | CRM next_steps present | body includes concrete next step |
| F5-04 | Negative | Invalid JSON once | malformed then valid | retry path returns valid EmailDraft |
| F5-05 | Boundary | Minimal transcript content | short transcript | output still valid schema with coherent text |
| F5-06 | Security | Prompt injection text in transcript | adversarial transcript | safe professional output within schema |
| F5-07 | Integration | Persistence check | valid email draft | email_drafts row exists |
| F5-08 | UI integration | Copy action | draft loaded in EmailPanel | copy-to-clipboard succeeds |

---

## 7. Feature 6 — Sales Coach Feedback

Feature goal:
- Produce five-dimension rubric with talk ratio and actionable feedback.

Test cases:

| ID | Type | Scenario | Input | Expected Result |
|---|---|---|---|---|
| F6-01 | Positive | Full coaching report | transcript + crm | CoachingReport valid |
| F6-02 | Validation | Rubric dimensions count | standard output | rubric_scores has exactly 5 items |
| F6-03 | Validation | Talk ratio consistency | segment durations | talk_ratio_rep + talk_ratio_customer within 99-101 |
| F6-04 | Quality | Actionability check | standard output | recommended_actions length >= 2 |
| F6-05 | Negative | Invalid JSON once | malformed then valid | retry succeeds |
| F6-06 | Negative | Missing rubric field | incomplete output | schema validation fails and retries |
| F6-07 | Integration | Persistence check | valid coaching report | coaching_reports row exists |
| F6-08 | Boundary | One-sided conversation | rep speaks almost all time | ratios reflect imbalance accurately |

---

## 8. Feature 7 — Sequential Pipeline (LangGraph)

Feature goal:
- Ensure strict node order and state propagation across all five nodes.

Test cases:

| ID | Type | Scenario | Input | Expected Result |
|---|---|---|---|---|
| F7-01 | Positive | Full run success | valid audio | state.status=complete and all outputs non-null |
| F7-02 | Order | Node ordering | valid audio | completed_nodes reflect transcription->crm->opportunity->email->coach |
| F7-03 | Negative | Node 2 failure | forced CRM failure | state.status=error, error_message sanitized |
| F7-04 | Recovery | Re-run after failure | same audio re-upload | second run can complete successfully |
| F7-05 | Persistence | Partial data retention | forced failure at node 4 | earlier node outputs remain persisted |
| F7-06 | Performance | Pipeline latency budget | 3-min audio | full run completes <= 120s target |

---

## 9. Feature 8 — Supabase Persistence

Feature goal:
- Persist all outputs by call_id and retrieve complete result payload.

Test cases:

| ID | Type | Scenario | Input | Expected Result |
|---|---|---|---|---|
| F8-01 | Positive | Save transcript | TranscriptOutput | transcripts row saved with call_id |
| F8-02 | Positive | Save CRM | CRMRecord | crm_records row saved with call_id |
| F8-03 | Positive | Save opportunity report | OpportunityReport | opportunity_reports row saved |
| F8-04 | Positive | Save email | EmailDraft | email_drafts row saved |
| F8-05 | Positive | Save coaching | CoachingReport | coaching_reports row saved |
| F8-06 | Integration | Full result join | call_id with all data | /result returns all objects non-null |
| F8-07 | Negative | Missing call_id lookup | unknown call_id | 404 or error response shape as spec |
| F8-08 | Data integrity | Cross-table call_id consistency | completed run | all table rows reference same call_id |

---

## 10. Feature 9 — React Dashboard

Feature goal:
- Display all outputs reliably and support session navigation.

Test cases:

| ID | Type | Scenario | Input | Expected Result |
|---|---|---|---|---|
| F9-01 | Positive | Session list loads | existing sessions | sidebar shows sessions with status |
| F9-02 | Positive | Session selection | click one session | all 5 panels render corresponding data |
| F9-03 | Positive | Upload flow | valid audio upload | progress shown, then new result displayed |
| F9-04 | Negative | API result failure | /result returns 500 | UI error state displayed |
| F9-05 | Negative | Status polling failure | intermittent network fail | user sees retry/error feedback |
| F9-06 | UX | Loading state | slow API | skeleton/loading indicators visible |
| F9-07 | Panel check | Transcript panel | transcript result | timestamps + speaker labels visible |
| F9-08 | Panel check | CRM panel toggle | crm result | formatted view and raw JSON toggle work |
| F9-09 | Panel check | Opportunity panel | opportunity result | confidence bars render correctly |
| F9-10 | Panel check | Email panel copy | email result | copy action succeeds |
| F9-11 | Panel check | Coach panel | coaching result | 5 scores and talk ratios displayed |

---

## 11. Feature 10 — FastAPI Contract Layer

Feature goal:
- API contract stability for run, status, result, and sessions endpoints.

Test cases:

| ID | Type | Scenario | Input | Expected Result |
|---|---|---|---|---|
| F10-01 | Positive | Run endpoint contract | valid multipart upload | 202 with call_id and status |
| F10-02 | Positive | Status endpoint contract | valid call_id | 200 with allowed status values |
| F10-03 | Positive | Result endpoint contract | completed call_id | 200 with full PipelineState shape |
| F10-04 | Positive | Sessions endpoint contract | existing rows | 200 list with session summaries |
| F10-05 | Negative | Invalid call_id format | malformed call_id | 400/422 validation response |
| F10-06 | Security | Sanitized errors | forced backend exception | response does not expose stack trace |

---

## 12. End-to-End Regression Suite

Core E2E scenarios:
- E2E-01: Happy path upload to full dashboard output.
- E2E-02: STT timeout with retry/fallback handling.
- E2E-03: LLM invalid JSON once then recover.
- E2E-04: Silent/corrupt audio returns safe error.
- E2E-05: Re-open previous session from sidebar after new upload.

Pass criteria:
- 100% pass for all P0 cases (F1-01, F2-01, F3-01, F4-01, F5-01, F6-01, F7-01, F8-06, F9-03, F10-01).
- No high-severity defects open.
- End-to-end demo run completes within time budget.

---

## 13. Suggested Test File Mapping

Backend:
- backend/tests/test_upload_api.py
- backend/tests/test_transcription_feature.py
- backend/tests/test_crm_feature.py
- backend/tests/test_opportunity_feature.py
- backend/tests/test_email_feature.py
- backend/tests/test_sales_coach_feature.py
- backend/tests/test_pipeline_orchestration.py
- backend/tests/test_persistence_feature.py
- backend/tests/test_api_contracts.py

Frontend:
- frontend/src/components/__tests__/UploadModal.test.tsx
- frontend/src/components/__tests__/TranscriptPanel.test.tsx
- frontend/src/components/__tests__/CRMPanel.test.tsx
- frontend/src/components/__tests__/OpportunityPanel.test.tsx
- frontend/src/components/__tests__/EmailPanel.test.tsx
- frontend/src/components/__tests__/CoachPanel.test.tsx
- frontend/src/pages/__tests__/Dashboard.integration.test.tsx
