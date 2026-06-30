# PROMPT_SEQUENCES.md — Copilot Agent Mode Prompt Patterns

> These are battle-tested prompt sequences for building this project with GitHub Copilot Agent Mode.
> Run these prompts in order within each phase. Each prompt builds on the previous state.

---

## How to Use

1. Open Copilot Chat in Agent Mode (`@workspace` context active).
2. Reference this file and run prompts in order.
3. After each prompt, verify the output matches the spec in `SPEC.md` before proceeding.
4. Do not skip prompts — each one sets up context for the next.

---

## Phase 0 — Project Setup

### Prompt 0.1 — Backend Scaffold
```
Create the backend folder structure for a FastAPI Python project following the layout in SPEC.md.
Create:
- backend/main.py with a FastAPI app instance, CORS middleware (allowing localhost:3000), and a health check GET / route returning {"status": "ok"}
- backend/requirements.txt with: fastapi, uvicorn[standard], python-dotenv, supabase, openai, langchain, langchain-openai, langgraph, pydantic, python-multipart
- backend/.env.example with keys: LITELLM_PROXY_URL, LITELLM_VIRTUAL_KEY, LITELLM_STT_MODEL, LITELLM_LLM_MODEL, SUPABASE_URL, SUPABASE_ANON_KEY
Do not create any agent files yet.
```

### Prompt 0.2 — Frontend Scaffold
```
Initialize a React TypeScript frontend in the frontend/ directory using Vite.
Install: axios, @tanstack/react-query, tailwindcss, postcss, autoprefixer.
Configure Tailwind CSS.
Create frontend/src/api/client.ts with an Axios instance pointing to http://localhost:8000.
Create a placeholder frontend/src/App.tsx that renders "Intelligent Sales Rep Assistant" in a centered heading.
```

---

## Phase 1 — Schemas & Database

### Prompt 1.1 — Pydantic Schemas
```
Create backend/models/schemas.py with all Pydantic v2 models exactly as specified in SPEC.md Section 3.
Include: TranscriptSegment, TranscriptOutput, CRMRecord, BuyingSignal, OpportunityFlag, OpportunityReport, EmailDraft, RubricScore, CoachingReport, PipelineState.
Use Literal types where specified. All fields must match the spec exactly.
```

### Prompt 1.2 — Supabase CRUD Layer
```
Create backend/db/supabase_client.py.
Initialize a Supabase client using SUPABASE_URL and SUPABASE_ANON_KEY from environment variables.
Implement these async functions, each returning the relevant Pydantic model from backend/models/schemas.py:
- create_session(audio_file_name: str) -> dict (returns {call_id, status})
- get_session(call_id: str) -> dict
- list_sessions() -> list[dict]
- save_transcript(call_id: str, transcript: TranscriptOutput) -> None
- save_crm_record(call_id: str, crm: CRMRecord) -> None
- save_opportunity_report(call_id: str, report: OpportunityReport) -> None
- save_email_draft(call_id: str, email: EmailDraft) -> None
- save_coaching_report(call_id: str, report: CoachingReport) -> None
- get_full_result(call_id: str) -> dict (joins all 5 output tables)
```

### Prompt 1.3 — API Route Stubs
```
Create backend/api/routes/sessions.py with GET /api/sessions calling list_sessions() from the Supabase client.
Create backend/api/routes/pipeline.py with:
- POST /api/pipeline/run (stub: creates a session and returns {call_id, status: "running"})
- GET /api/pipeline/{call_id}/status (stub: returns {call_id, status: "complete", completed_nodes: []})
- GET /api/pipeline/{call_id}/result (stub: calls get_full_result and returns the dict)
Register both routers in backend/main.py.
```

---

## Phase 2 — Transcription Agent

### Prompt 2.1 — Transcription Agent
```
Create backend/agents/transcription.py.
Implement async function transcribe_audio(audio_file_path: str) -> TranscriptOutput.
Steps:
1. Open the audio file in binary mode.
2. Call LiteLLM proxy STT endpoint at ${LITELLM_PROXY_URL} using bearer token ${LITELLM_VIRTUAL_KEY} and model ${LITELLM_STT_MODEL}.
3. Parse the response segments into List[TranscriptSegment]. Alternate speaker labels: even-index segments are "Rep", odd-index are "Customer".
4. Calculate duration_seconds from the last segment's end time.
5. Build full_text by joining all segment texts.
6. Return TranscriptOutput(call_id=call_id, audio_file_name=filename, duration_seconds=duration, segments=segments, full_text=full_text).
Import TranscriptOutput and TranscriptSegment from backend/models/schemas.py.
```

### Prompt 2.2 — Wire Upload to Transcription
```
Update backend/api/routes/pipeline.py.
Change POST /api/pipeline/run to:
1. Accept a multipart file upload (UploadFile from fastapi).
2. Save the file to a temp directory.
3. Call create_session() to get a call_id.
4. In a background task (BackgroundTasks), call transcribe_audio() and then save_transcript().
5. Return {call_id, status: "running"} immediately (202 response).
Update GET /api/pipeline/{call_id}/status to read the actual status from Supabase.
```

---

## Phase 3 — CRM & Opportunity Agents

### Prompt 3.1 — CRM Extraction Prompt
```
Create backend/prompts/crm_prompt.py.
Define a LangChain ChatPromptTemplate named CRM_PROMPT.
System message: You are a CRM data extraction specialist. Extract structured sales data from the provided call transcript. Return ONLY valid JSON matching the CRMRecord schema. Never hallucinate data that is not explicitly in the transcript.
Human message template: Extract CRM data from this sales call transcript:
{transcript}
Return JSON with these exact fields: contact_name, company, deal_stage (one of: Discovery, Proposal Sent, Negotiation, Closed Won, Closed Lost), pain_points (array of strings), next_steps (string), call_date (today's date in ISO format if not mentioned).
```

### Prompt 3.2 — CRM Automation Agent
```
Create backend/agents/crm_automation.py.
Implement async function extract_crm_data(transcript: TranscriptOutput) -> CRMRecord.
Use the CRM_PROMPT from backend/prompts/crm_prompt.py.
Use ChatOpenAI configured to call LiteLLM proxy (`base_url=${LITELLM_PROXY_URL}/v1`, `api_key=${LITELLM_VIRTUAL_KEY}`) with model=${LITELLM_LLM_MODEL} and model_kwargs={"response_format": {"type": "json_object"}}.
Chain: CRM_PROMPT | llm | JsonOutputParser().
Validate the output against the CRMRecord Pydantic model.
If validation fails, retry once with an error-correction prompt that includes the validation error.
```

### Prompt 3.3 — Opportunity Spotting Prompt + Agent
```
Create backend/prompts/opportunity_prompt.py with OPPORTUNITY_PROMPT ChatPromptTemplate.
System: You are a sales intelligence AI. Analyze this transcript for buying signals and upsell/cross-sell opportunities. Return ONLY valid JSON.
Human: Analyze this transcript and CRM context for commercial opportunities. Return JSON with: buying_signals (array of {quote, signal_type, confidence}) and opportunity_flags (array of {opportunity_type, product_suggestion, evidence, confidence}).
{transcript} {crm_context}

Create backend/agents/opportunity_spotting.py.
Implement async function spot_opportunities(transcript: TranscriptOutput, crm: CRMRecord) -> OpportunityReport.
Follow the same LangChain JSON pattern as the CRM agent.
Validate against OpportunityReport schema.
```

### Prompt 3.4 — LangGraph 3-Node Pipeline
```
Create backend/pipeline/graph.py.
Build a LangGraph StateGraph with state type PipelineState (from backend/models/schemas.py).
Add nodes:
- "transcription_node": calls transcribe_audio, sets state.transcript
- "crm_automation_node": calls extract_crm_data with state.transcript, sets state.crm_record
- "opportunity_spotting_node": calls spot_opportunities with state.transcript and state.crm_record, sets state.opportunity_report
Set entry point to "transcription_node".
Add edges: transcription_node → crm_automation_node → opportunity_spotting_node → END.
Compile the graph and export as `sales_pipeline`.
```

---

## Phase 4 — Email & Coach Agents + Full Pipeline

### Prompt 4.1 — Email Generation Prompt + Agent
```
Create backend/prompts/email_prompt.py with EMAIL_PROMPT.
System: You are an expert B2B sales writer. Write personalized, professional follow-up emails. Be specific and reference actual details from the call. Do not use generic phrases.
Human: Write a follow-up email based on this sales call. Use the customer's name, reference their pain points, mention the agreed next steps, and include the top opportunity if relevant.
Transcript summary: {full_text}
CRM data: {crm_json}
Top opportunity: {top_opportunity}
Return JSON with: subject (string) and body (string, plain text, no markdown).

Create backend/agents/email_generation.py.
Implement async function generate_email(transcript: TranscriptOutput, crm: CRMRecord, opportunities: OpportunityReport) -> EmailDraft.
Use LiteLLM proxy model from ${LITELLM_LLM_MODEL}. Validate against EmailDraft schema.
```

### Prompt 4.2 — Sales Coach Prompt + Agent
```
Create backend/prompts/coach_prompt.py with COACH_PROMPT.
System: You are an expert sales coach. Evaluate the sales representative's performance on this call using the following 5-dimension rubric. Score each dimension 1-10 with specific evidence. Return ONLY valid JSON.
Dimensions: Opening & Rapport Building, Discovery & Needs Analysis, Objection Handling, Closing & Next Steps, Active Listening.

Create backend/agents/sales_coach.py.
Implement async function generate_coaching_report(transcript: TranscriptOutput, crm: CRMRecord) -> CoachingReport.
Before calling the LLM:
- Calculate talk_ratio_rep and talk_ratio_customer from segment durations (sum Rep durations / total duration).
Pass these ratios to the prompt for context.
Validate against CoachingReport schema.
```

### Prompt 4.3 — Complete 5-Node Pipeline
```
Update backend/pipeline/graph.py.
Add two more nodes to the existing StateGraph:
- "email_generation_node": calls generate_email with transcript, crm_record, opportunity_report; sets state.email_draft
- "sales_coach_node": calls generate_coaching_report with transcript, crm_record; sets state.coaching_report
Add edges: opportunity_spotting_node → email_generation_node → sales_coach_node → END.
After each node, set state.status to the node name + "_complete".
On any exception in any node, set state.status = "error" and state.error_message = str(e).
Recompile the graph.
```

### Prompt 4.4 — Wire Full Pipeline to API
```
Update backend/api/routes/pipeline.py.
Update the background task in POST /api/pipeline/run to:
1. Run the full sales_pipeline graph with initial PipelineState.
2. After completion, save all 5 outputs to Supabase using the CRUD functions.
3. Update the session status to "complete" (or "error").
Update GET /api/pipeline/{call_id}/result to return the full PipelineState dict from get_full_result().
```

---

## Phase 5 — React Dashboard

### Prompt 5.1 — API Client & Session List
```
Update frontend/src/api/client.ts with typed functions:
- getSessions(): Promise<SessionSummary[]>
- getPipelineStatus(callId: string): Promise<StatusResponse>
- getPipelineResult(callId: string): Promise<PipelineResult>
- uploadAudio(file: File): Promise<{call_id: string, status: string}>
Define TypeScript interfaces matching the SPEC.md schemas.

Create frontend/src/components/SessionList.tsx.
Use useQuery from @tanstack/react-query to fetch sessions.
Display each session as a clickable card showing: contact name, company, deal stage, call date, status badge.
Highlight the selected session.
```

### Prompt 5.2 — Upload Modal with Progress Polling
```
Create frontend/src/components/UploadModal.tsx.
On file select + submit:
1. Call uploadAudio(file).
2. Poll getPipelineStatus every 3 seconds until status is "complete" or "error".
3. Show a step indicator with 5 steps: Transcribing, Updating CRM, Spotting Opportunities, Drafting Email, Coaching Analysis.
4. On complete, call a callback prop to navigate to the new session.
5. On error, show the error message.
```

### Prompt 5.3 — Result Panels
```
Create these React components using TypeScript. Each accepts the relevant typed props from the PipelineResult interface.

1. frontend/src/components/TranscriptPanel.tsx
- Display segments as a chat-like list.
- Rep segments: right-aligned, blue background.
- Customer segments: left-aligned, gray background.
- Show timestamp in small text above each bubble.

2. frontend/src/components/CRMPanel.tsx
- Display CRM fields in a clean key-value table.
- Toggle button to show raw JSON.

3. frontend/src/components/OpportunityPanel.tsx
- Two sections: "Buying Signals" and "Opportunities".
- Each item shows quote/evidence, type badge, and confidence score as a colored bar.

4. frontend/src/components/EmailPanel.tsx
- Show subject line and body in a styled email preview.
- "Copy to Clipboard" button.
- Editable textarea for the body.

5. frontend/src/components/CoachPanel.tsx
- Show rubric as a table with score bars (1-10).
- Talk ratio as two progress bars side by side.
- Strengths as green bullet points, improvements as amber, actions as blue.
```

### Prompt 5.4 — Dashboard Page
```
Create frontend/src/pages/Dashboard.tsx.
Layout: fixed sidebar (SessionList + Upload button) + scrollable main content area.
On session select: fetch getPipelineResult and render all 5 panels in order:
TranscriptPanel → CRMPanel → OpportunityPanel → EmailPanel → CoachPanel.
Show a loading skeleton while fetching.
Show an error state if the result fetch fails.
Wire UploadModal to the "Upload New Call" button.
Update frontend/src/App.tsx to render Dashboard as the root page.
```

---

## Phase 6 — Testing & Polish

### Prompt 6.1 — Error Handling
```
Add retry logic to backend/agents/crm_automation.py, backend/agents/opportunity_spotting.py, backend/agents/email_generation.py, and backend/agents/sales_coach.py.
Each LLM call should retry up to 2 times on JSONDecodeError or Pydantic ValidationError.
On the retry, append to the prompt: "Your previous response was invalid. Error: {error}. Return ONLY valid JSON matching the schema."
```

### Prompt 6.2 — Smoke Test
```
Create backend/tests/test_pipeline_smoke.py.
Write a pytest test that:
1. Reads mock_data/sample_call.mp3 (or uses a short mock transcript if file not present).
2. Runs the full 5-node pipeline.
3. Asserts that the returned PipelineState has non-null values for all 5 output fields.
4. Asserts that crm_record.contact_name is not empty.
5. Asserts that coaching_report.rubric_scores has exactly 5 items.
Use pytest-asyncio for async test support.
```

### Prompt 6.3 — Feature-Wise Tests
```
Create feature-wise backend test files and implement tests mapped from TEST_CASES.md:
- backend/tests/test_transcription_feature.py
- backend/tests/test_crm_feature.py
- backend/tests/test_opportunity_feature.py
- backend/tests/test_email_feature.py
- backend/tests/test_sales_coach_feature.py

For each file:
1. Include at least one positive case, one negative case, and one validation/persistence case.
2. Mock LiteLLM proxy responses where needed to avoid flaky external calls.
3. Validate Pydantic schema outputs and retry behavior on invalid JSON.
4. Keep tests deterministic and runnable in CI.
```
