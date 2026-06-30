from __future__ import annotations

import pytest

from agents.email_generation import generate_email
from models.schemas import CRMRecord, OpportunityReport, TranscriptOutput, TranscriptSegment
from test_helpers import FakeLLMClient


def _sample_inputs() -> tuple[TranscriptOutput, CRMRecord, OpportunityReport]:
    segments = [
        TranscriptSegment(speaker="Rep", timestamp_start=0.0, timestamp_end=5.0, text="Let's review your reporting goals."),
        TranscriptSegment(speaker="Customer", timestamp_start=5.0, timestamp_end=10.0, text="We need better dashboards."),
    ]
    transcript = TranscriptOutput(
        call_id="call-email",
        audio_file_name="sample.wav",
        duration_seconds=10.0,
        segments=segments,
        full_text="\n".join(s.text for s in segments),
    )
    crm = CRMRecord(
        contact_name="Sarah Chen",
        company="Acme Corp",
        deal_stage="Discovery",
        pain_points=["manual reporting"],
        next_steps="Send deck",
        call_date="2026-06-26",
    )
    opportunities = OpportunityReport.model_validate(
        {
            "buying_signals": [{"quote": "need better dashboards", "signal_type": "urgency", "confidence": 0.73}],
            "opportunity_flags": [
                {
                    "opportunity_type": "upsell",
                    "product_suggestion": "Premium Analytics",
                    "evidence": "dashboards",
                    "confidence": 0.8,
                }
            ],
        }
    )
    return transcript, crm, opportunities


@pytest.mark.asyncio
async def test_email_fallback_without_client(monkeypatch: pytest.MonkeyPatch) -> None:
    transcript, crm, opportunities = _sample_inputs()
    monkeypatch.setattr("agents.email_generation.get_litellm_client", lambda: None)

    email = await generate_email(transcript, crm, opportunities)

    assert email.subject
    assert "Sarah" in email.body


@pytest.mark.asyncio
async def test_email_retries_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    transcript, crm, opportunities = _sample_inputs()
    fake_client = FakeLLMClient(
        outputs=[
            "{bad",
            '{"subject":"Next Steps","body":"Hi Sarah, thanks for the discussion. Next steps: Send deck."}',
        ]
    )
    monkeypatch.setattr("agents.email_generation.get_litellm_client", lambda: fake_client)

    email = await generate_email(transcript, crm, opportunities)

    assert email.subject == "Next Steps"
    assert fake_client.chat.completions.call_count == 2
