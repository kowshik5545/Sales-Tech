from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from supabase import Client, create_client

from models.schemas import (
    CRMRecord,
    CoachingReport,
    EmailDraft,
    OpportunityReport,
    PipelineState,
    SessionSummary,
    TranscriptOutput,
)

logger = logging.getLogger(__name__)

# In-memory fallback so the app runs without Supabase.
LOCAL_STORE: dict[str, dict[str, Any]] = {}
LOCAL_USERS: dict[str, dict[str, Any]] = {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_supabase_client() -> Client | None:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    if not url or not key or "your-project" in url:
        return None
    try:
        return create_client(url, key)
    except Exception as e:
        logger.warning("Supabase client creation failed: %s", e)
        return None


def _safe_execute(fn: Any, label: str = "db op") -> Any:
    try:
        return fn()
    except Exception as e:
        logger.warning("Supabase %s failed: %s", label, e)
        return None


def _to_json(val: Any) -> Any:
    """Convert Pydantic models / lists / dicts to JSON‑compatible values."""
    if hasattr(val, "model_dump"):
        return val.model_dump()
    if isinstance(val, list):
        return [_to_json(v) for v in val]
    if isinstance(val, dict):
        return {k: _to_json(v) for k, v in val.items()}
    return val


# ─── User functions ───────────────────────────────────────


async def get_user_by_email(email: str) -> dict[str, Any] | None:
    local = LOCAL_USERS.get(email)
    if local:
        return local
    sb = _get_supabase_client()
    if not sb:
        return None
    result = _safe_execute(
        lambda: sb.table("users").select("*").eq("email", email).limit(1).execute(),
        label="get_user_by_email",
    )
    rows = getattr(result, "data", []) or []
    if not rows:
        return None
    return dict(rows[0])


async def get_user_by_id(user_id: str) -> dict[str, Any] | None:
    for u in LOCAL_USERS.values():
        if u["id"] == user_id:
            return u
    sb = _get_supabase_client()
    if not sb:
        return None
    result = _safe_execute(
        lambda: sb.table("users").select("*").eq("id", user_id).limit(1).execute(),
        label="get_user_by_id",
    )
    rows = getattr(result, "data", []) or []
    if not rows:
        return None
    return dict(rows[0])


async def list_users() -> list[dict[str, Any]]:
    seen: set[str] = set()
    output: list[dict[str, Any]] = []

    # Always include LOCAL_USERS
    for u in LOCAL_USERS.values():
        if u.get("id") in seen:
            continue
        seen.add(u.get("id", ""))
        output.append({"id": u["id"], "email": u["email"], "name": u["name"], "role": u["role"]})

    # Also include Supabase users
    sb = _get_supabase_client()
    if sb:
        result = _safe_execute(
            lambda: sb.table("users").select("id,email,name,role").order("name").execute(),
            label="list_users",
        )
        rows = getattr(result, "data", []) or []
        for r in rows:
            if r.get("id") in seen:
                continue
            seen.add(r["id"])
            output.append({"id": r["id"], "email": r["email"], "name": r["name"], "role": r["role"]})

    return output


# ─── Session lifecycle ───────────────────────────────────


async def create_session(audio_file_name: str, user_id: str | None = None) -> dict[str, str]:
    call_id = str(uuid.uuid4())
    now = _now_iso()
    LOCAL_STORE[call_id] = {
        "call_id": call_id,
        "audio_file_name": audio_file_name,
        "user_id": user_id,
        "status": "running",
        "created_at": now,
        "transcript": None,
        "crm_record": None,
        "opportunity_report": None,
        "email_draft": None,
        "coaching_report": None,
        "error_message": None,
    }

    sb = _get_supabase_client()
    if sb:
        payload: dict[str, Any] = {"id": call_id, "audio_file_name": audio_file_name, "status": "running", "created_at": now}
        if user_id:
            payload["user_id"] = user_id
        _safe_execute(
            lambda: sb.table("call_sessions").upsert(payload).execute(),
            label="create_session",
        )

    return {"call_id": call_id, "status": "running"}


async def update_session_status(call_id: str, status: str, error_message: str | None = None) -> None:
    if call_id in LOCAL_STORE:
        LOCAL_STORE[call_id]["status"] = status
        LOCAL_STORE[call_id]["error_message"] = error_message

    sb = _get_supabase_client()
    if sb:
        payload: dict[str, Any] = {"status": status}
        if status == "complete":
            payload["completed_at"] = _now_iso()
        if error_message:
            payload["error_message"] = error_message
        _safe_execute(
            lambda: sb.table("call_sessions").update(payload).eq("id", call_id).execute(),
            label="update_session_status",
        )


async def get_session(call_id: str) -> dict[str, Any] | None:
    local = LOCAL_STORE.get(call_id)
    if local:
        return local

    sb = _get_supabase_client()
    if not sb:
        return None

    result = _safe_execute(
        lambda: sb.table("call_sessions")
        .select("id,audio_file_name,status,created_at,completed_at,error_message")
        .eq("id", call_id)
        .limit(1)
        .execute(),
        label="get_session",
    )
    rows = getattr(result, "data", []) or []
    if not rows:
        return None
    row = rows[0]
    return {
        "call_id": row["id"],
        "audio_file_name": row.get("audio_file_name"),
        "status": row.get("status", "pending"),
        "created_at": row.get("created_at"),
        "completed_at": row.get("completed_at"),
        "error_message": row.get("error_message"),
    }


async def get_session_user_id(call_id: str) -> str | None:
    local = LOCAL_STORE.get(call_id)
    if local:
        return local.get("user_id")
    sb = _get_supabase_client()
    if not sb:
        return None
    result = _safe_execute(
        lambda: sb.table("call_sessions").select("user_id").eq("id", call_id).limit(1).execute(),
        label="get_session_user_id",
    )
    rows = getattr(result, "data", []) or []
    if not rows:
        return None
    return rows[0].get("user_id")


# ─── List sessions ───────────────────────────────────────


async def list_sessions(user_role: str | None = None, user_id: str | None = None) -> list[SessionSummary]:
    seen: set[str] = set()
    output: list[SessionSummary] = []

    # Always include LOCAL_STORE sessions (used by tests and in-memory fallback)
    for value in LOCAL_STORE.values():
        if user_role == "rep" and user_id and value.get("user_id") != user_id:
            continue
        cid = value.get("call_id", "")
        if cid in seen:
            continue
        seen.add(cid)
        crm = value.get("crm_record") or {}
        output.append(
            SessionSummary(
                call_id=cid,
                contact_name=crm.get("contact_name") if isinstance(crm, dict) else getattr(crm, "contact_name", None),
                company=crm.get("company") if isinstance(crm, dict) else getattr(crm, "company", None),
                deal_stage=crm.get("deal_stage") if isinstance(crm, dict) else getattr(crm, "deal_stage", None),
                call_date=crm.get("call_date") if isinstance(crm, dict) else getattr(crm, "call_date", None),
                status=value.get("status", "pending"),
            )
        )

    # Also include Supabase entries if available
    sb = _get_supabase_client()
    if sb:
        query = sb.table("call_sessions").select("id,status,created_at").order("created_at", desc=True)
        if user_role == "rep" and user_id:
            try:
                query = query.eq("user_id", user_id)
            except Exception:
                logger.warning("user_id column not available on call_sessions, skipping filter")
        result = _safe_execute(
            lambda q=query: q.execute(),
            label="list_sessions",
        )
        rows = getattr(result, "data", []) or []
        for row in rows:
            cid = row["id"]
            if cid in seen:
                continue
            seen.add(cid)
            crm_result = _safe_execute(
                lambda cid=cid: sb.table("crm_records")
                .select("contact_name,company,deal_stage,call_date,contact_email")
                .eq("call_id", cid)
                .limit(1)
                .execute(),
                label="list_sessions_crm",
            )
            crm_rows = getattr(crm_result, "data", []) or []
            crm = crm_rows[0] if crm_rows else {}
            output.append(
                SessionSummary(
                    call_id=cid,
                    contact_name=crm.get("contact_name"),
                    company=crm.get("company"),
                    deal_stage=crm.get("deal_stage"),
                    call_date=crm.get("call_date"),
                    status=row.get("status", "pending"),
                )
            )

    return sorted(output, key=lambda s: s.call_id, reverse=True)


# ─── Save functions ──────────────────────────────────────


async def save_transcript(call_id: str, transcript: TranscriptOutput) -> None:
    if call_id in LOCAL_STORE:
        LOCAL_STORE[call_id]["transcript"] = transcript.model_dump()

    sb = _get_supabase_client()
    if sb:
        _safe_execute(
            lambda: sb.table("transcripts").upsert(
                {
                    "call_id": call_id,
                    "audio_file_name": transcript.audio_file_name,
                    "full_text": transcript.full_text,
                    "segments": json.loads(transcript.model_dump_json())["segments"],
                    "duration_seconds": transcript.duration_seconds,
                }
            ).execute(),
            label="save_transcript",
        )


async def save_crm_record(call_id: str, crm: CRMRecord) -> None:
    if call_id in LOCAL_STORE:
        LOCAL_STORE[call_id]["crm_record"] = crm.model_dump()

    sb = _get_supabase_client()
    if sb:
        payload = {
            "call_id": call_id,
            "contact_name": crm.contact_name,
            "contact_email": crm.contact_email,
            "company": crm.company,
            "deal_stage": crm.deal_stage,
            "pain_points": crm.pain_points,
            "next_steps": crm.next_steps,
            "call_date": crm.call_date,
        }
        _safe_execute(
            lambda: sb.table("crm_records").delete().eq("call_id", call_id).execute(),
            label="save_crm_record_delete",
        )
        _safe_execute(
            lambda: sb.table("crm_records").insert(payload).execute(),
            label="save_crm_record_insert",
        )


async def save_opportunity_report(call_id: str, report: OpportunityReport) -> None:
    if call_id in LOCAL_STORE:
        LOCAL_STORE[call_id]["opportunity_report"] = report.model_dump()

    sb = _get_supabase_client()
    if sb:
        data = json.loads(report.model_dump_json())
        _safe_execute(
            lambda: sb.table("opportunity_reports").upsert(
                {
                    "call_id": call_id,
                    "buying_signals": data["buying_signals"],
                    "opportunity_flags": data["opportunity_flags"],
                }
            ).execute(),
            label="save_opportunity_report",
        )


async def save_email_draft(call_id: str, email: EmailDraft) -> None:
    if call_id in LOCAL_STORE:
        LOCAL_STORE[call_id]["email_draft"] = email.model_dump()

    sb = _get_supabase_client()
    if sb:
        payload = {
            "call_id": call_id,
            "subject": email.subject,
            "body": email.body,
        }
        _safe_execute(
            lambda: sb.table("email_drafts").delete().eq("call_id", call_id).execute(),
            label="save_email_draft_delete",
        )
        _safe_execute(
            lambda: sb.table("email_drafts").insert(payload).execute(),
            label="save_email_draft_insert",
        )


async def save_coaching_report(call_id: str, report: CoachingReport) -> None:
    if call_id in LOCAL_STORE:
        LOCAL_STORE[call_id]["coaching_report"] = report.model_dump()

    sb = _get_supabase_client()
    if sb:
        data = json.loads(report.model_dump_json())
        _safe_execute(
            lambda: sb.table("coaching_reports").upsert(
                {
                    "call_id": call_id,
                    "rubric_scores": data["rubric_scores"],
                    "talk_ratio_rep": report.talk_ratio_rep,
                    "talk_ratio_customer": report.talk_ratio_customer,
                    "strengths": report.strengths,
                    "areas_to_improve": report.areas_to_improve,
                    "recommended_actions": report.recommended_actions,
                }
            ).execute(),
            label="save_coaching_report",
        )


# ─── Get full pipeline result ────────────────────────────


async def get_full_result(call_id: str) -> PipelineState | None:
    session = LOCAL_STORE.get(call_id)
    if session:
        return PipelineState(
            call_id=call_id,
            audio_file_path="",
            transcript=TranscriptOutput.model_validate(session["transcript"]) if session.get("transcript") else None,
            crm_record=CRMRecord.model_validate(session["crm_record"]) if session.get("crm_record") else None,
            opportunity_report=OpportunityReport.model_validate(session["opportunity_report"]) if session.get("opportunity_report") else None,
            email_draft=EmailDraft.model_validate(session["email_draft"]) if session.get("email_draft") else None,
            coaching_report=CoachingReport.model_validate(session["coaching_report"]) if session.get("coaching_report") else None,
            status=session.get("status", "pending"),
            error_message=session.get("error_message"),
        )

    sb = _get_supabase_client()
    if not sb:
        return None

    session_result = _safe_execute(
        lambda: sb.table("call_sessions").select("id,status,error_message").eq("id", call_id).limit(1).execute(),
        label="get_full_result_session",
    )
    session_rows = getattr(session_result, "data", []) or []
    if not session_rows:
        return None

    def _fetch(table: str, cols: str) -> list:
        r = _safe_execute(
            lambda: sb.table(table).select(cols).eq("call_id", call_id).limit(1).execute(),
            label=f"get_full_result_{table}",
        )
        return getattr(r, "data", []) or []

    t_rows = _fetch("transcripts", "audio_file_name,full_text,segments,duration_seconds")
    c_rows = _fetch("crm_records", "contact_name,contact_email,company,deal_stage,pain_points,next_steps,call_date")
    o_rows = _fetch("opportunity_reports", "buying_signals,opportunity_flags")
    e_rows = _fetch("email_drafts", "subject,body")
    co_rows = _fetch("coaching_reports", "rubric_scores,talk_ratio_rep,talk_ratio_customer,strengths,areas_to_improve,recommended_actions")

    def _validate(model_cls, data, label="component"):
        if data is None:
            return None
        try:
            return model_cls.model_validate(data)
        except Exception as e:
            logger.warning("Failed to validate %s for call %s: %s", label, call_id, e)
            return None

    transcript = None
    if t_rows:
        tr = t_rows[0]
        transcript = _validate(
            TranscriptOutput,
            {
                "call_id": call_id,
                "audio_file_name": tr.get("audio_file_name", "uploaded_audio.wav"),
                "duration_seconds": float(tr.get("duration_seconds", 0)),
                "segments": tr.get("segments", []),
                "full_text": tr.get("full_text", ""),
            },
            "transcript",
        )

    crm = _validate(CRMRecord, c_rows[0], "crm_record") if c_rows else None
    opp = _validate(OpportunityReport, o_rows[0], "opportunity_report") if o_rows else None
    email = _validate(EmailDraft, e_rows[0], "email_draft") if e_rows else None
    coach = _validate(CoachingReport, co_rows[0], "coaching_report") if co_rows else None

    return PipelineState(
        call_id=call_id,
        audio_file_path="",
        transcript=transcript,
        crm_record=crm,
        opportunity_report=opp,
        email_draft=email,
        coaching_report=coach,
        status=session_rows[0].get("status", "pending"),
        error_message=session_rows[0].get("error_message"),
    )
