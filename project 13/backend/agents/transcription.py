from __future__ import annotations

import asyncio
import logging
import mimetypes
import traceback
from pathlib import Path

from agents.client import get_litellm_client, get_litellm_request_options, get_stt_model, get_whisper_model_name
from models.schemas import TranscriptOutput, TranscriptSegment

logger = logging.getLogger(__name__)

_whisper_available: bool | None = None


def _is_whisper_available() -> bool:
    global _whisper_available
    if _whisper_available is not None:
        return _whisper_available
    try:
        import whisper  # noqa: F401
        _whisper_available = True
        logger.info("openai-whisper is available for local transcription")
    except ImportError:
        _whisper_available = False
        logger.info("openai-whisper not installed, will only use API")
    return _whisper_available


def _assign_speakers(segments: list) -> list[TranscriptSegment]:
    result: list[TranscriptSegment] = []
    for idx, item in enumerate(segments):
        speaker = "Rep" if idx % 2 == 0 else "Customer"
        result.append(
            TranscriptSegment(
                speaker=speaker,
                timestamp_start=float(item.get("start", 0.0)),
                timestamp_end=float(item.get("end", 0.0)),
                text=item.get("text", "").strip(),
            )
        )
    return result


def _build_output(call_id: str, audio_name: str, segments: list[TranscriptSegment]) -> TranscriptOutput:
    full_text = "\n".join(seg.text for seg in segments)
    duration = max((seg.timestamp_end for seg in segments), default=0.0)
    return TranscriptOutput(
        call_id=call_id,
        audio_file_name=audio_name,
        duration_seconds=duration,
        segments=segments,
        full_text=full_text,
    )


def _transcribe_via_api(client, audio_file_path: str, audio_name: str, call_id: str) -> TranscriptOutput:
    request_options = get_litellm_request_options()
    mime_type, _ = mimetypes.guess_type(audio_file_path)
    if not mime_type:
        mime_type = "audio/wav"
    with open(audio_file_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model=get_stt_model(),
            file=(audio_name, audio_file, mime_type),
            response_format="verbose_json",
            **request_options,
        )

    raw_segments = getattr(response, "segments", None) or []
    if not raw_segments:
        text = getattr(response, "text", "No transcription returned").strip()
        segments = [
            TranscriptSegment(
                speaker="Rep",
                timestamp_start=0.0,
                timestamp_end=5.0,
                text=text or "No transcription returned",
            )
        ]
        return _build_output(call_id, audio_name, segments)

    segments = _assign_speakers(raw_segments)
    return _build_output(call_id, audio_name, segments)


def _transcribe_via_whisper(audio_file_path: str, audio_name: str, call_id: str) -> TranscriptOutput:
    import whisper

    model_name = get_whisper_model_name()
    logger.info("Loading whisper model '%s' ...", model_name)
    model = whisper.load_model(model_name)
    logger.info("Transcribing with whisper model '%s' ...", model_name)
    result = model.transcribe(audio_file_path, language="en")

    raw_segments = result.get("segments", [])
    if not raw_segments:
        text = result.get("text", "").strip()
        segments = [
            TranscriptSegment(
                speaker="Rep",
                timestamp_start=0.0,
                timestamp_end=5.0,
                text=text or "No transcription returned",
            )
        ]
        return _build_output(call_id, audio_name, segments)

    segments = _assign_speakers(raw_segments)
    return _build_output(call_id, audio_name, segments)


async def transcribe_audio(call_id: str, audio_file_path: str) -> TranscriptOutput:
    audio_name = Path(audio_file_path).name
    client = get_litellm_client()

    if client:
        try:
            return await asyncio.to_thread(_transcribe_via_api, client, audio_file_path, audio_name, call_id)
        except Exception as exc:
            logger.warning("API transcription failed: %s", exc)

    if _is_whisper_available():
        try:
            logger.info("Falling back to local whisper transcription for %s ...", audio_name)
            return await asyncio.to_thread(_transcribe_via_whisper, audio_file_path, audio_name, call_id)
        except Exception as exc:
            logger.warning("Local whisper transcription failed: %s\n%s", exc, traceback.format_exc())

    raise RuntimeError(
        f"Transcription failed for {audio_name}. "
        "API provider returned an error and no local whisper fallback is available. "
        "Check the LiteLLM proxy configuration and STT model settings."
    )
