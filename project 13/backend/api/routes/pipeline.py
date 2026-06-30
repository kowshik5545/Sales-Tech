from __future__ import annotations

import os
import tempfile
import struct
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile

from api.routes.auth import get_current_user, optional_user, require_role
from db.supabase_client import (
    create_session,
    get_full_result,
    get_session,
    save_crm_record,
    save_email_draft,
    update_session_status,
    get_session_user_id,
)
from models.schemas import CRMRecord, EmailDraft, PipelineRunResponse, PipelineStatusResponse
from pipeline.graph import run_pipeline

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])

ALLOWED_MIME_TYPES = {"audio/mpeg", "audio/wav", "audio/x-wav"}
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024

# Magic bytes for audio file validation
WAV_HEADER = b"RIFF"
WAV_WAVE_ID = b"WAVE"
MP3_ID3 = b"ID3"
MP3_SYNC = bytes([0xFF, 0xFB])


async def _check_session_access(call_id: str, current_user: dict) -> dict:
    """Verify session exists and that the user has access (rep can only see own)."""
    session = await get_session(call_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    role = current_user.get("role", "")
    uid = current_user.get("sub")
    if role == "rep":
        owner_id = await get_session_user_id(call_id)
        if owner_id != uid:
            raise HTTPException(status_code=403, detail="Access denied: you can only view your own sessions")
    return session


def _validate_audio_content(data: bytes) -> bool:
    """Check file signature (magic bytes) to confirm it's really audio."""
    if len(data) < 12:
        return False
    if data[:4] == WAV_HEADER and data[8:12] == WAV_WAVE_ID:
        return True
    if data[:3] == MP3_ID3:
        return True
    if len(data) >= 2 and data[:2] == MP3_SYNC:
        return True
    return False


def _sanitize_pipeline_error(exc: Exception) -> str:
    raw = str(exc)
    message = raw.lower()
    if "cannot read" in message and "does not support" in message:
        return (
            "Transcription failed: the audio file was sent to a model that does not support audio input. "
            "This usually means the LiteLLM proxy is routing the transcription request to a chat model "
            "instead of a speech-to-text model. Check your proxy config.\n\n"
            f"Provider error: {raw[:300]}"
        )
    if "401" in message or "unauthorized" in message or "denied" in message:
        return f"Pipeline failed due to provider authorization. Verify configured LiteLLM model access for this key.\n\nProvider error: {raw[:300]}"
    if "timeout" in message:
        return f"Pipeline timed out while calling an external provider. Please retry.\n\nProvider error: {raw[:300]}"
    return f"Pipeline execution failed: {raw[:300]}"


async def _run_pipeline_task(call_id: str, audio_path: str) -> None:
    temp_dir = str(Path(audio_path).parent)
    try:
        await run_pipeline(call_id=call_id, audio_file_path=audio_path)
        await update_session_status(call_id, "complete")
    except Exception as exc:  # noqa: BLE001
        await update_session_status(call_id, "error", error_message=_sanitize_pipeline_error(exc))
    finally:
        try:
            Path(audio_path).unlink(missing_ok=True)
        except OSError:
            pass
        try:
            Path(temp_dir).rmdir()
        except OSError:
            pass


@router.post("/run", response_model=PipelineRunResponse, status_code=202)
async def run_pipeline_endpoint(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...),
    current_user: dict | None = Depends(optional_user),
) -> PipelineRunResponse:
    if audio_file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type. Use MP3 or WAV.")

    content = await audio_file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File is larger than 25 MB.")
    if not _validate_audio_content(content):
        raise HTTPException(
            status_code=400,
            detail="File content does not appear to be a valid audio file (WAV or MP3). The Content-Type was accepted, but the file signature does not match audio formats.",
        )

    suffix = Path(audio_file.filename or "uploaded_audio.wav").suffix or ".wav"
    temp_dir = tempfile.mkdtemp(prefix="sales_rep_audio_")
    temp_path = os.path.join(temp_dir, f"input{suffix}")

    with open(temp_path, "wb") as handle:
        handle.write(content)

    user_id = current_user.get("sub") if current_user else None
    session = await create_session(audio_file.filename or "uploaded_audio.wav", user_id=user_id)
    background_tasks.add_task(_run_pipeline_task, session["call_id"], temp_path)

    return PipelineRunResponse(call_id=session["call_id"], status=session["status"])


@router.patch("/{call_id}/crm")
async def update_crm_record(
    call_id: str,
    crm: CRMRecord,
    current_user: dict = Depends(require_role(["admin", "manager"])),
) -> dict:
    session = await get_session(call_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await save_crm_record(call_id, crm)
    return {"call_id": call_id, "status": "updated"}


@router.patch("/{call_id}/email")
async def update_email_draft(
    call_id: str,
    email: EmailDraft,
    current_user: dict = Depends(require_role(["admin", "manager"])),
) -> dict:
    session = await get_session(call_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await save_email_draft(call_id, email)
    return {"call_id": call_id, "status": "updated"}


@router.get("/{call_id}/status", response_model=PipelineStatusResponse)
async def get_pipeline_status(
    call_id: str,
    current_user: dict = Depends(get_current_user),
) -> PipelineStatusResponse:
    session = await _check_session_access(call_id, current_user)

    completed_nodes: list[str] = []
    if session.get("transcript"):
        completed_nodes.append("transcription_node")
    if session.get("crm_record"):
        completed_nodes.append("crm_automation_node")
    if session.get("opportunity_report"):
        completed_nodes.append("opportunity_spotting_node")
    if session.get("email_draft"):
        completed_nodes.append("email_generation_node")
    if session.get("coaching_report"):
        completed_nodes.append("sales_coach_node")

    return PipelineStatusResponse(call_id=call_id, status=session.get("status", "pending"), completed_nodes=completed_nodes)


@router.get("/{call_id}/result")
async def get_pipeline_result(
    call_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    await _check_session_access(call_id, current_user)
    state = await get_full_result(call_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session result not found")
    return state.model_dump()
