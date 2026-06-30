from __future__ import annotations

import pytest

from pipeline.graph import run_pipeline
from db.supabase_client import create_session, get_full_result


@pytest.mark.asyncio
async def test_pipeline_smoke() -> None:
    session = await create_session("test_tone.wav")
    call_id = session["call_id"]
    await run_pipeline(call_id=call_id, audio_file_path="mock_data/test_tone.wav")

    state = await get_full_result(call_id)

    assert state is not None
    assert state.transcript is not None
    assert state.crm_record is not None
    assert state.opportunity_report is not None
    assert state.email_draft is not None
    assert state.coaching_report is not None
    assert state.crm_record.contact_name
    assert len(state.coaching_report.rubric_scores) == 5
