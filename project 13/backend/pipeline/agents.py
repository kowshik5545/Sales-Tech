from __future__ import annotations

import logging

from agents.crm_automation import extract_crm_data
from agents.email_generation import generate_email
from agents.opportunity_spotting import spot_opportunities
from agents.sales_coach import generate_coaching_report
from agents.transcription import transcribe_audio
from db.supabase_client import (
    save_coaching_report,
    save_crm_record,
    save_email_draft,
    save_opportunity_report,
    save_transcript,
)
from models.schemas import PipelineState

logger = logging.getLogger(__name__)


async def transcription_node(state: PipelineState) -> dict:
    transcript = await transcribe_audio(call_id=state.call_id, audio_file_path=state.audio_file_path)
    await save_transcript(state.call_id, transcript)
    return {"transcript": transcript}


async def crm_automation_node(state: PipelineState) -> dict:
    crm = await extract_crm_data(state.transcript)
    await save_crm_record(state.call_id, crm)
    return {"crm_record": crm}


async def opportunity_spotting_node(state: PipelineState) -> dict:
    report = await spot_opportunities(state.transcript, state.crm_record)
    await save_opportunity_report(state.call_id, report)
    return {"opportunity_report": report}


async def email_generation_node(state: PipelineState) -> dict:
    draft = await generate_email(state.transcript, state.crm_record, state.opportunity_report)
    await save_email_draft(state.call_id, draft)
    return {"email_draft": draft}


async def sales_coach_node(state: PipelineState) -> dict:
    report = await generate_coaching_report(state.transcript, state.crm_record)
    await save_coaching_report(state.call_id, report)
    return {"coaching_report": report}
