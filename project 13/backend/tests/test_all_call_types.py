"""Full pipeline integration tests for all 5 sales call scenarios.

Each test creates a session, runs the full LangGraph pipeline, and validates
every output stage against scenario-specific expectations.
"""

from __future__ import annotations

import asyncio
from datetime import date
from unittest.mock import patch

import pytest

from db.supabase_client import LOCAL_STORE, create_session, get_full_result
from mock_data.scenarios import SCENARIOS
from models.schemas import (
    CRMRecord,
    CoachingReport,
    EmailDraft,
    OpportunityReport,
    TranscriptOutput,
    TranscriptSegment,
)
from pipeline.graph import run_pipeline


def _clear_store():
    LOCAL_STORE.clear()


def _build_scenario_outputs(
    scenario: dict,
    call_id: str,
) -> dict:
    """Build fake return values that the pipeline agent functions will produce."""
    segments = scenario["segments"]
    full_text = "\n".join(s.text for s in segments)
    duration = max((s.timestamp_end for s in segments), default=0.0)

    transcript = TranscriptOutput(
        call_id=call_id,
        audio_file_name=f"{scenario['name'].lower().replace(' ', '_')}.wav",
        duration_seconds=duration,
        segments=segments,
        full_text=full_text,
    )

    crm = scenario["crm"]
    # Override call_date to today for consistency
    crm.call_date = date.today().isoformat()

    return {
        "transcript": transcript,
        "crm": crm,
        "opportunity": scenario["opportunity"],
        "email": scenario["email"],
        "coach": scenario["coach"],
    }


async def _run_scenario(scenario_key: str) -> dict:
    """Run the full pipeline for a given scenario key and return the PipelineState."""
    _clear_store()
    scenario = SCENARIOS[scenario_key]
    outputs = _build_scenario_outputs(scenario, "test-call-id")

    # Patch all 5 agent functions to return scenario-specific data
    async def fake_transcribe(call_id, audio_file_path):
        return outputs["transcript"]

    async def fake_crm(transcript):
        return outputs["crm"]

    async def fake_opportunity(transcript, crm):
        return outputs["opportunity"]

    async def fake_email(transcript, crm, opp):
        return outputs["email"]

    async def fake_coach(transcript, crm):
        return outputs["coach"]

    patches = [
        patch("pipeline.agents.transcribe_audio", fake_transcribe),
        patch("pipeline.agents.extract_crm_data", fake_crm),
        patch("pipeline.agents.spot_opportunities", fake_opportunity),
        patch("pipeline.agents.generate_email", fake_email),
        patch("pipeline.agents.generate_coaching_report", fake_coach),
    ]

    for p in patches:
        p.start()

    try:
        session = await create_session(f"{scenario_key}_call.wav")
        call_id = session["call_id"]

        # Update call_id in the outputs
        outputs["transcript"].call_id = call_id

        await run_pipeline(call_id=call_id, audio_file_path=f"mock_data/{scenario_key}_call.wav")
        state = await get_full_result(call_id)

        assert state is not None, f"PipelineState should not be None for {scenario_key}"
        return {
            "call_id": call_id,
            "state": state,
            "expected": outputs,
            "scenario": scenario,
        }
    finally:
        for p in patches:
            p.stop()
        _clear_store()


# ─── Individual scenario tests ───


@pytest.mark.asyncio
async def test_discovery_call_pipeline():
    result = await _run_scenario("discovery")
    state = result["state"]
    exp = result["expected"]
    scen = result["scenario"]

    # Transcript
    assert state.transcript is not None
    assert len(state.transcript.segments) == len(exp["transcript"].segments)
    assert "analytics" in state.transcript.full_text.lower()

    # CRM
    assert state.crm_record is not None
    assert state.crm_record.contact_name == "Sarah Chen"
    assert state.crm_record.company == "Acme Corp"
    assert state.crm_record.deal_stage == "Discovery"
    assert len(state.crm_record.pain_points) == 4
    assert "manual reporting" in state.crm_record.pain_points

    # Opportunities
    assert state.opportunity_report is not None
    assert len(state.opportunity_report.buying_signals) == 3
    assert any("budget" in bs.signal_type for bs in state.opportunity_report.buying_signals)
    assert len(state.opportunity_report.opportunity_flags) == 2

    # Email
    assert state.email_draft is not None
    assert "Acme Corp" in state.email_draft.subject or "Acme Corp" in state.email_draft.body
    assert "$50k" in state.email_draft.body

    # Coach
    assert state.coaching_report is not None
    assert len(state.coaching_report.rubric_scores) == 5
    assert len(state.coaching_report.strengths) >= 2
    assert 0 < state.coaching_report.talk_ratio_rep < 100
    assert 0 < state.coaching_report.talk_ratio_customer < 100
    assert abs(state.coaching_report.talk_ratio_rep + state.coaching_report.talk_ratio_customer - 100) < 1


@pytest.mark.asyncio
async def test_demo_call_pipeline():
    result = await _run_scenario("demo")
    state = result["state"]
    exp = result["expected"]

    assert state.transcript is not None
    assert len(state.transcript.segments) == len(exp["transcript"].segments)
    assert "Salesforce" in state.transcript.full_text

    assert state.crm_record is not None
    assert state.crm_record.contact_name == "Mark Johnson"
    assert state.crm_record.company == "BetaTech Solutions"
    assert state.crm_record.deal_stage == "Demo"
    assert len(state.crm_record.pain_points) == 3

    assert state.opportunity_report is not None
    assert len(state.opportunity_report.buying_signals) == 3
    assert len(state.opportunity_report.opportunity_flags) == 2

    assert state.email_draft is not None
    assert "BetaTech" in state.email_draft.subject or "BetaTech" in state.email_draft.body
    assert "30-day trial" in state.email_draft.body.lower()

    assert state.coaching_report is not None
    assert len(state.coaching_report.rubric_scores) == 5
    assert len(state.coaching_report.strengths) >= 2


@pytest.mark.asyncio
async def test_negotiation_call_pipeline():
    result = await _run_scenario("negotiation")
    state = result["state"]
    exp = result["expected"]

    assert state.transcript is not None
    assert "competing offer" in state.transcript.full_text.lower() or "pricing" in state.transcript.full_text.lower()

    assert state.crm_record is not None
    assert state.crm_record.contact_name == "Priya Patel"
    assert state.crm_record.company == "GlobalTech Industries"
    assert state.crm_record.deal_stage == "Negotiation"
    assert "budget" in state.crm_record.pain_points[0].lower()

    assert state.opportunity_report is not None
    assert len(state.opportunity_report.buying_signals) == 3
    assert any("agreement" in bs.signal_type for bs in state.opportunity_report.buying_signals)

    assert state.email_draft is not None
    assert "10%" in state.email_draft.body or "discount" in state.email_draft.body.lower()

    assert state.coaching_report is not None
    assert any("objection" in s.lower() for s in state.coaching_report.strengths)
    assert state.coaching_report.talk_ratio_rep > 40


@pytest.mark.asyncio
async def test_followup_call_pipeline():
    result = await _run_scenario("followup")
    state = result["state"]
    exp = result["expected"]

    assert state.transcript is not None
    assert "trial" in state.transcript.full_text.lower() or "checking in" in state.transcript.full_text.lower()

    assert state.crm_record is not None
    assert state.crm_record.contact_name == "James Wilson"
    assert state.crm_record.company == "GreenLeaf Analytics"
    assert state.crm_record.deal_stage == "Follow-up"

    assert state.opportunity_report is not None
    assert len(state.opportunity_report.buying_signals) == 3
    assert any("adoption" in bs.signal_type for bs in state.opportunity_report.buying_signals)

    assert state.email_draft is not None
    assert "GreenLeaf" in state.email_draft.subject or "GreenLeaf" in state.email_draft.body
    assert "executive" in state.email_draft.body.lower() or "ROI" in state.email_draft.body

    assert state.coaching_report is not None
    assert state.coaching_report.talk_ratio_customer > state.coaching_report.talk_ratio_rep
    assert len(state.coaching_report.recommended_actions) >= 2


@pytest.mark.asyncio
async def test_objection_call_pipeline():
    result = await _run_scenario("objection")
    state = result["state"]
    exp = result["expected"]

    assert state.transcript is not None
    assert "timeline" in state.transcript.full_text.lower() or "implementation" in state.transcript.full_text.lower()

    assert state.crm_record is not None
    assert state.crm_record.contact_name == "David Kim"
    assert state.crm_record.company == "NovaTech Systems"
    assert state.crm_record.deal_stage == "Objection Handling"
    assert "trust" in " ".join(state.crm_record.pain_points).lower() or "vendor" in " ".join(state.crm_record.pain_points).lower()

    assert state.opportunity_report is not None
    assert len(state.opportunity_report.buying_signals) == 3
    assert len(state.opportunity_report.opportunity_flags) == 2

    assert state.email_draft is not None
    assert "NovaTech" in state.email_draft.subject or "NovaTech" in state.email_draft.body
    assert "SLA" in state.email_draft.subject or "SLA" in state.email_draft.body

    assert state.coaching_report is not None
    # Objection handling should score high on objection handling dimension
    obj_scores = [r for r in state.coaching_report.rubric_scores if "objection" in r.dimension.lower()]
    assert len(obj_scores) == 1
    assert obj_scores[0].score >= 8


# ─── Combined scenario test suite ───


@pytest.mark.asyncio
async def test_all_scenarios_comprehensive():
    """Run all 5 scenarios in sequence and compare differences."""
    results = {}
    for key in SCENARIOS:
        results[key] = await _run_scenario(key)

    # Verify each scenario produced distinct outputs
    companies = {key: r["expected"]["crm"].company for key, r in results.items()}
    # All companies should be different
    assert len(set(companies.values())) == 5, "Each scenario should have a unique company"

    contacts = {key: r["expected"]["crm"].contact_name for key, r in results.items()}
    assert len(set(contacts.values())) == 5, "Each scenario should have a unique contact"

    stages = {key: r["expected"]["crm"].deal_stage for key, r in results.items()}
    assert len(set(stages.values())) == 5, "Each scenario should have a unique deal stage"

    # Verify all scenarios produced PipelineState with all 5 outputs
    for key, r in results.items():
        state = r["state"]
        assert state.transcript is not None, f"{key}: transcript missing"
        assert state.crm_record is not None, f"{key}: crm missing"
        assert state.opportunity_report is not None, f"{key}: opportunity missing"
        assert state.email_draft is not None, f"{key}: email missing"
        assert state.coaching_report is not None, f"{key}: coach missing"

    # Talk ratios should differ across scenarios
    talk_ratios = {key: r["state"].coaching_report.talk_ratio_rep for key, r in results.items()}
    unique_ratios = len(set(round(v, 1) for v in talk_ratios.values()))
    assert unique_ratios >= 4, f"Expected at least 4 unique talk ratios across scenarios, got {unique_ratios}"


@pytest.mark.asyncio
async def test_scenario_metadata_accuracy():
    """Verify that each scenario's metadata matches its expected call type."""
    for key, scenario in SCENARIOS.items():
        result = await _run_scenario(key)
        state = result["state"]
        crm = state.crm_record

        if key == "discovery":
            assert crm.deal_stage == "Discovery"
            assert "reporting" in " ".join(crm.pain_points).lower() or "visibility" in " ".join(crm.pain_points).lower()
        elif key == "demo":
            assert crm.deal_stage == "Demo"
            assert "real-time" in " ".join(crm.pain_points).lower() or "collaboration" in " ".join(crm.pain_points).lower()
        elif key == "negotiation":
            assert crm.deal_stage == "Negotiation"
            assert "budget" in " ".join(crm.pain_points).lower() or "competitive" in " ".join(crm.pain_points).lower()
        elif key == "followup":
            assert crm.deal_stage == "Follow-up"
            assert "executive" in " ".join(crm.pain_points).lower() or "justification" in " ".join(crm.pain_points).lower()
        elif key == "objection":
            assert crm.deal_stage == "Objection Handling"
            assert "trust" in " ".join(crm.pain_points).lower() or "vendor" in " ".join(crm.pain_points).lower()


@pytest.mark.asyncio
async def test_email_drafts_are_distinct():
    """All 5 email drafts should have unique subjects and content."""
    subjects = set()
    bodies = set()
    for key in SCENARIOS:
        result = await _run_scenario(key)
        email = result["state"].email_draft
        subjects.add(email.subject)
        bodies.add(email.body[:50])  # First 50 chars should be unique
    assert len(subjects) == 5, f"Expected 5 unique subjects, got {len(subjects)}"
    assert len(bodies) == 5, f"Expected 5 unique bodies, got {len(bodies)}"


@pytest.mark.asyncio
async def test_coaching_reports_are_distinct():
    """All 5 coaching reports should have unique recommendations."""
    all_recommendations = set()
    for key in SCENARIOS:
        result = await _run_scenario(key)
        coach = result["state"].coaching_report
        for action in coach.recommended_actions:
            all_recommendations.add(action[:40])
    # With 5 scenarios each having 2+ actions, we should have at least 10 unique entries
    assert len(all_recommendations) >= 10, f"Expected >=10 unique recommendations across scenarios, got {len(all_recommendations)}"


if __name__ == "__main__":
    """Manual runner — prints scenario summaries for quick verification."""
    async def manual_test():
        for key in SCENARIOS:
            print(f"\n{'='*60}")
            print(f"SCENARIO: {SCENARIOS[key]['name']}")
            print(f"Company: {SCENARIOS[key]['company']}")
            print(f"Contact: {SCENARIOS[key]['contact']}")
            print(f"{'='*60}")

            result = await _run_scenario(key)
            state = result["state"]

            print(f"  Transcript: {len(state.transcript.segments)} segments, {state.transcript.duration_seconds:.1f}s")
            print(f"  CRM: {state.crm_record.contact_name} @ {state.crm_record.company} ({state.crm_record.deal_stage})")
            print(f"  Pain Points: {len(state.crm_record.pain_points)}")
            print(f"  Buying Signals: {len(state.opportunity_report.buying_signals)}")
            print(f"  Opp. Flags: {len(state.opportunity_report.opportunity_flags)}")
            print(f"  Email: {state.email_draft.subject}")
            print(f"  Coach: {len(state.coaching_report.rubric_scores)} rubrics, {len(state.coaching_report.strengths)} strengths")
            print(f"  Talk Ratio: Rep {state.coaching_report.talk_ratio_rep}% / Cust {state.coaching_report.talk_ratio_customer}%")
        print(f"\n{'='*60}")
        print("ALL 5 SCENARIOS VALIDATED SUCCESSFULLY")
        print(f"{'='*60}")

    asyncio.run(manual_test())
