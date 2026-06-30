from __future__ import annotations

from agents.client import call_llm_json_with_retry, get_litellm_client, get_llm_model
from models.schemas import CRMRecord, CoachingReport, TranscriptOutput
from prompts.coach_prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE


def _calculate_talk_ratio(transcript: TranscriptOutput) -> tuple[float, float]:
    rep_seconds = 0.0
    customer_seconds = 0.0

    for segment in transcript.segments:
        duration = max(0.0, segment.timestamp_end - segment.timestamp_start)
        if segment.speaker == "Rep":
            rep_seconds += duration
        else:
            customer_seconds += duration

    total = rep_seconds + customer_seconds
    if total == 0:
        return 50.0, 50.0

    rep_ratio = round((rep_seconds / total) * 100, 2)
    customer_ratio = round((customer_seconds / total) * 100, 2)
    return rep_ratio, customer_ratio


async def generate_coaching_report(transcript: TranscriptOutput, crm: CRMRecord) -> CoachingReport:
    talk_ratio_rep, talk_ratio_customer = _calculate_talk_ratio(transcript)
    client = get_litellm_client()

    if client:
        user_prompt = USER_PROMPT_TEMPLATE.format(
            transcript=transcript.full_text,
            crm=crm.model_dump_json(indent=2),
            talk_ratio_rep=talk_ratio_rep,
            talk_ratio_customer=talk_ratio_customer,
        )
        return call_llm_json_with_retry(
            client=client,
            model=get_llm_model(),
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            validator=CoachingReport.model_validate,
            temperature=0.2,
        )

    return CoachingReport.model_validate(
        {
            "rubric_scores": [
                {"dimension": "Opening & Rapport Building", "score": 8, "comment": "Positive opening tone."},
                {"dimension": "Discovery & Needs Analysis", "score": 7, "comment": "Captured core pain points."},
                {"dimension": "Objection Handling", "score": 6, "comment": "Could probe deeper."},
                {"dimension": "Closing & Next Steps", "score": 9, "comment": "Clear action items agreed."},
                {"dimension": "Active Listening", "score": 7, "comment": "Good acknowledgement of concerns."},
            ],
            "talk_ratio_rep": talk_ratio_rep,
            "talk_ratio_customer": talk_ratio_customer,
            "strengths": [
                "Defined concrete next steps.",
                "Maintained a structured call flow.",
            ],
            "areas_to_improve": [
                "Use more follow-up discovery questions.",
                "Address objections with stronger proof points.",
            ],
            "recommended_actions": [
                "Practice objection handling frameworks.",
                "Target a 50/50 talk-to-listen ratio.",
            ],
        }
    )
