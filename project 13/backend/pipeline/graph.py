from __future__ import annotations

import logging

from models.schemas import PipelineState
from pipeline.agents import (
    crm_automation_node,
    email_generation_node,
    opportunity_spotting_node,
    sales_coach_node,
    transcription_node,
)

logger = logging.getLogger(__name__)


async def run_pipeline(call_id: str, audio_file_path: str) -> None:
    logger.info("Starting sequential pipeline for call %s", call_id)

    state = PipelineState(call_id=call_id, audio_file_path=audio_file_path)

    transcription_output = await transcription_node(state)
    state.transcript = transcription_output["transcript"]

    crm_output = await crm_automation_node(state)
    state.crm_record = crm_output["crm_record"]

    opportunity_output = await opportunity_spotting_node(state)
    state.opportunity_report = opportunity_output["opportunity_report"]

    email_output = await email_generation_node(state)
    state.email_draft = email_output["email_draft"]

    coach_output = await sales_coach_node(state)
    state.coaching_report = coach_output["coaching_report"]

    logger.info("Sequential pipeline completed for call %s", call_id)
