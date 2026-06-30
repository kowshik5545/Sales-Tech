from __future__ import annotations

import pytest

from agents.opportunity_spotting import spot_opportunities
from models.schemas import CRMRecord, TranscriptOutput, TranscriptSegment
from test_helpers import FakeLLMClient


def _sample_inputs() -> tuple[TranscriptOutput, CRMRecord]:
    segments = [
        TranscriptSegment(speaker="Rep", timestamp_start=0.0, timestamp_end=5.0, text="Are you expanding this quarter?"),
        TranscriptSegment(speaker="Customer", timestamp_start=5.0, timestamp_end=12.0, text="Budget is approved and we need better analytics."),
    ]
    transcript = TranscriptOutput(
        call_id="call-opp",
        audio_file_name="sample.wav",
        duration_seconds=12.0,
        segments=segments,
        full_text="\n".join(s.text for s in segments),
    )
    crm = CRMRecord(
        contact_name="Sarah Chen",
        company="Acme Corp",
        deal_stage="Discovery",
        pain_points=["manual reporting"],
        next_steps="follow up",
        call_date="2026-06-26",
    )
    return transcript, crm


@pytest.mark.asyncio
async def test_opportunity_fallback_without_client(monkeypatch: pytest.MonkeyPatch) -> None:
    transcript, crm = _sample_inputs()
    monkeypatch.setattr("agents.opportunity_spotting.get_litellm_client", lambda: None)

    report = await spot_opportunities(transcript, crm)

    assert len(report.buying_signals) >= 1
    assert all(0.0 <= signal.confidence <= 1.0 for signal in report.buying_signals)


@pytest.mark.asyncio
async def test_opportunity_retries_invalid_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    transcript, crm = _sample_inputs()
    fake_client = FakeLLMClient(
        outputs=[
            '{"buying_signals":[{"quote":"x","signal_type":"urgency"}],"opportunity_flags":[]}',
            '{"buying_signals":[{"quote":"budget is approved","signal_type":"budget_confirmed","confidence":0.9}],"opportunity_flags":[{"opportunity_type":"upsell","product_suggestion":"Premium Analytics","evidence":"asked for better analytics","confidence":0.81}]}',
        ]
    )
    monkeypatch.setattr("agents.opportunity_spotting.get_litellm_client", lambda: fake_client)

    report = await spot_opportunities(transcript, crm)

    assert len(report.buying_signals) == 1
    assert report.opportunity_flags[0].opportunity_type == "upsell"
    assert fake_client.chat.completions.call_count == 2
