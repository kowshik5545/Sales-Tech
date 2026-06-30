"""
RBAC End-to-End test: verifies role-based access control works correctly
for all 3 roles (admin, manager, rep).

Usage:
    python scripts/test_rbac_e2e.py
"""

import io
import json
import os
import sys
import uuid
import wave

import bcrypt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
from fastapi.testclient import TestClient

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from main import app
from db.supabase_client import LOCAL_STORE, LOCAL_USERS

client = TestClient(app)

PASS = 0
FAIL = 0


def check(description: str, ok: bool):
    global PASS, FAIL
    if ok:
        print(f"  [PASS] {description}")
        PASS += 1
    else:
        print(f"  [FAIL] {description}")
        FAIL += 1


def _dummy_wav() -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(8000)
        w.writeframes(b"\x00" * 8000)
    return buf.getvalue()


def _seed_users() -> dict:
    users = {}
    for email, name, role in [
        ("admin@test.com", "Admin User", "admin"),
        ("manager@test.com", "Manager User", "manager"),
        ("rep1@test.com", "Rep One", "rep"),
        ("rep2@test.com", "Rep Two", "rep"),
    ]:
        uid = str(uuid.uuid4())
        pw_hash = bcrypt.hashpw(b"test123", bcrypt.gensalt())
        if isinstance(pw_hash, bytes):
            pw_hash = pw_hash.decode("utf-8")
        LOCAL_USERS[email] = {
            "id": uid,
            "email": email,
            "password_hash": pw_hash,
            "name": name,
            "role": role,
        }
        users[email] = {"id": uid, "email": email, "name": name, "role": role}
    return users


def _login(email: str) -> str:
    resp = client.post("/api/auth/login", json={"email": email, "password": "test123"})
    assert resp.status_code == 200, f"Login failed for {email}: {resp.status_code} {resp.text}"
    return resp.json()["token"]


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_session(owner_id: str | None = None) -> str:
    call_id = str(uuid.uuid4())
    LOCAL_STORE[call_id] = {
        "call_id": call_id,
        "audio_file_name": "test_call.wav",
        "user_id": owner_id,
        "status": "complete",
        "created_at": "2026-01-01T00:00:00Z",
        "transcript": {
            "call_id": call_id,
            "audio_file_name": "test_call.wav",
            "full_text": "Hello this is a test call",
            "segments": [
                {"speaker": "Rep", "text": "Hello", "timestamp_start": 0.0, "timestamp_end": 1.0},
                {"speaker": "Customer", "text": "Hi", "timestamp_start": 1.0, "timestamp_end": 2.0},
            ],
            "duration_seconds": 2.0,
        },
        "crm_record": {
            "call_id": call_id,
            "contact_name": "John Doe",
            "contact_email": "john@example.com",
            "company": "Acme Inc",
            "deal_stage": "Discovery",
            "pain_points": [],
            "next_steps": "Follow up next week",
            "call_date": "2026-01-01",
        },
        "opportunity_report": {"call_id": call_id, "buying_signals": [], "opportunity_flags": []},
        "email_draft": {"call_id": call_id, "subject": "Test", "body": "Test body"},
        "coaching_report": {
            "call_id": call_id,
            "rubric_scores": [
                {"dimension": "Opening", "score": 4, "comment": ""},
                {"dimension": "Discovery", "score": 3, "comment": ""},
                {"dimension": "Presentation", "score": 5, "comment": ""},
                {"dimension": "Objection", "score": 4, "comment": ""},
                {"dimension": "Closing", "score": 3, "comment": ""},
            ],
            "talk_ratio_rep": 0.5,
            "talk_ratio_customer": 0.5,
            "strengths": [],
            "areas_to_improve": [],
            "recommended_actions": [],
        },
        "error_message": None,
    }
    return call_id


def test_rbac():
    global PASS, FAIL
    print("=" * 60)
    print("RBAC End-to-End Test")
    print("=" * 60)

    # ── Setup ────────────────────────────────────────────
    print("\n[Setup] Seeding test users...")
    users = _seed_users()
    admin_token = _login("admin@test.com")
    mgr_token = _login("manager@test.com")
    rep1_token = _login("rep1@test.com")
    rep2_token = _login("rep2@test.com")
    check("All 4 users can login", True)

    # ── Test 1: Session listing ─────────────────────────
    print("\n── 1. Session listing (GET /api/sessions) ──")

    # Create test sessions: rep1 owns one, rep2 owns one, no owner
    rep1_call = _create_session(users["rep1@test.com"]["id"])
    rep2_call = _create_session(users["rep2@test.com"]["id"])
    orphan_call = _create_session(None)  # no owner (legacy)

    # Admin sees all sessions
    resp = client.get("/api/sessions", headers=_headers(admin_token))
    check("admin sees all sessions (200)", resp.status_code == 200)
    admin_ids = {s["call_id"] for s in resp.json()}
    check("admin sees rep1 session", rep1_call in admin_ids)
    check("admin sees orphan session", orphan_call in admin_ids)

    # Manager sees all sessions
    resp = client.get("/api/sessions", headers=_headers(mgr_token))
    mgr_ids = {s["call_id"] for s in resp.json()}
    check("manager sees all sessions", resp.status_code == 200 and rep1_call in mgr_ids and orphan_call in mgr_ids)

    # rep1 sees only own sessions (rep1_call)
    resp = client.get("/api/sessions", headers=_headers(rep1_token))
    rep1_ids = {s["call_id"] for s in resp.json()}
    check("rep1 sees own session", rep1_call in rep1_ids)
    check("rep1 does NOT see rep2's session", rep2_call not in rep1_ids)
    check("rep1 does NOT see orphan session", orphan_call not in rep1_ids)

    # rep2 sees only own sessions (rep2_call)
    resp = client.get("/api/sessions", headers=_headers(rep2_token))
    rep2_ids = {s["call_id"] for s in resp.json()}
    check("rep2 sees own session", rep2_call in rep2_ids)
    check("rep2 does NOT see rep1's session", rep1_call not in rep2_ids)

    # ── Test 2: View session status ─────────────────────
    print("\n── 2. Session status (GET /api/pipeline/{id}/status) ──")

    # Admin can view any session
    resp = client.get(f"/api/pipeline/{rep1_call}/status", headers=_headers(admin_token))
    check("admin can view rep's session status", resp.status_code == 200)

    # Manager can view any session
    resp = client.get(f"/api/pipeline/{rep1_call}/status", headers=_headers(mgr_token))
    check("manager can view rep's session status", resp.status_code == 200)

    # Rep can view own session
    resp = client.get(f"/api/pipeline/{rep1_call}/status", headers=_headers(rep1_token))
    check("rep can view own session status", resp.status_code == 200)

    # Rep cannot view another rep's session
    resp = client.get(f"/api/pipeline/{orphan_call}/status", headers=_headers(rep1_token))
    check("rep is DENIED another rep's session status (403)", resp.status_code == 403)

    # ── Test 3: View session result ─────────────────────
    print("\n── 3. Session result (GET /api/pipeline/{id}/result) ──")

    resp = client.get(f"/api/pipeline/{rep1_call}/result", headers=_headers(admin_token))
    check("admin can view rep's session result", resp.status_code == 200)

    resp = client.get(f"/api/pipeline/{rep1_call}/result", headers=_headers(mgr_token))
    check("manager can view rep's session result", resp.status_code == 200)

    resp = client.get(f"/api/pipeline/{rep1_call}/result", headers=_headers(rep1_token))
    check("rep can view own session result", resp.status_code == 200)

    resp = client.get(f"/api/pipeline/{orphan_call}/result", headers=_headers(rep1_token))
    check("rep is DENIED another rep's session result (403)", resp.status_code == 403)

    # ── Test 4: Edit CRM record ─────────────────────────
    print("\n── 4. Edit CRM (PATCH /api/pipeline/{id}/crm) ──")

    crm_payload = {
        "contact_name": "Updated Name",
        "contact_email": "updated@example.com",
        "company": "Updated Corp",
        "deal_stage": "Negotiation",
        "pain_points": [],
        "next_steps": "Close deal",
        "call_date": "2026-01-15",
    }

    # Admin can edit CRM
    resp = client.patch(f"/api/pipeline/{rep1_call}/crm", json=crm_payload, headers=_headers(admin_token))
    check("admin can edit CRM (200)", resp.status_code == 200)

    # Manager can edit CRM
    resp = client.patch(f"/api/pipeline/{rep1_call}/crm", json=crm_payload, headers=_headers(mgr_token))
    check("manager can edit CRM (200)", resp.status_code == 200)

    # Rep cannot edit CRM (even own session)
    resp = client.patch(f"/api/pipeline/{rep1_call}/crm", json=crm_payload, headers=_headers(rep1_token))
    check("rep is DENIED CRM edit (403)", resp.status_code == 403)

    # ── Test 5: Edit Email draft ────────────────────────
    print("\n── 5. Edit Email (PATCH /api/pipeline/{id}/email) ──")

    email_payload = {"subject": "Updated Subject", "body": "Updated body"}

    resp = client.patch(f"/api/pipeline/{rep1_call}/email", json=email_payload, headers=_headers(admin_token))
    check("admin can edit email (200)", resp.status_code == 200)

    resp = client.patch(f"/api/pipeline/{rep1_call}/email", json=email_payload, headers=_headers(mgr_token))
    check("manager can edit email (200)", resp.status_code == 200)

    resp = client.patch(f"/api/pipeline/{rep1_call}/email", json=email_payload, headers=_headers(rep1_token))
    check("rep is DENIED email edit (403)", resp.status_code == 403)

    # ── Test 6: User management ─────────────────────────
    print("\n── 6. User management (GET /api/auth/users) ──")

    # Admin can list users
    resp = client.get("/api/auth/users", headers=_headers(admin_token))
    check("admin can list users (200)", resp.status_code == 200)
    emails = {u["email"] for u in resp.json()}
    check("admin sees all test users", "admin@test.com" in emails and "rep1@test.com" in emails)

    # Manager can list users (view-only)
    resp = client.get("/api/auth/users", headers=_headers(mgr_token))
    check("manager can list users (200)", resp.status_code == 200)

    # Rep cannot list users
    resp = client.get("/api/auth/users", headers=_headers(rep1_token))
    check("rep cannot list users (403)", resp.status_code == 403)

    # ── Test 7: Unauthenticated access ──────────────────
    print("\n── 7. Unauthenticated access ──")

    resp = client.get(f"/api/pipeline/{rep1_call}/status")
    check("status rejects unauthenticated (401)", resp.status_code == 401)

    resp = client.patch(f"/api/pipeline/{rep1_call}/crm", json=crm_payload)
    check("CRM edit rejects unauthenticated (401)", resp.status_code == 401)

    resp = client.patch(f"/api/pipeline/{rep1_call}/email", json=email_payload)
    check("email edit rejects unauthenticated (401)", resp.status_code == 401)

    # ── Test 8: File upload pipeline ────────────────────
    print("\n── 8. Pipeline upload ──")

    wav_bytes = _dummy_wav()
    resp = client.post(
        "/api/pipeline/run",
        files={"audio_file": ("test.wav", wav_bytes, "audio/wav")},
        headers=_headers(rep1_token),
    )
    check("rep can upload (202)", resp.status_code == 202)

    resp = client.post(
        "/api/pipeline/run",
        files={"audio_file": ("test.wav", wav_bytes, "audio/wav")},
        headers=_headers(admin_token),
    )
    check("admin can upload (202)", resp.status_code == 202)

    # ── Summary ─────────────────────────────────────────
    print(f"\n{'=' * 60}")
    total = PASS + FAIL
    print(f"Results: {PASS}/{total} passed, {FAIL}/{total} failed")
    if FAIL > 0:
        sys.exit(1)
    print("All RBAC E2E tests passed!")


if __name__ == "__main__":
    test_rbac()
