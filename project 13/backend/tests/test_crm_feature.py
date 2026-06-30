from __future__ import annotations

import pytest

from agents.crm_automation import extract_crm_data
from models.schemas import TranscriptOutput, TranscriptSegment
from test_helpers import FakeLLMClient


def _sample_transcript() -> TranscriptOutput:
    segments = [
        TranscriptSegment(speaker="Rep", timestamp_start=0.0, timestamp_end=5.0, text="Tell me about your needs"),
        TranscriptSegment(speaker="Customer", timestamp_start=5.0, timestamp_end=9.0, text="Manual reporting is painful"),
    ]
    return TranscriptOutput(
        call_id="call-crm",
        audio_file_name="sample.wav",
        duration_seconds=9.0,
        segments=segments,
        full_text="\n".join(s.text for s in segments),
    )


@pytest.mark.asyncio
async def test_crm_fallback_without_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("agents.crm_automation.get_litellm_client", lambda: None)

    crm = await extract_crm_data(_sample_transcript())

    assert crm.contact_name
    assert crm.company
    assert isinstance(crm.pain_points, list)


@pytest.mark.asyncio
async def test_crm_retries_after_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = FakeLLMClient(
        outputs=[
            "{invalid-json",
            '{"contact_name":"Sarah Chen","company":"Acme Corp","deal_stage":"Discovery","pain_points":["manual reporting"],"next_steps":"send proposal","call_date":"2026-06-26"}',
        ]
    )
    monkeypatch.setattr("agents.crm_automation.get_litellm_client", lambda: fake_client)

    crm = await extract_crm_data(_sample_transcript())

    assert crm.contact_name == "Sarah Chen"
    assert fake_client.chat.completions.call_count == 2
