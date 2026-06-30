from __future__ import annotations

from types import SimpleNamespace

import pytest

from agents.transcription import transcribe_audio
from test_helpers import FakeSTTClient


@pytest.mark.asyncio
async def test_transcription_fallback_without_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("agents.transcription.get_litellm_client", lambda: None)

    transcript = await transcribe_audio(call_id="c1", audio_file_path="mock_data/test_tone.wav")

    assert transcript.call_id == "c1"
    assert transcript.duration_seconds > 0
    assert len(transcript.segments) >= 1
    assert set(segment.speaker for segment in transcript.segments).issubset({"Rep", "Customer"})


@pytest.mark.asyncio
async def test_transcription_parses_provider_segments(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    audio_path = tmp_path / "sample.wav"
    audio_path.write_bytes(b"RIFF....WAVE")

    provider_payload = SimpleNamespace(
        segments=[
            {"start": 0.0, "end": 2.5, "text": "Hello there"},
            {"start": 2.5, "end": 5.0, "text": "Hi, thanks"},
        ],
        text="",
    )
    monkeypatch.setattr(
        "agents.transcription.get_litellm_client",
        lambda: FakeSTTClient(provider_payload),
    )

    transcript = await transcribe_audio(call_id="c2", audio_file_path=str(audio_path))

    assert transcript.call_id == "c2"
    assert len(transcript.segments) == 2
    assert transcript.segments[0].speaker == "Rep"
    assert transcript.segments[1].speaker == "Customer"
    assert "Hello there" in transcript.full_text
