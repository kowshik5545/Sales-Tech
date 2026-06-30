# MVP_PREVIEW.md — What the Product Looks Like After 2 Weeks

> This document describes the end state of the Intelligent Sales Rep Assistant after the 2-week sprint. It is written from the perspective of a user running a live demo.

---

## What You Will See

### 1. React Dashboard — Home Screen

A clean, single-page dashboard with:
- A top navigation bar: **"Intelligent Sales Rep Assistant"** with the current phase status badge.
- A sidebar listing previous call sessions (call date, customer name, deal stage).
- A main content area showing the selected session's full pipeline output.
- An **"Upload New Call"** button in the top right.

---

### 2. Upload Flow

1. Rep clicks **"Upload New Call"**.
2. A modal appears with a file picker (MP3/WAV, max 25 MB).
3. Rep selects the mock sales call audio file and clicks **"Process Call"**.
4. A progress indicator shows the 5 pipeline stages in sequence:
   - `[1/5] Transcribing...`
   - `[2/5] Updating CRM...`
   - `[3/5] Spotting Opportunities...`
   - `[4/5] Drafting Email...`
   - `[5/5] Generating Coaching Feedback...`
5. On completion, the dashboard auto-navigates to the new session view.

---

### 3. Session View — 5 Output Panels

Each panel is a collapsible card on the dashboard:

#### Panel 1 — Call Transcript
```
[00:00] Rep: "Hi Sarah, thanks for making time today..."
[00:08] Customer: "Of course! I've been looking forward to it."
[00:14] Rep: "So last time we spoke, you mentioned your team was struggling with..."
...
```
- Speaker labels: **Rep** / **Customer**
- Timestamps on every turn
- Full scrollable transcript

#### Panel 2 — CRM Record (JSON View)
```json
{
  "contact_name": "Sarah Chen",
  "company": "Acme Corp",
  "deal_stage": "Proposal Sent",
  "pain_points": ["manual reporting", "team onboarding time"],
  "next_steps": "Send pricing deck by Friday; schedule follow-up for Tuesday",
  "call_date": "2026-06-26"
}
```
- A formatted table view alongside the raw JSON toggle.

#### Panel 3 — Opportunities Spotted
```
BUYING SIGNALS DETECTED
━━━━━━━━━━━━━━━━━━━━━━━
1. "We're planning to scale the team by Q3" → High urgency signal (confidence: 0.91)
2. "Budget has been approved for this quarter" → Budget confirmed (confidence: 0.87)

UPSELL / CROSS-SELL FLAGS
━━━━━━━━━━━━━━━━━━━━━━━━━
1. UPSELL → Premium Analytics Add-on: Customer mentioned "better reporting" 3 times (confidence: 0.84)
2. CROSS-SELL → Onboarding Services Package: "onboarding time" cited as top pain point (confidence: 0.79)
```

#### Panel 4 — Follow-Up Email Draft
```
Subject: Next Steps After Our Call Today — Acme Corp × [Your Company]

Hi Sarah,

Thank you for the great conversation this morning! I really appreciated you sharing
the challenges your team is facing around manual reporting and onboarding time.

Based on what we discussed, I'll have the detailed pricing deck over to you by
Friday, as promised. I've also flagged our Premium Analytics Add-on as something
that could directly address the reporting visibility you mentioned — I'll include
a one-pager on that as well.

Looking forward to our follow-up call on Tuesday. In the meantime, feel free to
reach out with any questions.

Best regards,
[Rep Name]
```
- A **"Copy to Clipboard"** button.
- An editable text area for manual tweaks before copying.

#### Panel 5 — Sales Coach Report
```
PERFORMANCE SCORECARD
━━━━━━━━━━━━━━━━━━━━━
Opening & Rapport Building       ████████░░  8/10
Discovery & Needs Analysis       ███████░░░  7/10
Objection Handling               ██████░░░░  6/10
Closing & Next Steps             █████████░  9/10
Talk-to-Listen Ratio             55% Rep / 45% Customer  ⚠️ Slightly high

STRENGTHS
• Excellent specific next steps defined at close
• Built genuine rapport in the opening 2 minutes

AREAS TO IMPROVE
• Objection at 12:34 ("we already tried something like this") was not fully addressed
• Rep spoke for 3 consecutive minutes without a discovery question between 8:00–11:00

RECOMMENDED ACTIONS
1. Practice the "Feel, Felt, Found" objection reframe technique
2. Aim for a question every 90 seconds during discovery
```

---

### 4. What Is NOT in the MVP Demo

- No live streaming; audio upload only.
- No actual CRM sync; JSON output only.
- No email sending; draft display only.
- No login screen; direct dashboard access.
- No mobile layout; desktop only.

---

## AI-First Development Approach: Specification-Driven Development

This MVP was built using **Specification-Driven Development (SDD)**:

- All agents, schemas, and prompts were fully specified in `SPEC.md` and `PROMPT_SEQUENCES.md` before any code was written.
- Copilot Agent Mode was used with guardrails (`copilot-instructions.md`) to generate code that strictly conforms to the spec.
- Each phase was gated by objective criteria in `CHECKPOINTS.md` — no phase began until the previous gate was green.
- LLM outputs are always structured JSON validated against Pydantic schemas, eliminating unpredictable free-text parsing.

The result is a pipeline that is **predictable, testable, and extendable** — not a collection of ad-hoc prompts.
