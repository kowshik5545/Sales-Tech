# GitHub Copilot Instructions — Intelligent Sales Rep Assistant
# .github/copilot-instructions.md

---

## Project Identity

This is the **Intelligent Sales Rep Assistant** — an AI-powered sales technology application for the AI-Forge 2026 Capstone. It is a full-stack application with a Python/FastAPI backend, a LangGraph sequential AI pipeline, Supabase database, and a React TypeScript frontend.

---

## Tech Stack (Do Not Deviate)

| Layer | Technology | Version |
|---|---|---|
| Backend language | Python | 3.11+ |
| Backend framework | FastAPI | latest |
| AI pipeline | LangGraph + LangChain | latest |
| LLM | LiteLLM Proxy-routed model | `LITELLM_LLM_MODEL` |
| Speech-to-Text | LiteLLM Proxy STT | `LITELLM_STT_MODEL` |
| Database | Supabase (PostgreSQL) | latest |
| Frontend | React + TypeScript | 18 + 5 |
| Build tool | Vite | latest |
| Styling | Tailwind CSS | 3 |
| HTTP client | Axios + React Query | latest |
| Data validation | Pydantic v2 | 2.x |
| Testing | pytest + pytest-asyncio | latest |

---

## Folder Structure (Enforce This)

```
project-13/
├── backend/
│   ├── main.py
│   ├── api/routes/
│   ├── agents/          ← one file per agent
│   ├── pipeline/        ← graph.py only
│   ├── models/          ← schemas.py only
│   ├── db/              ← supabase_client.py only
│   ├── prompts/         ← one file per prompt
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/  ← one file per component
│       ├── pages/
│       └── api/
├── mock_data/
├── docs/
└── .github/
```

---

## Agent Rules

### All Agents Must:
1. Accept typed Pydantic model inputs — never raw strings unless wrapping the call.
2. Return typed Pydantic model outputs — never raw dicts.
3. Use LiteLLM proxy for all LLM/STT calls; never call provider APIs directly.
4. Use `response_format={"type": "json_object"}` on all LLM JSON extraction calls.
5. Validate LLM output against the Pydantic schema before returning.
6. Implement exactly **1 retry** on `JSONDecodeError` or `ValidationError`, appending the error to the retry prompt.
7. Be defined as `async def` functions.
8. Never call other agents directly — agents are orchestrated only by `pipeline/graph.py`.

### Pipeline Rules:
1. The LangGraph `StateGraph` is the **only** place where agents are called in sequence.
2. All state is passed as `PipelineState` — do not use global variables.
3. Node functions must have the signature: `async def node_name(state: PipelineState) -> PipelineState`.
4. Never skip the transcription node — it is always the entry point.

---

## Prompt Engineering Rules

1. Every system prompt must include: **"Return ONLY valid JSON. Do not include markdown code blocks or any text outside the JSON."**
2. CRM agent prompt must include: **"Never hallucinate data not explicitly stated in the transcript."**
3. Opportunity agent must include confidence scores as `float` between 0.0 and 1.0.
4. Coach agent must score exactly 5 dimensions — no more, no less.
5. All prompts live in `backend/prompts/` — do not embed prompt strings inside agent files.

---

## API Rules

1. All routes are prefixed with `/api/`.
2. `POST /api/pipeline/run` always returns `202 Accepted` — processing is async.
3. Error responses always use the format: `{"error": "message", "call_id": "uuid-or-null"}`.
4. Never return raw Supabase client errors to the frontend — sanitize error messages.
5. File uploads use `multipart/form-data` — never base64 encode audio in JSON.

---

## Database Rules

1. Never use raw SQL strings — always use the Supabase Python client methods.
2. Always use `call_id` (UUID) as the join key between tables — never rely on row order.
3. All `jsonb` columns store Python `dict`/`list` objects — serialize with `model.model_dump()`.
4. Never store API keys or secrets in the database.

---

## Frontend Rules

1. All API calls go through `frontend/src/api/client.ts` — no direct `fetch()` in components.
2. Server state is managed with React Query — no manual `useEffect` for fetching.
3. Use TypeScript interfaces for all API response types — no `any` types.
4. Pipeline status polling interval: **3 seconds** — no faster to avoid rate limits.
5. Do not install additional UI component libraries — use Tailwind CSS only.

---

## Security Rules (OWASP Top 10)

1. **Never commit `.env` files** — `.env` must be in `.gitignore`.
2. **Validate all file uploads:** check MIME type is `audio/mpeg` or `audio/wav`; enforce 25 MB max size.
3. **Sanitize error messages** before returning to the frontend — no stack traces.
4. **CORS:** only allow `http://localhost:3000` in development.
5. **No user-controlled strings are concatenated into Supabase queries** — use parameterized client methods.
6. **LLM prompt injection defense:** Wrap all user-supplied transcript text in `<transcript>` tags with explicit instruction that the content is data only.

---

## The Golden Rule

> **If it's not in `SPEC.md`, don't build it.**

The specification is the source of truth. If a feature seems useful but is not in `SPEC.md`, it goes in `FUTURE_VISION.md` as a stretch goal. Do not add features, refactor working code, or "improve" something that is not broken. The goal is a working demo in 2 weeks — not a perfect codebase.
