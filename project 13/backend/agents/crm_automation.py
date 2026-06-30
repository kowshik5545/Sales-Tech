from __future__ import annotations

from datetime import date

from agents.client import call_llm_json_with_retry, get_litellm_client, get_llm_model
from models.schemas import CRMRecord, TranscriptOutput
from prompts.crm_prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE


async def extract_crm_data(transcript: TranscriptOutput) -> CRMRecord:
    client = get_litellm_client()

    if client:
        user_prompt = USER_PROMPT_TEMPLATE.format(transcript=transcript.full_text)
        return call_llm_json_with_retry(
            client=client,
            model=get_llm_model(),
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            validator=CRMRecord.model_validate,
            temperature=0.1,
        )

    # Local fallback for development mode.
    return CRMRecord(
        contact_name="Sarah Chen",
        contact_email="",
        company="Acme Corp",
        deal_stage="Discovery",
        pain_points=["manual reporting", "low analytics visibility"],
        next_steps="Send pricing deck and schedule follow-up call next Tuesday.",
        call_date=date.today().isoformat(),
    )
