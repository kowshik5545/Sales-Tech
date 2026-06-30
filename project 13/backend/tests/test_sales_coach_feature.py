from __future__ import annotations

import pytest

from agents.sales_coach import generate_coaching_report
from models.schemas import CRMRecord, TranscriptOutput, TranscriptSegment
from test_helpers import FakeLLMClient


def _sample_inputs() -> tuple[TranscriptOutput, CRMRecord]:
    segments = [
        TranscriptSegment(speaker="Rep", timestamp_start=0.0, timestamp_end=8.0, text="Tell me about your goals."),
        TranscriptSegment(speaker="Customer", timestamp_start=8.0, timestamp_end=15.0, text="We need faster onboarding."),
    ]
    transcript = TranscriptOutput(
        call_id="call-coach",
        audio_file_name="sample.wav",
        duration_seconds=15.0,
        segments=segments,
        full_text="\n".join(s.text for s in segments),
    )
    crm = CRMRecord(
        contact_name="Sarah Chen",
        company="Acme Corp",
        deal_stage="Discovery",
        pain_points=["slow onboarding"],
        next_steps="follow up",
        call_date="2026-06-26",
    )
    return transcript, crm


@pytest.mark.asyncio
async def test_sales_coach_fallback_without_client(monkeypatch: pytest.MonkeyPatch) -> None:
    transcript, crm = _sample_inputs()
    monkeypatch.setattr("agents.sales_coach.get_litellm_client", lambda: None)

    report = await generate_coaching_report(transcript, crm)

    assert len(report.rubric_scores) == 5
    assert 99.0 <= (report.talk_ratio_rep + report.talk_ratio_customer) <= 101.0


@pytest.mark.asyncio
async def test_sales_coach_retries_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    transcript, crm = _sample_inputs()
    fake_client = FakeLLMClient(
        outputs=[
            '{"rubric_scores":[{"dimension":"Opening","score":7,"comment":"ok"}],"talk_ratio_rep":51.0,"talk_ratio_customer":49.0,"strengths":[],"areas_to_improve":[],"recommended_actions":[]}',
            '{"rubric_scores":[{"dimension":"Opening & Rapport Building","score":8,"comment":"good"},{"dimension":"Discovery & Needs Analysis","score":7,"comment":"solid"},{"dimension":"Objection Handling","score":6,"comment":"needs depth"},{"dimension":"Closing & Next Steps","score":8,"comment":"clear"},{"dimension":"Active Listening","score":7,"comment":"good"}],"talk_ratio_rep":51.0,"talk_ratio_customer":49.0,"strengths":["rapport","clarity"],"areas_to_improve":["objections","question depth"],"recommended_actions":["practice framework","increase probing"]}',
        ]
    )
    monkeypatch.setattr("agents.sales_coach.get_litellm_client", lambda: fake_client)

    report = await generate_coaching_report(transcript, crm)

    assert len(report.rubric_scores) == 5
    assert fake_client.chat.completions.call_count == 2
