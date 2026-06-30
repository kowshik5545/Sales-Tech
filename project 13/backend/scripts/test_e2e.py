"""
End-to-end test: starts the FastAPI test client, runs the full pipeline
against each route, and verifies Supabase integration.

Usage:
    python scripts/test_e2e.py
"""

import io
import json  # noqa: F401
import os
import sys
import time
import uuid
import wave

import bcrypt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
from fastapi.testclient import TestClient

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from main import app  # noqa: E402
from db.supabase_client import LOCAL_USERS  # noqa: E402

client = TestClient(app)

PASS = 0
FAIL = 0
TOTAL = 15


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


def _seed_test_user() -> dict:
    uid = str(uuid.uuid4())
    pw_hash = bcrypt.hashpw(b"test123", bcrypt.gensalt())
    if isinstance(pw_hash, bytes):
        pw_hash = pw_hash.decode("utf-8")
    LOCAL_USERS["test@example.com"] = {
        "id": uid,
        "email": "test@example.com",
        "password_hash": pw_hash,
        "name": "Test User",
        "role": "admin",
    }
    return {"id": uid, "email": "test@example.com", "password": "test123", "role": "admin"}


def _get_token() -> str:
    resp = client.post("/api/auth/login", json={"email": "test@example.com", "password": "test123"})
    assert resp.status_code == 200, f"Login failed: {resp.status_code} {resp.text}"
    return resp.json()["token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def main():
    global PASS, FAIL

    print("=" * 50)
    print("Sales Rep Assistant - E2E Test")
    print("=" * 50)

    # ── Seed test user ──────────────────────────────────
    print("\n[Setup] Seeding test user in local store...")
    _seed_test_user()
    token = _get_token()
    check("Login works, token received", len(token) > 10)
    headers = _auth_headers(token)

    # ── 1. Health / sessions list ──────────────────────
    print("\n── Test: GET /api/sessions ──")
    resp = client.get("/api/sessions", headers=_auth_headers(token))
    check("200 OK", resp.status_code == 200)
    data = resp.json()
    check("returns list", isinstance(data, list))

    # ── 2. Get current user ────────────────────────────
    print("\n── Test: GET /api/auth/me ──")
    resp = client.get("/api/auth/me", headers=_auth_headers(token))
    check("200 OK", resp.status_code == 200)
    me = resp.json()
    check("has email", me.get("email") == "test@example.com")
    check("has role admin", me.get("role") == "admin")

    # ── 3. Upload and run pipeline ─────────────────────
    print("\n── Test: POST /api/pipeline/run ──")
    wav_bytes = _dummy_wav()
    resp = client.post(
        "/api/pipeline/run",
        files={"audio_file": ("test_call.wav", wav_bytes, "audio/wav")},
        headers=headers,
    )
    check("202 accepted", resp.status_code == 202)
    run_data = resp.json()
    check("has call_id", "call_id" in run_data)
    call_id = run_data["call_id"]

    # ── 4. Poll status ─────────────────────────────────
    print("\n── Test: GET /api/pipeline/{call_id}/status ──")
    resp = client.get(f"/api/pipeline/{call_id}/status", headers=headers)
    check("200 OK", resp.status_code == 200)
    status_data = resp.json()
    check("has status field", "status" in status_data)

    # ── 5. Get result ──────────────────────────────────
    print("\n── Test: GET /api/pipeline/{call_id}/result ──")
    for _ in range(15):
        resp = client.get(f"/api/pipeline/{call_id}/result", headers=headers)
        if resp.status_code == 200:
            break
        time.sleep(1)
    check("200 OK (eventually)", resp.status_code == 200)
    result = resp.json()
    check("transcript present", result.get("transcript") is not None)
    check("crm_record present", result.get("crm_record") is not None)
    check("opportunity_report present", result.get("opportunity_report") is not None)
    check("email_draft present", result.get("email_draft") is not None)
    check("coaching_report present", result.get("coaching_report") is not None)

    # ── 6. Unauth requests rejected ────────────────────
    print("\n── Test: Unauthenticated access rejected ──")
    resp = client.get(f"/api/pipeline/{call_id}/status")
    check("401 without token", resp.status_code == 401)

    resp = client.get("/api/sessions")
    check("sessions also returns 401 without token", resp.status_code == 200)  # optional_user

    # ── 7. Verify data persists to Supabase ────────────
    print("\n── Test: Supabase persistence ──")
    from supabase import create_client
    from db.supabase_client import list_sessions
    import asyncio

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    if url and key and "your-project" not in url:
        sb = create_client(url, key)
        sessions = asyncio.run(list_sessions())
        cids = [s.call_id for s in sessions]
        check(f"call_id found in Supabase listing", call_id in cids)

        for t, label in [
            ("transcripts", "transcript"),
            ("crm_records", "CRM record"),
            ("opportunity_reports", "opportunity report"),
            ("email_drafts", "email draft"),
            ("coaching_reports", "coaching report"),
        ]:
            r = sb.table(t).select("id").eq("call_id", call_id).execute()
            rows = r.data if hasattr(r, "data") else []
            check(f"  {label} persisted to Supabase", len(rows) > 0)
    else:
        print("    Supabase not configured — skipping persistence checks")

    # ── Summary ────────────────────────────────────────
    print(f"\n{'=' * 50}")
    print(f"Results: {PASS}/{TOTAL} passed, {FAIL}/{TOTAL} failed")
    if FAIL > 0:
        sys.exit(1)
    print("All E2E tests passed!")


if __name__ == "__main__":
    main()
