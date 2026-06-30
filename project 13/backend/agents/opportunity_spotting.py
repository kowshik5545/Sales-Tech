from __future__ import annotations

from agents.client import call_llm_json_with_retry, get_litellm_client, get_llm_model
from models.schemas import CRMRecord, OpportunityReport, TranscriptOutput
from prompts.opportunity_prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE


async def spot_opportunities(transcript: TranscriptOutput, crm: CRMRecord) -> OpportunityReport:
    client = get_litellm_client()

    if client:
        user_prompt = USER_PROMPT_TEMPLATE.format(
            transcript=transcript.full_text,
            crm=crm.model_dump_json(indent=2),
        )
        return call_llm_json_with_retry(
            client=client,
            model=get_llm_model(),
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            validator=OpportunityReport.model_validate,
            temperature=0.2,
        )

    return OpportunityReport.model_validate(
        {
            "buying_signals": [
                {
                    "quote": "Budget is approved and we want better analytics visibility.",
                    "signal_type": "budget_confirmed",
                    "confidence": 0.87,
                }
            ],
            "opportunity_flags": [
                {
                    "opportunity_type": "upsell",
                    "product_suggestion": "Premium Analytics Add-on",
                    "evidence": "Customer explicitly requested better analytics visibility.",
                    "confidence": 0.81,
                }
            ],
        }
    )
