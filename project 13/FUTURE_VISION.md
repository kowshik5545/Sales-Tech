# FUTURE_VISION.md — Intelligent Sales Rep Assistant

> This document captures the full product vision beyond the 2-week MVP. It is organized into three horizons: **In-Scope (MVP)**, **Out-of-Scope (Next 3–6 months)**, and **Stretch (12+ months)**.

---

## Horizon 1 — In-Scope MVP (2 Weeks)

These features will be built and demonstrated as part of the capstone submission.

| # | Feature | Description |
|---|---|---|
| 1 | Audio Upload & Transcription | Upload MP3/WAV; LiteLLM-routed STT returns timestamped, speaker-labeled transcript |
| 2 | CRM Automation Agent | Extract 6 structured CRM fields from transcript via LangGraph node |
| 3 | Opportunity Spotting Agent | Identify buying signals + upsell/cross-sell flags with confidence scores |
| 4 | Email Generation Agent | Draft personalized follow-up email from transcript + CRM context |
| 5 | Sales Coach Agent | Score rep on 5-point rubric; return structured improvement tips |
| 6 | Sequential LangGraph Pipeline | 5-node DAG connecting all agents in order |
| 7 | Supabase Persistence | Store all pipeline outputs per call session |
| 8 | React Dashboard | Display all outputs per session; call history list |
| 9 | FastAPI Backend | REST API driving pipeline and serving frontend |

---

## Horizon 2 — Out-of-Scope (Next 3–6 Months)

Features that are architecturally compatible but require additional time, integrations, or infrastructure.

| Feature | Why Not In MVP | Next Step |
|---|---|---|
| **Live call streaming** | Requires WebSocket + telephony bridge (Twilio/Zoom SDK) | Integrate LiteLLM-compatible real-time STT provider |
| **Native Salesforce / HubSpot sync** | OAuth setup + CRM API rate limits add complexity | Build CRM adapter layer behind a common interface |
| **n8n Workflow Automation** | Pipeline handled directly via LangGraph for MVP | Add n8n triggers for external event-driven workflows |
| **Multi-language transcription** | English-only sufficient for demo | Enable provider language detection via LiteLLM + i18n prompt templates |
| **User Authentication (Supabase Auth)** | Single-user demo mode for MVP | Add row-level security + JWT-based session management |
| **Team / Manager Dashboard** | No multi-user model in MVP | Add manager role with aggregate rep performance views |
| **Vector search over call history** | Deferred to keep setup simple | Integrate ChromaDB/Pinecone for semantic call retrieval |
| **Email sending (SendGrid)** | Draft only in MVP | Add one-click send with approval gate |
| **Automated email sending** | Security review needed | Integrate SendGrid with opt-in confirmation |
| **Custom confidence scoring model** | GPT-4o scoring sufficient for demo | Fine-tune a classifier on labeled sales call data |

---

## Horizon 3 — Stretch Goals (12+ Months)

Ambitious capabilities that represent the full product vision for enterprise deployment.

| Feature | Vision |
|---|---|
| **Real-time in-call coaching overlay** | Surface live prompts to the rep mid-call ("Ask about budget now") |
| **Deal risk prediction** | ML model trained on historical closed/lost deals to predict win probability from transcript signals |
| **Competitive intelligence extraction** | Detect competitor mentions and auto-pull battle cards |
| **Voice persona analysis** | Analyze tone, pace, energy, and empathy using audio features (beyond text) |
| **AI-generated call preparation briefs** | Before the call, generate a prospect brief from CRM + LinkedIn data |
| **Rep performance trend analytics** | Track coaching scores over time; identify skill gaps across the team |
| **Automated meeting scheduling** | Extract "let's meet Thursday at 2pm" → create calendar invite automatically |
| **Custom fine-tuned sales LLM** | Fine-tune GPT/LLaMA on company-specific sales playbook data |
| **Mobile app** | iOS/Android app for reps in the field with voice memo → pipeline trigger |
| **CRM-agnostic adapter framework** | Plug-and-play connectors for Salesforce, HubSpot, Pipedrive, Zoho |
| **Compliance & PII redaction** | Automatically redact sensitive customer data before storage |
| **Multi-call deal thread summarization** | Summarize the full deal history across multiple calls into one deal brief |

---

## Development Strategy: Specification-Driven Development (SDD)

This project follows a **Specification-Driven Development** approach:

1. **Spec first** — Every agent, schema, and API endpoint is defined in `SPEC.md` before any code is written.
2. **Prompt engineering before implementation** — All LLM prompts are drafted in `PROMPT_SEQUENCES.md` and validated with sample inputs before integration.
3. **Gate-based progression** — No phase begins until the previous phase's checkpoint in `CHECKPOINTS.md` is green.
4. **Schema contracts** — All inter-agent data is typed as Pydantic models; LLMs are constrained to structured JSON output.
5. **AI-assisted scaffolding** — Copilot Agent Mode is used with guardrails defined in `.github/copilot-instructions.md` to accelerate implementation without deviation from the spec.

This strategy ensures the AI pipeline is predictable, testable, and demo-ready within the 2-week window.
