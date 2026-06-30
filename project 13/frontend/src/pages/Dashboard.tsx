import { useState, useEffect, useCallback, useRef } from "react";
import { useQuery, useIsFetching } from "@tanstack/react-query";

import { useAuth } from "../context/AuthContext";
import {
  getSessions,
  getPipelineStatus,
  getPipelineResult,
  updateCRMRecord,
  updateEmailDraft,
  uploadAudio,
  type CRMRecord,
  type EmailDraft,
  type PipelineResult,
  type SessionSummary,
} from "../api/client";
import { getUsers, createUser, updateUser, deleteUser, type User } from "../api/auth";

const PIPELINE_STAGES = [
  { id: "transcription", label: "Transcription", icon: "\uD83C\uDFA7" },
  { id: "crm_automation", label: "CRM Automation", icon: "\uD83D\uDCCB" },
  { id: "opportunity_spotting", label: "Opportunity Spotting", icon: "\uD83D\uDD0D" },
  { id: "email_generation", label: "Email Generation", icon: "\u2709\uFE0F" },
  { id: "sales_coach", label: "Sales Coach", icon: "\uD83C\uDFAF" },
];

type StepId = "upload" | "transcript" | "crm" | "opportunity" | "email" | "coach";

interface StepDef {
  id: StepId;
  icon: string;
  label: string;
  desc: string;
}

const STEPS: StepDef[] = [
  { id: "upload", icon: "\uD83D\uDCE4", label: "Upload Call", desc: "Upload a sales call recording (MP3/WAV)" },
  { id: "transcript", icon: "\uD83C\uDFA7", label: "Transcription", desc: "View the full call transcript with speaker labels" },
  { id: "crm", icon: "\uD83D\uDCCB", label: "CRM Data", desc: "Extracted contact and deal information" },
  { id: "opportunity", icon: "\uD83D\uDD0D", label: "Opportunities", desc: "Buying signals and upsell opportunities" },
  { id: "email", icon: "\u2709\uFE0F", label: "Email Draft", desc: "AI-generated follow-up email" },
  { id: "coach", icon: "\uD83C\uDFAF", label: "Sales Coach", desc: "Performance scoring and feedback" },
];

const CALL_TYPES: Record<string, { label: string; cssClass: string }> = {
  discovery: { label: "Discovery Call", cssClass: "discovery" },
  demo: { label: "Demo Call", cssClass: "demo" },
  negotiation: { label: "Negotiation", cssClass: "negotiation" },
  followup: { label: "Follow-up", cssClass: "followup" },
  objection: { label: "Objection Handling", cssClass: "objection" },
};

const confidenceLabel = (c: number) => {
  if (c >= 0.7) return "high";
  if (c >= 0.4) return "medium";
  return "low";
};

function ProgressBar({
  steps,
  currentStep,
  completedSteps,
  onNavigate,
}: {
  steps: StepDef[];
  currentStep: number;
  completedSteps: Set<number>;
  onNavigate: (idx: number) => void;
}) {
  return (
    <div className="progress-bar">
      {steps.map((s, i) => {
        const isCompleted = completedSteps.has(i);
        const isActive = i === currentStep;
        const isUnlocked = i <= currentStep || completedSteps.has(i - 1);
        return (
          <button
            key={s.id}
            className={`progress-step ${isActive ? "active" : ""} ${isCompleted ? "completed" : ""} ${!isUnlocked ? "locked" : ""}`}
            onClick={() => isUnlocked && onNavigate(i)}
            disabled={!isUnlocked}
            title={s.desc}
          >
            <div className="progress-indicator">
              {isCompleted ? "\u2713" : i + 1}
            </div>
            <div className="progress-label">{s.label}</div>
          </button>
        );
      })}
    </div>
  );
}

function StepUpload({
  onComplete,
  selectedCallId,
  onCallIdChange,
  onOpenSessions,
}: {
  onComplete: (callId: string) => void;
  selectedCallId: string | null;
  onCallIdChange: (id: string | null) => void;
  onOpenSessions: () => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<string>("idle");
  const [busy, setBusy] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [activeStage, setActiveStage] = useState<number>(-1);
  const [completedStages, setCompletedStages] = useState<Set<number>>(new Set());

  const handleSubmit = useCallback(async () => {
    if (!file) return;
    setBusy(true);
    setErrorMsg(null);
    setStatus("Uploading audio...");
    setActiveStage(-1);
    setCompletedStages(new Set());
    try {
      const run = await uploadAudio(file);
      setStatus("Processing pipeline...");
      onCallIdChange(run.call_id);
      let current = "running";
      let attempts = 0;
      while ((current === "running" || current === "pending") && attempts < 60) {
        await new Promise((r) => setTimeout(r, 3000));
        const ps = await getPipelineStatus(run.call_id);
        current = ps.status;
        if (ps.completed_nodes && ps.completed_nodes.length > 0) {
          setActiveStage(ps.completed_nodes.length);
          setCompletedStages(new Set(ps.completed_nodes.map((n) => PIPELINE_STAGES.findIndex((s) => s.id === n)).filter((i) => i >= 0)));
        }
        attempts++;
      }
      if (current === "complete") {
        setCompletedStages(new Set(PIPELINE_STAGES.map((_, i) => i)));
        setActiveStage(PIPELINE_STAGES.length);
        setStatus("Complete");
        onComplete(run.call_id);
      } else {
        // Fetch the result to get the error message
        try {
          const errResult = await getPipelineResult(run.call_id);
          setErrorMsg(errResult.error_message || "Pipeline processing failed.");
        } catch {
          setErrorMsg("Pipeline processing failed.");
        }
        setStatus("Failed");
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Upload failed";
      if (msg.toLowerCase().includes("does not appear to be a valid audio")) {
        setErrorMsg("The uploaded file is not a valid WAV or MP3 audio file.");
      } else {
        setErrorMsg(msg);
      }
      setStatus("Failed");
    } finally {
      setBusy(false);
    }
  }, [file, onComplete, onCallIdChange]);

  return (
    <div>
      <div className="page-header">
        <h2>Upload Call Recording</h2>
        <div className="page-subtitle">
          Select an MP3 or WAV file of a sales call (max 25 MB). The AI pipeline will process it through 5 stages.
        </div>
      </div>

      <div className="card">
        <h3>Select Audio File</h3>
        <div className="flex items-center gap-2" style={{ flexWrap: "wrap" }}>
          <div className="file-input-wrapper">
            <input
              accept=".mp3,.wav,audio/mpeg,audio/wav"
              disabled={busy}
              onChange={(e) => {
                setFile(e.target.files?.[0] || null);
                setErrorMsg(null);
              }}
              type="file"
            />
          </div>
          <button className="btn btn-primary" disabled={!file || busy} onClick={handleSubmit}>
            {busy ? (
              <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                <span className="spinner spinner-sm" /> Processing...
              </span>
            ) : (
              "Process Call"
            )}
          </button>
          {status !== "idle" && status !== "Uploading audio..." && status !== "Processing pipeline..." && (
            <span className={`status-badge ${status === "Complete" ? "complete" : "error"}`}>
              <span className="status-dot" />
              {status}
            </span>
          )}
          {busy && status === "Uploading audio..." && (
            <span className="status-badge running">
              <span className="spinner spinner-sm" style={{ marginRight: 4 }} /> Uploading...
            </span>
          )}
        </div>

        {/* Pipeline stage progress */}
        {busy && status === "Processing pipeline..." && (
          <div className="pipeline-progress">
            {PIPELINE_STAGES.map((stage, i) => {
              let stageClass = "pending";
              if (completedStages.has(i)) stageClass = "completed";
              else if (i === activeStage) stageClass = "active";
              return (
                <div key={stage.id} className={`pipeline-stage ${stageClass}`}>
                  <span className="stage-icon">
                    {completedStages.has(i) ? "\u2713" : stageClass === "active" ? <span className="spinner spinner-sm" /> : stage.icon}
                  </span>
                  <span>{stage.label}</span>
                  {stageClass === "active" && <span style={{ fontSize: 11, opacity: 0.7, marginLeft: "auto" }}>Processing...</span>}
                  {completedStages.has(i) && <span style={{ fontSize: 11, opacity: 0.7, marginLeft: "auto" }}>Done</span>}
                </div>
              );
            })}
          </div>
        )}

        {/* Error message */}
        {errorMsg && (
          <div className="error-message">
            {errorMsg}
          </div>
        )}
      </div>

      <button
        className="btn"
        onClick={onOpenSessions}
        style={{ marginTop: 8, display: "inline-flex", alignItems: "center", gap: 6 }}
      >
        {"\uD83D\uDCCB"} Browse Recent Sessions
      </button>
    </div>
  );
}

function StepTranscript({ result }: { result: PipelineResult }) {
  const transcript = result.transcript;
  return (
    <div>
      <div className="page-header">
        <h2>Call Transcription</h2>
        <div className="page-subtitle">
          Timestamped transcript with speaker labels from the sales call.
        </div>
      </div>

      {transcript && (
        <div className="stats-grid">
          <div className="stat-card">
            <div>
              <div className="stat-value">{transcript.segments.length}</div>
              <div className="stat-label">Segments</div>
            </div>
            <div className="stat-icon accent">{"\uD83D\uDCCB"}</div>
          </div>
          <div className="stat-card">
            <div>
              <div className="stat-value">{transcript.duration_seconds.toFixed(1)}s</div>
              <div className="stat-label">Duration</div>
            </div>
            <div className="stat-icon success">{"\u23F1\uFE0F"}</div>
          </div>
          <div className="stat-card">
            <div>
              <div className="stat-value">{transcript.segments.filter(s => s.speaker === "Rep").length}</div>
              <div className="stat-label">Rep Turns</div>
            </div>
            <div className="stat-icon warning">{"\uD83D\uDDE3\uFE0F"}</div>
          </div>
          <div className="stat-card">
            <div>
              <div className="stat-value">{transcript.segments.filter(s => s.speaker === "Customer").length}</div>
              <div className="stat-label">Customer Turns</div>
            </div>
            <div className="stat-icon error">{"\uD83D\uDCAC"}</div>
          </div>
        </div>
      )}

      <div className="card">
        <h3>Transcript</h3>
        {!transcript ? (
          <div className="empty-state">
            <div className="empty-icon">{"\uD83C\uDFA7"}</div>
            <p>No transcript available for this session.</p>
          </div>
        ) : (
          transcript.segments.map((seg, i) => (
            <div className="transcript-segment" key={i}>
              <div className="timestamp">
                [{seg.timestamp_start.toFixed(1)}s {"\u2013"} {seg.timestamp_end.toFixed(1)}s]
              </div>
              <div className={`speaker-label ${seg.speaker === "Rep" ? "rep" : "customer"}`}>
                {seg.speaker}
              </div>
              <div className="segment-text">{seg.text}</div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function StepCRM({ result, canEdit }: { result: PipelineResult; canEdit: boolean }) {
  const crm = result.crm_record;
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editForm, setEditForm] = useState<CRMRecord | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (crm) setEditForm({ ...crm });
  }, [crm]);

  if (!crm) {
    return (
      <div>
        <div className="page-header">
          <h2>CRM Data Extraction</h2>
          <div className="page-subtitle">Structured contact and deal information extracted from the call transcript.</div>
        </div>
        <div className="card">
          <div className="empty-state">
            <div className="empty-icon">{"\uD83D\uDCCB"}</div>
            <p>No CRM data available for this session.</p>
          </div>
        </div>
      </div>
    );
  }

  const handleSave = async () => {
    if (!editForm) return;
    setSaving(true);
    try {
      await updateCRMRecord(result.call_id, editForm);
      setSaved(true);
      setEditing(false);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      /* ignore */
    } finally {
      setSaving(false);
    }
  };

  const addPainPoint = () => {
    if (!editForm) return;
    setEditForm({ ...editForm, pain_points: [...editForm.pain_points, ""] });
  };

  const updatePainPoint = (i: number, val: string) => {
    if (!editForm) return;
    const next = [...editForm.pain_points];
    next[i] = val;
    setEditForm({ ...editForm, pain_points: next });
  };

  const removePainPoint = (i: number) => {
    if (!editForm) return;
    setEditForm({ ...editForm, pain_points: editForm.pain_points.filter((_, idx) => idx !== i) });
  };

  return (
    <div>
      <div className="page-header">
        <h2>CRM Data Extraction</h2>
        <div className="page-subtitle">Structured contact and deal information extracted from the call transcript.</div>
      </div>

      <div className="card">
        <div className="flex items-center justify-between" style={{ marginBottom: 16 }}>
          <h3 style={{ margin: 0 }}>CRM Record</h3>
          {!editing && canEdit && (
            <button className="btn btn-sm" onClick={() => setEditing(true)}>
              {"\u270F\uFE0F"} Edit
            </button>
          )}
          {saved && <span className="status-badge complete"><span className="status-dot" /> Saved</span>}
        </div>

        {editing && editForm ? (
          <div className="crm-edit-form">
            <div className="form-grid">
              <div className="form-field">
                <label className="field-label">Contact Name</label>
                <input className="input" value={editForm.contact_name} onChange={(e) => setEditForm({ ...editForm, contact_name: e.target.value })} />
              </div>
              <div className="form-field">
                <label className="field-label">Contact Email</label>
                <input className="input" value={editForm.contact_email} onChange={(e) => setEditForm({ ...editForm, contact_email: e.target.value })} />
              </div>
              <div className="form-field">
                <label className="field-label">Company</label>
                <input className="input" value={editForm.company} onChange={(e) => setEditForm({ ...editForm, company: e.target.value })} />
              </div>
              <div className="form-field">
                <label className="field-label">Deal Stage</label>
                <select className="input" value={editForm.deal_stage} onChange={(e) => setEditForm({ ...editForm, deal_stage: e.target.value })}>
                  {["Discovery", "Demo Scheduled", "Proposal", "Negotiation", "Closed Won", "Closed Lost"].map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
              <div className="form-field">
                <label className="field-label">Call Date</label>
                <input className="input" type="date" value={editForm.call_date} onChange={(e) => setEditForm({ ...editForm, call_date: e.target.value })} />
              </div>
              <div className="form-field">
                <label className="field-label">Next Steps</label>
                <textarea className="input" rows={2} value={editForm.next_steps} onChange={(e) => setEditForm({ ...editForm, next_steps: e.target.value })} />
              </div>
              <div className="form-field full-width">
                <label className="field-label">Pain Points</label>
                {editForm.pain_points.map((p, i) => (
                  <div key={i} className="pain-point-row">
                    <input className="input" value={p} onChange={(e) => updatePainPoint(i, e.target.value)} />
                    <button className="btn btn-sm btn-remove" onClick={() => removePainPoint(i)}>{"\u2715"}</button>
                  </div>
                ))}
                <button className="btn btn-sm" onClick={addPainPoint} style={{ marginTop: 4 }}>+ Add pain point</button>
              </div>
            </div>
            <div className="form-actions">
              <button className="btn" onClick={() => { setEditing(false); if (crm) setEditForm({ ...crm }); }}>Cancel</button>
              <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
                {saving ? <span className="btn-loading"><span className="spinner spinner-sm" /> Saving...</span> : "Save Changes"}
              </button>
            </div>
          </div>
        ) : (
          <div className="crm-grid">
            <div className="crm-field">
              <div className="field-label">Contact Name</div>
              <div className="field-value">{crm.contact_name}</div>
            </div>
            <div className="crm-field">
              <div className="field-label">Contact Email</div>
              <div className="field-value">{crm.contact_email || "\u2014"}</div>
            </div>
            <div className="crm-field">
              <div className="field-label">Company</div>
              <div className="field-value">{crm.company}</div>
            </div>
            <div className="crm-field">
              <div className="field-label">Deal Stage</div>
              <div className="field-value">{crm.deal_stage}</div>
            </div>
            <div className="crm-field">
              <div className="field-label">Call Date</div>
              <div className="field-value">{crm.call_date}</div>
            </div>
            <div className="crm-field">
              <div className="field-label">Next Steps</div>
              <div className="field-value">{crm.next_steps}</div>
            </div>
            <div className="crm-field full-width">
              <div className="field-label">Pain Points</div>
              {crm.pain_points.length > 0 ? (
                <div className="tag-list">
                  {crm.pain_points.map((p, i) => (
                    <span className="tag warning" key={i}>{p}</span>
                  ))}
                </div>
              ) : (
                <div className="field-value text-muted">None identified</div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function StepOpportunities({ result }: { result: PipelineResult }) {
  const report = result.opportunity_report;
  return (
    <div>
      <div className="page-header">
        <h2>Opportunity Spotting</h2>
        <div className="page-subtitle">
          Buying signals and upsell/cross-sell opportunities detected in the conversation.
        </div>
      </div>

      <div className="card">
        <h3>Buying Signals</h3>
        {!report || report.buying_signals.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">{"\uD83D\uDD0D"}</div>
            <p>No buying signals detected.</p>
          </div>
        ) : (
          report.buying_signals.map((s, i) => (
            <div className="signal-card" key={i}>
              <div className="signal-header">
                <span className={`signal-type ${confidenceLabel(s.confidence)}`}>
                  {s.signal_type.replace(/_/g, " ")}
                </span>
                <span className="text-muted" style={{ fontSize: 12 }}>
                  {(s.confidence * 100).toFixed(0)}% confidence
                </span>
              </div>
              <div className="signal-quote">{"\u201C"}{s.quote}{"\u201D"}</div>
            </div>
          ))
        )}
      </div>

      <div className="card">
        <h3>Upsell / Cross-sell Opportunities</h3>
        {!report || report.opportunity_flags.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">{"\uD83D\uDCC8"}</div>
            <p>No opportunities identified.</p>
          </div>
        ) : (
          report.opportunity_flags.map((f, i) => (
            <div className="signal-card" key={i}>
              <div className="signal-header">
                <span className={`signal-type ${confidenceLabel(f.confidence)}`}>
                  {f.opportunity_type === "upsell" ? "\u2B06\uFE0F Upsell" : "\uD83D\uDD17 Cross-sell"}
                </span>
                <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text)" }}>
                  {f.product_suggestion}
                </span>
                <span className="text-muted" style={{ fontSize: 12, marginLeft: "auto" }}>
                  {(f.confidence * 100).toFixed(0)}% confidence
                </span>
              </div>
              <div className="signal-quote">{f.evidence}</div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function StepEmail({ result, canEdit }: { result: PipelineResult; canEdit: boolean }) {
  const email = result.email_draft;
  const crm = result.crm_record;
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editForm, setEditForm] = useState<EmailDraft | null>(null);
  const [saved, setSaved] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (email) setEditForm({ ...email });
  }, [email]);

  const copyToClipboard = async () => {
    if (!email) return;
    try {
      await navigator.clipboard.writeText(`Subject: ${email.subject}\n\n${email.body}`);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch { /* ignore */ }
  };

  if (!email) {
    return (
      <div>
        <div className="page-header">
          <h2>Email Generation</h2>
          <div className="page-subtitle">AI-generated follow-up email based on the call content.</div>
        </div>
        <div className="card">
          <div className="empty-state">
            <div className="empty-icon">{"\uD83D\uDCE7"}</div>
            <p>No email draft available for this session.</p>
          </div>
        </div>
      </div>
    );
  }

  const handleSave = async () => {
    if (!editForm) return;
    setSaving(true);
    try {
      await updateEmailDraft(result.call_id, editForm);
      setSaved(true);
      setEditing(false);
      setTimeout(() => setSaved(false), 2000);
    } catch { /* ignore */ }
    finally { setSaving(false); }
  };

  return (
    <div>
      <div className="page-header">
        <h2>Email Generation</h2>
        <div className="page-subtitle">AI-generated follow-up email based on the call content.</div>
      </div>

      <div className="card">
        <div className="flex items-center justify-between" style={{ marginBottom: 16 }}>
          <h3 style={{ margin: 0 }}>Email Draft</h3>
          {!editing && canEdit && (
            <button className="btn btn-sm" onClick={() => setEditing(true)}>
              {"\u270F\uFE0F"} Edit
            </button>
          )}
          {saved && <span className="status-badge complete"><span className="status-dot" /> Saved</span>}
        </div>

        <div className="crm-field" style={{ marginBottom: 12 }}>
          <div className="field-label">Recipient</div>
          <div className="field-value">{crm?.contact_email || "No email on record"}</div>
        </div>
        <div className="crm-field" style={{ marginBottom: 12 }}>
          <div className="field-label">SMTP Status</div>
          <div className="field-value">
            {crm?.contact_email ? (
              <span className="status-badge complete"><span className="status-dot" /> SMTP configured and ready</span>
            ) : (
              <span className="text-muted">No contact email {"\u2014"} SMTP skipped</span>
            )}
          </div>
        </div>

        {editing && editForm ? (
          <div className="crm-edit-form">
            <div className="form-grid">
              <div className="form-field full-width">
                <label className="field-label">Subject</label>
                <input className="input" value={editForm.subject} onChange={(e) => setEditForm({ ...editForm, subject: e.target.value })} />
              </div>
              <div className="form-field full-width">
                <label className="field-label">Body</label>
                <textarea className="input" rows={12} value={editForm.body} onChange={(e) => setEditForm({ ...editForm, body: e.target.value })} />
              </div>
            </div>
            <div className="form-actions">
              <button className="btn" onClick={() => { setEditing(false); if (email) setEditForm({ ...email }); }}>Cancel</button>
              <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
                {saving ? <span className="btn-loading"><span className="spinner spinner-sm" /> Saving...</span> : "Save Changes"}
              </button>
            </div>
          </div>
        ) : (
          <>
            <div className="email-preview">
              <div className="email-subject">{"\uD83D\uDCE8"} {email.subject}</div>
              <div className="email-body">{email.body}</div>
            </div>
            <div className="mt-2">
              <button className="btn btn-sm" onClick={copyToClipboard}>
                {copied ? "Copied!" : "Copy to Clipboard"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function StepCoach({ result }: { result: PipelineResult }) {
  const report = result.coaching_report;
  return (
    <div>
      <div className="page-header">
        <h2>Sales Coach</h2>
        <div className="page-subtitle">
          Rubric-based performance scoring with talk ratio analysis and actionable recommendations.
        </div>
      </div>

      <div className="card">
        <h3>Rubric Scores</h3>
        {!report ? (
          <div className="empty-state">
            <div className="empty-icon">{"\uD83C\uDFAF"}</div>
            <p>No coaching report available for this session.</p>
          </div>
        ) : (
          <>
            {report.rubric_scores.map((r, i) => (
              <div key={i}>
                <div className="rubric-bar">
                  <div className="rubric-dimension">{r.dimension}</div>
                  <div className="rubric-track">
                    <div className="rubric-fill" style={{ width: `${(r.score / 10) * 100}%` }} />
                  </div>
                  <div className="rubric-score">{r.score}/10</div>
                </div>
                <div className="rubric-comment">{r.comment}</div>
              </div>
            ))}

            <h4 style={{ marginTop: 20 }}>Talk Ratio</h4>
            <div className="talk-ratio-container">
              <div className="talk-bar">
                <div className="talk-label">Rep</div>
                <div className="talk-value rep">{report.talk_ratio_rep.toFixed(1)}%</div>
              </div>
              <div className="talk-bar">
                <div className="talk-label">Customer</div>
                <div className="talk-value customer">{report.talk_ratio_customer.toFixed(1)}%</div>
              </div>
            </div>
          </>
        )}
      </div>

      {report && report.strengths.length > 0 && (
        <div className="card">
          <h3>{"\u2B50"} Strengths</h3>
          <div className="tag-list">
            {report.strengths.map((s, i) => (
              <span className="tag success" key={i}>{s}</span>
            ))}
          </div>
        </div>
      )}

      {report && report.areas_to_improve.length > 0 && (
        <div className="card">
          <h3>{"\uD83D\uDCD8"} Areas to Improve</h3>
          <div className="tag-list">
            {report.areas_to_improve.map((a, i) => (
              <span className="tag warning" key={i}>{a}</span>
            ))}
          </div>
        </div>
      )}

      {report && report.recommended_actions.length > 0 && (
        <div className="card">
          <h3>{"\uD83D\uDE80"} Recommended Actions</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {report.recommended_actions.map((a, i) => (
              <div className="step" key={i} style={{ gap: 10 }}>
                <div className="step-number" style={{ width: 22, height: 22, fontSize: 11 }}>{i + 1}</div>
                <div className="step-content">
                  <span style={{ fontSize: 13, color: "var(--text)" }}>{a}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="loading-skeleton-container">
      <div className="page-header">
        <div className="skeleton skeleton-text short" style={{ height: 28, width: 200 }} />
        <div className="skeleton skeleton-text" style={{ height: 14, width: 320, marginTop: 6 }} />
      </div>
      <div className="stats-grid" style={{ marginBottom: 16 }}>
        {[1, 2, 3, 4].map((i) => (
          <div className="skeleton skeleton-card" key={i} style={{ height: 72 }} />
        ))}
      </div>
      <div className="card">
        <div className="skeleton skeleton-text short" style={{ height: 20, width: 120, marginBottom: 16 }} />
        {[1, 2, 3].map((i) => (
          <div key={i} style={{ marginBottom: 16 }}>
            <div className="skeleton skeleton-text" style={{ height: 12, width: 140, marginBottom: 4 }} />
            <div className="skeleton skeleton-text" style={{ height: 14, width: "90%" }} />
            <div className="skeleton skeleton-text" style={{ height: 14, width: "70%", marginTop: 2 }} />
          </div>
        ))}
      </div>
    </div>
  );
}

function StepLoadingSkeleton({ step }: { step: number }) {
  const labels: Record<number, { title: string; subtitle: string; statCount: number; rows: number }> = {
    1: { title: "Call Transcription", subtitle: "Timestamped transcript with speaker labels from the sales call.", statCount: 4, rows: 5 },
    2: { title: "CRM Data Extraction", subtitle: "Structured contact and deal information extracted from the call transcript.", statCount: 0, rows: 6 },
    3: { title: "Opportunity Spotting", subtitle: "Buying signals and upsell/cross-sell opportunities detected in the conversation.", statCount: 0, rows: 3 },
    4: { title: "Email Generation", subtitle: "AI-generated follow-up email based on the call content.", statCount: 0, rows: 0 },
    5: { title: "Sales Coach", subtitle: "Rubric-based performance scoring with talk ratio analysis and actionable recommendations.", statCount: 0, rows: 5 },
  };
  const cfg = labels[step] || labels[1];

  return (
    <div className="loading-skeleton-container">
      <div className="page-header">
        <h2 style={{ opacity: 0.3 }}>{cfg.title}</h2>
        <div className="page-subtitle" style={{ opacity: 0.3 }}>{cfg.subtitle}</div>
      </div>

      {cfg.statCount > 0 && (
        <div className="stats-grid" style={{ marginBottom: 24 }}>
          {Array.from({ length: cfg.statCount }).map((_, i) => (
            <div className="stat-card" key={i} style={{ background: "var(--bg)", border: "1px dashed var(--border)" }}>
              <div style={{ flex: 1 }}>
                <div className="skeleton" style={{ height: 32, width: 60, marginBottom: 6 }} />
                <div className="skeleton" style={{ height: 12, width: 80 }} />
              </div>
              <div className="skeleton" style={{ width: 48, height: 48, borderRadius: 12, flexShrink: 0 }} />
            </div>
          ))}
        </div>
      )}

      <div className="card">
        <h3 style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span className="spinner" /> Loading...
        </h3>
        {Array.from({ length: cfg.rows || 3 }).map((_, i) => (
          <div key={i} style={{ marginBottom: 14, opacity: 0.5 }}>
            {step === 1 && (
              <>
                <div className="skeleton" style={{ height: 11, width: 120, marginBottom: 4 }} />
                <div className="skeleton" style={{ height: 11, width: 50, marginBottom: 6 }} />
                <div className="skeleton" style={{ height: 14, width: `${85 - i * 8}%` }} />
              </>
            )}
            {step === 2 && (
              <>
                <div className="skeleton" style={{ height: 10, width: 100, marginBottom: 6 }} />
                <div className="skeleton" style={{ height: 16, width: "60%" }} />
              </>
            )}
            {step === 3 && (
              <>
                <div className="skeleton" style={{ height: 12, width: 100, marginBottom: 6, borderRadius: 4 }} />
                <div className="skeleton" style={{ height: 14, width: "80%" }} />
              </>
            )}
            {step === 4 && (
              <>
                <div className="skeleton" style={{ height: 14, width: "90%", marginBottom: 6 }} />
                <div className="skeleton" style={{ height: 14, width: "70%" }} />
              </>
            )}
            {step === 5 && (
              <>
                <div className="skeleton" style={{ height: 10, width: 140, marginBottom: 4 }} />
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <div className="skeleton" style={{ flex: 1, height: 10 }} />
                  <div className="skeleton" style={{ height: 14, width: 36 }} />
                </div>
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function SessionsPanel({
  open,
  onClose,
  sessions,
  sessionsLoading,
  selectedCallId,
  onSelect,
}: {
  open: boolean;
  onClose: () => void;
  sessions: SessionSummary[] | undefined;
  sessionsLoading: boolean;
  selectedCallId: string | null;
  onSelect: (s: { call_id: string; status: string }) => void;
}) {
  const [search, setSearch] = useState("");

  const filtered = (sessions || []).filter((s) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      (s.contact_name || "").toLowerCase().includes(q) ||
      (s.company || "").toLowerCase().includes(q) ||
      (s.deal_stage || "").toLowerCase().includes(q)
    );
  });

  const completeSessions = filtered.filter((s) => s.status === "complete");
  const otherSessions = filtered.filter((s) => s.status !== "complete");

  if (!open) return null;

  return (
    <>
      <style>{`
        .sessions-search:focus {
          border-color: var(--accent) !important;
          box-shadow: 0 0 0 3px rgba(124,58,237,0.1);
        }
        @keyframes sessions-slide-in {
          from { transform: translateX(100%); }
          to { transform: translateX(0); }
        }
      `}</style>
      <div
        style={{
          position: "fixed",
          inset: 0,
          background: "rgba(0,0,0,0.25)",
          zIndex: 200,
          transition: "opacity 0.2s",
        }}
        onClick={onClose}
      />
      <div
        style={{
          position: "fixed",
          top: 0,
          right: 0,
          bottom: 0,
          width: 380,
          maxWidth: "90vw",
          background: "var(--bg)",
          borderLeft: "1px solid var(--border)",
          zIndex: 201,
          display: "flex",
          flexDirection: "column",
          boxShadow: "-8px 0 30px rgba(0,0,0,0.12)",
          animation: "sessions-slide-in 0.25s ease-out",
        }}
      >
        <div style={{
          padding: "20px 20px 16px",
          borderBottom: "1px solid var(--border)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}>
          <div>
            <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: "var(--text)" }}>Recent Sessions</h3>
            <p style={{ margin: "4px 0 0", fontSize: 12, color: "var(--text-muted)" }}>
              {sessions ? `${sessions.length} session${sessions.length !== 1 ? "s" : ""}` : "Loading..."}
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: "none",
              border: "1px solid var(--border)",
              borderRadius: 6,
              width: 32,
              height: 32,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
              color: "var(--text-muted)",
              fontSize: 16,
            }}
          >
            {"\u2715"}
          </button>
        </div>

        <div style={{ padding: "12px 20px" }}>
          <input
            type="text"
            placeholder="Search by name, company, or stage..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="sessions-search"
            style={{
              width: "100%",
              padding: "10px 12px",
              border: "1px solid var(--border)",
              borderRadius: 8,
              background: "var(--bg)",
              color: "var(--text)",
              fontSize: 13,
              outline: "none",
              fontFamily: "var(--font-sans)",
              boxSizing: "border-box",
            }}
          />
        </div>

        <div style={{ flex: 1, overflowY: "auto", padding: "0 20px 20px" }}>
          {sessionsLoading && !sessions ? (
            <div className="empty-state" style={{ padding: "40px 20px" }}>
              <span className="spinner spinner-lg" />
              <p>Loading sessions...</p>
            </div>
          ) : filtered.length === 0 ? (
            <div className="empty-state" style={{ padding: "40px 20px" }}>
              <div className="empty-icon">{"\uD83C\uDFA7"}</div>
              <p>{search ? "No matching sessions found." : "No sessions yet. Upload a call to get started."}</p>
            </div>
          ) : (
            <>
              {completeSessions.length > 0 && (
                <div style={{ marginBottom: 16 }}>
                  <div style={{
                    fontSize: 11,
                    textTransform: "uppercase",
                    letterSpacing: "0.06em",
                    fontWeight: 600,
                    color: "var(--text-muted)",
                    marginBottom: 8,
                  }}>
                    Completed ({completeSessions.length})
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    {completeSessions.map((s) => (
                      <button
                        key={s.call_id}
                        onClick={() => {
                          onSelect(s);
                          onClose();
                        }}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 12,
                          width: "100%",
                          textAlign: "left",
                          padding: "12px 14px",
                          border: selectedCallId === s.call_id ? "1.5px solid var(--accent)" : "1px solid var(--border)",
                          borderRadius: 8,
                          background: selectedCallId === s.call_id ? "var(--accent-light)" : "var(--bg-card)",
                          cursor: "pointer",
                          fontFamily: "var(--font-sans)",
                        }}
                      >
                        <div style={{
                          width: 36,
                          height: 36,
                          borderRadius: "50%",
                          background: "var(--accent-light)",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          fontSize: 14,
                          fontWeight: 700,
                          color: "var(--accent)",
                          flexShrink: 0,
                        }}>
                          {(s.contact_name || "U").charAt(0).toUpperCase()}
                        </div>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{
                            fontSize: 13,
                            fontWeight: 600,
                            color: selectedCallId === s.call_id ? "var(--accent)" : "var(--text)",
                            whiteSpace: "nowrap",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                          }}>
                            {s.contact_name || "Unknown Contact"}
                          </div>
                          <div style={{
                            fontSize: 11,
                            color: "var(--text-muted)",
                            marginTop: 2,
                            whiteSpace: "nowrap",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                          }}>
                            {s.company || "Unknown Company"} {"\u00B7 "} {s.deal_stage || "No stage"}
                          </div>
                        </div>
                        <span
                          className="status-badge complete"
                          style={{ flexShrink: 0, fontSize: 10 }}
                        >
                          <span className="status-dot" />
                          Done
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {otherSessions.length > 0 && (
                <div>
                  <div style={{
                    fontSize: 11,
                    textTransform: "uppercase",
                    letterSpacing: "0.06em",
                    fontWeight: 600,
                    color: "var(--text-muted)",
                    marginBottom: 8,
                  }}>
                    In Progress ({otherSessions.length})
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    {otherSessions.map((s) => (
                      <button
                        key={s.call_id}
                        onClick={() => {
                          onSelect(s);
                          onClose();
                        }}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 12,
                          width: "100%",
                          textAlign: "left",
                          padding: "12px 14px",
                          border: selectedCallId === s.call_id ? "1.5px solid var(--accent)" : "1px solid var(--border)",
                          borderRadius: 8,
                          background: selectedCallId === s.call_id ? "var(--accent-light)" : "var(--bg-card)",
                          cursor: "pointer",
                          fontFamily: "var(--font-sans)",
                        }}
                      >
                        <div style={{
                          width: 36,
                          height: 36,
                          borderRadius: "50%",
                          background: s.status === "error" ? "rgba(239,68,68,0.1)" : "rgba(245,158,11,0.1)",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          fontSize: 14,
                          flexShrink: 0,
                        }}>
                          {s.status === "error" ? "\u2717" : <span className="spinner spinner-sm" />}
                        </div>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{
                            fontSize: 13,
                            fontWeight: 600,
                            color: selectedCallId === s.call_id ? "var(--accent)" : "var(--text)",
                            whiteSpace: "nowrap",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                          }}>
                            {s.contact_name || "Unknown Contact"}
                          </div>
                          <div style={{
                            fontSize: 11,
                            color: "var(--text-muted)",
                            marginTop: 2,
                          }}>
                            {s.company || "Unknown Company"}
                          </div>
                        </div>
                        <span
                          className={`status-badge ${s.status === "error" ? "error" : "running"}`}
                          style={{ flexShrink: 0, fontSize: 10 }}
                        >
                          <span className="status-dot" />
                          {s.status}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
}

function UsersPanel({
  open,
  onClose,
  users,
  isLoading,
  token,
  canManageUsers,
  onUsersChanged,
}: {
  open: boolean;
  onClose: () => void;
  users: User[] | undefined;
  isLoading: boolean;
  token: string | null;
  canManageUsers: boolean;
  onUsersChanged: () => void;
}) {
  const [search, setSearch] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [editUserId, setEditUserId] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("rep");
  const [editRole, setEditRole] = useState("");
  const [saving, setSaving] = useState(false);

  if (!open) return null;

  const filtered = !users ? [] : users.filter((u) => {
    const q = search.toLowerCase();
    return u.name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q) || u.role.includes(q);
  });

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!token || !name || !email || !password) return;
    setSaving(true);
    try {
      await createUser(token, { name, email, password, role });
      setName(""); setEmail(""); setPassword(""); setRole("rep");
      setShowAdd(false);
      onUsersChanged();
    } catch (err) {
      console.error("Failed to create user", err);
    } finally {
      setSaving(false);
    }
  }

  async function handleRoleSave(userId: string) {
    if (!token || !editRole) return;
    setSaving(true);
    try {
      await updateUser(token, userId, { role: editRole });
      setEditUserId(null);
      setEditRole("");
      onUsersChanged();
    } catch (err) {
      console.error("Failed to update user", err);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(userId: string) {
    if (!token) return;
    setSaving(true);
    try {
      await deleteUser(token, userId);
      setDeleteConfirm(null);
      onUsersChanged();
    } catch (err) {
      console.error("Failed to delete user", err);
    } finally {
      setSaving(false);
    }
  }

  function roleBadgeStyle(r: string) {
    const isAdmin = r === "admin";
    const isMgr = r === "manager";
    return {
      display: "inline-block" as const,
      padding: "2px 8px",
      borderRadius: 4,
      background: isAdmin ? "var(--accent-light)" : isMgr ? "rgba(245,158,11,0.1)" : "rgba(16,185,129,0.1)",
      color: isAdmin ? "var(--accent)" : isMgr ? "#f59e0b" : "#10b981",
      fontSize: 10,
      fontWeight: 600,
      textTransform: "uppercase" as const,
      flexShrink: 0,
    };
  }

  function avatarStyle(r: string) {
    const isAdmin = r === "admin";
    const isMgr = r === "manager";
    return {
      width: 36,
      height: 36,
      borderRadius: "50%",
      background: isAdmin ? "var(--accent-light)" : isMgr ? "rgba(245,158,11,0.1)" : "rgba(16,185,129,0.1)",
      display: "flex",
      alignItems: "center" as const,
      justifyContent: "center" as const,
      fontSize: 14,
      fontWeight: 700,
      color: isAdmin ? "var(--accent)" : isMgr ? "#f59e0b" : "#10b981",
      flexShrink: 0,
    };
  }

  return (
    <>
      <div className="panel-overlay" onClick={onClose} />
      <div className="panel-container">
        <div className="panel-header">
          <div>
            <h3 className="panel-title">User Management</h3>
            <p className="panel-subtitle">
              {users ? `${users.length} user${users.length !== 1 ? "s" : ""}` : "Loading..."}
            </p>
          </div>
          <button className="panel-close-btn" onClick={onClose}>{"\u2715"}</button>
        </div>

        <div style={{ padding: "12px 20px", display: "flex", gap: 8 }}>
          <div style={{ flex: 1, position: "relative" }}>
            <input
              className="field-input"
              type="text"
              placeholder="Search users..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ paddingLeft: 32, fontSize: 13 }}
            />
            <span style={{
              position: "absolute", left: 10, top: 8, fontSize: 13, color: "var(--text-muted)",
              pointerEvents: "none",
            }}>{"\uD83D\uDD0D"}</span>
          </div>
          {canManageUsers && !showAdd && (
            <button
              className="action-btn"
              onClick={() => setShowAdd(true)}
              title="Add user"
            >
              + Add
            </button>
          )}
        </div>

        {canManageUsers && showAdd && (
          <form
            onSubmit={handleAdd}
            style={{
              margin: "0 20px 12px",
              padding: 16,
              border: "1px solid var(--accent)",
              borderRadius: 8,
              background: "var(--bg-card)",
              display: "flex",
              flexDirection: "column",
              gap: 8,
            }}
          >
            <div style={{ fontSize: 13, fontWeight: 700, color: "var(--accent)", marginBottom: 4 }}>
              New User
            </div>
            <input className="field-input" type="text" placeholder="Name" value={name}
              onChange={(e) => setName(e.target.value)} required style={{ fontSize: 13 }} />
            <input className="field-input" type="email" placeholder="Email" value={email}
              onChange={(e) => setEmail(e.target.value)} required style={{ fontSize: 13 }} />
            <input className="field-input" type="password" placeholder="Password" value={password}
              onChange={(e) => setPassword(e.target.value)} required style={{ fontSize: 13 }} />
            <select className="field-input" value={role}
              onChange={(e) => setRole(e.target.value)} style={{ fontSize: 13 }}>
              <option value="rep">Rep</option>
              <option value="manager">Manager</option>
              <option value="admin">Admin</option>
            </select>
            <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
              <button type="button" className="btn-secondary" onClick={() => {
                setShowAdd(false); setName(""); setEmail(""); setPassword(""); setRole("rep");
              }} style={{ fontSize: 12, padding: "6px 12px" }}>Cancel</button>
              <button type="submit" className="btn-primary" disabled={saving}
                style={{ fontSize: 12, padding: "6px 12px" }}>
                {saving ? "Creating..." : "Create"}
              </button>
            </div>
          </form>
        )}

        <div className="panel-body">
          {isLoading ? (
            <div className="empty-state" style={{ padding: "40px 20px" }}>
              <span className="spinner spinner-lg" />
              <p>Loading users...</p>
            </div>
          ) : filtered.length === 0 ? (
            <div className="empty-state" style={{ padding: "40px 20px" }}>
              <div className="empty-icon">{"\uD83D\uDC64"}</div>
              <p>{search ? "No users match your search." : "No users found."}</p>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {filtered.map((u) => (
                <div key={u.id} className="user-row">
                  <div style={avatarStyle(u.role)}>
                    {u.name.charAt(0).toUpperCase()}
                  </div>

                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                      {u.name}
                      {deleteConfirm === u.id && (
                        <span style={{ marginLeft: 10, fontSize: 11, color: "#ef4444", fontWeight: 500 }}>
                          Delete this user?
                        </span>
                      )}
                    </div>
                    <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
                      {u.email}
                    </div>
                  </div>

                  {editUserId === u.id ? (
                    <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
                      <select
                        className="field-input"
                        value={editRole}
                        onChange={(e) => setEditRole(e.target.value)}
                        style={{ fontSize: 11, padding: "2px 4px", width: 80, height: 26 }}
                      >
                        <option value="rep">Rep</option>
                        <option value="manager">Manager</option>
                        <option value="admin">Admin</option>
                      </select>
                      <button className="btn-primary" onClick={() => handleRoleSave(u.id)}
                        disabled={saving} style={{ fontSize: 10, padding: "2px 8px", height: 26 }}>
                        {saving ? "..." : "Save"}
                      </button>
                      <button className="btn-secondary" onClick={() => { setEditUserId(null); setEditRole(""); }}
                        style={{ fontSize: 10, padding: "2px 8px", height: 26 }}>
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <>
                      <span style={roleBadgeStyle(u.role)}>{u.role}</span>
                      {canManageUsers && (
                        <div style={{ display: "flex", gap: 4 }}>
                          <button
                            className="btn-icon-sm"
                            onClick={() => { setEditUserId(u.id); setEditRole(u.role); setDeleteConfirm(null); }}
                            title="Edit role"
                          >
                            {"\u270F\uFE0F"}
                          </button>
                          <button
                            className="btn-icon-sm btn-icon-danger"
                            onClick={() => setDeleteConfirm(u.id)}
                            title="Delete user"
                          >
                            {"\uD83D\uDDD1\uFE0F"}
                          </button>
                        </div>
                      )}
                    </>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {deleteConfirm && (
          <div className="panel-footer" style={{ justifyContent: "center", gap: 8 }}>
            <button className="btn-secondary" onClick={() => setDeleteConfirm(null)}
              style={{ fontSize: 12, padding: "6px 14px" }}>
              Cancel
            </button>
            <button className="btn-primary" onClick={() => handleDelete(deleteConfirm)}
              disabled={saving}
              style={{ fontSize: 12, padding: "6px 14px", background: "#ef4444", borderColor: "#ef4444" }}>
              {saving ? "Deleting..." : "Confirm Delete"}
            </button>
          </div>
        )}
      </div>
    </>
  );
}

export default function Dashboard() {
  const { user, token, logout, canViewUsers, canManageUsers, canEditCRM, canEditEmail } = useAuth();
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());
  const [selectedCallId, setSelectedCallId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sessionsOpen, setSessionsOpen] = useState(false);
  const [usersOpen, setUsersOpen] = useState(false);
  const [stepTransition, setStepTransition] = useState(false);
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    const stored = localStorage.getItem("theme");
    if (stored === "light" || stored === "dark") return stored;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });
  const mainRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  const totalFetching = useIsFetching();
  const resultQuery = useQuery({
    queryKey: ["pipeline-result", selectedCallId],
    queryFn: () => getPipelineResult(selectedCallId as string),
    enabled: Boolean(selectedCallId),
  });

  const result = resultQuery.data;

  const isDataMissing = currentStep > 0 && result && !result.error_message && (
    (currentStep === 1 && !result.transcript) ||
    (currentStep === 2 && !result.crm_record) ||
    (currentStep === 3 && !result.opportunity_report) ||
    (currentStep === 4 && !result.email_draft) ||
    (currentStep === 5 && !result.coaching_report)
  );

  const { data: sessions, isLoading: sessionsLoading } = useQuery({
    queryKey: ["sessions"],
    queryFn: getSessions,
    refetchInterval: 5000,
  });

  const [sessionSearch, setSessionSearch] = useState("");

  const usersQuery = useQuery({
    queryKey: ["users"],
    queryFn: () => getUsers(token!),
    enabled: Boolean(usersOpen && token && canManageUsers),
  });

  useEffect(() => {
    if (currentStep > 0 && selectedCallId) {
      setStepTransition(true);
      const timer = setTimeout(() => setStepTransition(false), 400);
      return () => clearTimeout(timer);
    }
  }, [currentStep, selectedCallId]);

  const handleStepComplete = useCallback((callId: string) => {
    setSelectedCallId(callId);
    setCompletedSteps((prev) => {
      const next = new Set(prev);
      next.add(0);
      return next;
    });
    setCurrentStep(1);
    if (mainRef.current) mainRef.current.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  const goNext = useCallback(() => {
    if (currentStep < STEPS.length - 1) {
      setCompletedSteps((prev) => {
        const next = new Set(prev);
        next.add(currentStep);
        return next;
      });
      setCurrentStep((prev) => prev + 1);
      if (mainRef.current) mainRef.current.scrollTo({ top: 0, behavior: "smooth" });
    }
  }, [currentStep]);

  const goBack = useCallback(() => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
      if (mainRef.current) mainRef.current.scrollTo({ top: 0, behavior: "smooth" });
    }
  }, [currentStep]);

  const navigateToStep = useCallback(
    (idx: number) => {
      if (idx <= currentStep || completedSteps.has(idx - 1)) {
        setCurrentStep(idx);
        if (mainRef.current) mainRef.current.scrollTo({ top: 0, behavior: "smooth" });
      }
    },
    [currentStep, completedSteps]
  );

  const handleReset = useCallback(() => {
    setCurrentStep(0);
    setCompletedSteps(new Set());
    setSelectedCallId(null);
  }, []);

  const toggleTheme = () => setTheme((t) => (t === "light" ? "dark" : "light"));

  const isLastStep = currentStep === STEPS.length - 1;

  const getStepCallType = (): string | null => {
    const crm = result?.crm_record;
    if (!crm) return null;
    const stage = (crm.deal_stage || "").toLowerCase();
    if (stage.includes("discovery")) return "discovery";
    if (stage.includes("demo") || stage.includes("proposal")) return "demo";
    if (stage.includes("negotiation") || stage.includes("closing")) return "negotiation";
    if (stage.includes("follow") || stage.includes("review")) return "followup";
    return "objection";
  };

  const callType = getStepCallType();
  const callTypeMeta = callType ? CALL_TYPES[callType] : null;

  return (
    <div className="app-shell">
      {sidebarOpen && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.3)",
            zIndex: 99,
          }}
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside className={`sidebar ${sidebarOpen ? "open" : ""}`}>
        <div className="sidebar-header">
          <h1>Sales Rep Assistant</h1>
          <div className="subtitle" style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 4 }}>
            <span style={{
              display: "inline-block", padding: "1px 8px", borderRadius: 4,
              background: user?.role === "admin" ? "#7c3aed" : user?.role === "manager" ? "#f59e0b" : "#10b981",
              color: "#fff", fontSize: 10, fontWeight: 600, textTransform: "uppercase",
            }}>
              {user?.role}
            </span>
            <span>{user?.name}</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section-label">Pipeline Steps</div>
          {STEPS.map((s, i) => {
            const isCompleted = completedSteps.has(i);
            const isActive = i === currentStep;
            const isUnlocked = i === 0 || completedSteps.has(i - 1);
            return (
              <button
                key={s.id}
                className={`nav-item ${isActive ? "active" : ""}`}
                onClick={() => {
                  if (isUnlocked) {
                    navigateToStep(i);
                    setSidebarOpen(false);
                  }
                }}
                style={{ opacity: isUnlocked ? 1 : 0.4, cursor: isUnlocked ? "pointer" : "not-allowed" }}
                disabled={!isUnlocked}
              >
                <span className="nav-icon">
                  {isCompleted ? "\u2713" : s.icon}
                </span>
                {s.label}
                {isCompleted && <span className="nav-badge">Done</span>}
              </button>
            );
          })}
          <div className="nav-section-label" style={{ marginTop: 16 }}>Sessions</div>
          <button
            className="nav-item"
            onClick={() => {
              setSessionsOpen(true);
              setSidebarOpen(false);
            }}
          >
            <span className="nav-icon">{"\uD83D\uDCCB"}</span>
            Recent Sessions
            {sessions && sessions.length > 0 && (
              <span className="nav-badge">{sessions.length}</span>
            )}
          </button>
          {canViewUsers && (
            <button
              className="nav-item"
              onClick={() => {
                setUsersOpen(true);
                setSidebarOpen(false);
              }}
            >
              <span className="nav-icon">{"\uD83D\uDC64"}</span>
              Manage Users
            </button>
          )}
        </nav>

        <div className="sidebar-footer" style={{ flexDirection: "column", gap: 8 }}>
          <button className="theme-toggle" onClick={toggleTheme} style={{ justifyContent: "center" }}>
            {theme === "light" ? "\uD83C\uDF19" : "\u2600\uFE0F"} {theme === "light" ? "Dark Mode" : "Light Mode"}
          </button>
          <button className="theme-toggle" onClick={logout} style={{ justifyContent: "center", opacity: 0.8 }}>
            {"\uD83D\uDC4B"} Sign Out
          </button>
        </div>
      </aside>

      <main className="main" ref={mainRef}>
        {/* Global API activity bar */}
        {totalFetching > 0 && (
          <div style={{
            height: 2,
            background: "var(--bg-secondary)",
            position: "sticky", top: 0, zIndex: 10,
          }}>
            <div style={{
              height: "100%",
              width: `${Math.min(totalFetching * 20, 100)}%`,
              background: "linear-gradient(90deg, var(--accent), var(--success))",
              transition: "width 0.3s",
              borderRadius: "0 2px 2px 0",
            }} />
          </div>
        )}
        {/* Mobile hamburger */}
        <div style={{ display: "none" }} className="mobile-header">
          <button
            onClick={() => setSidebarOpen(true)}
            style={{
              background: "none",
              border: "none",
              fontSize: 24,
              cursor: "pointer",
              color: "var(--text)",
              padding: 4,
            }}
          >
            {"\u2630"}
          </button>
        </div>

        <ProgressBar
          steps={STEPS}
          currentStep={currentStep}
          completedSteps={completedSteps}
          onNavigate={navigateToStep}
        />

        {/* Call type badge */}
        {callTypeMeta && currentStep > 0 && (
          <div style={{ marginBottom: 8 }}>
            <span className={`call-type-badge ${callTypeMeta.cssClass}`}>
              {callTypeMeta.label}
            </span>
          </div>
        )}

        <div className="step-content-area">
          {currentStep === 0 && (
            <StepUpload
              onComplete={handleStepComplete}
              selectedCallId={selectedCallId}
              onCallIdChange={setSelectedCallId}
              onOpenSessions={() => setSessionsOpen(true)}
            />
          )}
          {currentStep > 0 && !selectedCallId && (
            <div className="card">
              <div className="empty-state">
                <div className="empty-icon">{"\uD83D\uDCE4"}</div>
                <p>Select a call session from the Upload step to view its results.</p>
              </div>
            </div>
          )}
          {currentStep > 0 && selectedCallId && (resultQuery.isFetching || stepTransition || isDataMissing) && (
            <StepLoadingSkeleton step={currentStep} />
          )}
          {currentStep > 0 && selectedCallId && !result && !resultQuery.isFetching && !stepTransition && !resultQuery.isError && (
            <div className="card">
              <div className="empty-state">
                <div className="empty-icon">{"\u23F3"}</div>
                <p>Loading pipeline result...</p>
              </div>
            </div>
          )}
          {currentStep > 0 && selectedCallId && result && result.error_message && (
            <div className="card">
              <div className="error-message">{result.error_message}</div>
            </div>
          )}
          {currentStep === 1 && result && !result.error_message && !stepTransition && !isDataMissing && <StepTranscript result={result} />}
          {currentStep === 2 && result && !result.error_message && !stepTransition && !isDataMissing && <StepCRM result={result} canEdit={canEditCRM} />}
          {currentStep === 3 && result && !result.error_message && !stepTransition && !isDataMissing && <StepOpportunities result={result} />}
          {currentStep === 4 && result && !result.error_message && !stepTransition && !isDataMissing && <StepEmail result={result} canEdit={canEditEmail} />}
          {currentStep === 5 && result && !result.error_message && !stepTransition && !isDataMissing && <StepCoach result={result} />}
          {resultQuery.isError && currentStep > 0 && selectedCallId && !result && (
            <div className="card">
              <div className="error-message">
                Failed to load pipeline result. The session may have been deleted or the server is unavailable.
              </div>
            </div>
          )}
        </div>

        <div className="step-navigation">
          {currentStep > 0 && (
            <button className="btn" onClick={goBack}>
              {"\u2190"} Back
            </button>
          )}
          <div style={{ flex: 1 }} />
          {resultQuery.isLoading && currentStep > 0 && !result && (
            <span className="status-badge running">
              <span className="status-dot" /> Loading results...
            </span>
          )}
          {!isLastStep && currentStep > 0 && result && (
            <button className="btn btn-primary" onClick={goNext}>
              Next {"\u2192"}
            </button>
          )}
          {isLastStep && result && (
            <button className="btn btn-primary" onClick={handleReset}>
              Start New Call
            </button>
          )}
          {currentStep > 0 && !result && !resultQuery.isLoading && (
            <span className="status-badge idle">
              <span className="status-dot" /> No data for this session
            </span>
          )}
        </div>
      </main>

      {/* Mobile responsive style injection */}
      <style>{`
        @media (max-width: 768px) {
          .mobile-header {
            display: flex !important;
            align-items: center;
            margin-bottom: 16px;
          }
        }
      `}</style>

      <SessionsPanel
        open={sessionsOpen}
        onClose={() => setSessionsOpen(false)}
        sessions={sessions}
        sessionsLoading={sessionsLoading}
        selectedCallId={selectedCallId}
        onSelect={(s) => {
          setSelectedCallId(s.call_id);
          if (s.status === "complete") {
            const idx = currentStep === 0 ? 1 : currentStep;
            setCurrentStep(idx);
            setCompletedSteps((prev) => {
              const next = new Set(prev);
              next.add(0);
              return next;
            });
          }
        }}
      />
      <UsersPanel
        open={usersOpen}
        onClose={() => setUsersOpen(false)}
        users={usersQuery.data}
        isLoading={usersQuery.isLoading}
        token={token}
        canManageUsers={canManageUsers}
        onUsersChanged={() => usersQuery.refetch()}
      />
    </div>
  );
}
