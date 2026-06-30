from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class TranscriptSegment(BaseModel):
    speaker: Literal["Rep", "Customer"]
    timestamp_start: float = Field(ge=0)
    timestamp_end: float = Field(ge=0)
    text: str


class TranscriptOutput(BaseModel):
    call_id: str
    audio_file_name: str
    duration_seconds: float = Field(ge=0)
    segments: list[TranscriptSegment]
    full_text: str


class CRMRecord(BaseModel):
    contact_name: str
    contact_email: str = ""
    company: str
    deal_stage: str
    pain_points: list[str]
    next_steps: str
    call_date: str


class BuyingSignal(BaseModel):
    quote: str
    signal_type: str
    confidence: float = Field(ge=0.0, le=1.0)


class OpportunityFlag(BaseModel):
    opportunity_type: Literal["upsell", "cross-sell"]
    product_suggestion: str
    evidence: str
    confidence: float = Field(ge=0.0, le=1.0)


class OpportunityReport(BaseModel):
    buying_signals: list[BuyingSignal]
    opportunity_flags: list[OpportunityFlag]


class EmailDraft(BaseModel):
    subject: str
    body: str


class RubricScore(BaseModel):
    dimension: str
    score: int = Field(ge=1, le=10)
    comment: str


class CoachingReport(BaseModel):
    rubric_scores: list[RubricScore] = Field(min_length=5, max_length=5)
    talk_ratio_rep: float = Field(ge=0.0, le=100.0)
    talk_ratio_customer: float = Field(ge=0.0, le=100.0)
    strengths: list[str]
    areas_to_improve: list[str]
    recommended_actions: list[str]


class PipelineState(BaseModel):
    call_id: str
    audio_file_path: str
    transcript: TranscriptOutput | None = None
    crm_record: CRMRecord | None = None
    opportunity_report: OpportunityReport | None = None
    email_draft: EmailDraft | None = None
    coaching_report: CoachingReport | None = None
    status: str = "pending"
    error_message: str | None = None


class SMTPConfig(BaseModel):
    host: str = "smtp.gmail.com"
    port: int = 587
    username: str = ""
    password: str = ""
    from_email: str = ""


class PipelineRunResponse(BaseModel):
    call_id: str
    status: str


class PipelineStatusResponse(BaseModel):
    call_id: str
    status: str
    completed_nodes: list[str] = []


class SessionSummary(BaseModel):
    call_id: str
    contact_name: str | None = None
    company: str | None = None
    deal_stage: str | None = None
    call_date: str | None = None
    status: str
