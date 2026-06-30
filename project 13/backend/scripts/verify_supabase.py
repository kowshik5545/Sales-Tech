"""
Verify Supabase connectivity by testing:
1. Connection (list tables)
2. Read seed data (list all sessions with CRM data)
3. Write a test record (then clean up)

Usage:
    python scripts/verify_supabase.py
"""

import os
import sys
import uuid
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
from supabase import create_client

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

PASS = 0
FAIL = 0


def check(description: str, ok: bool):
    global PASS, FAIL
    if ok:
        print(f"   {description}")
        PASS += 1
    else:
        print(f"   {description}")
        FAIL += 1


def main():
    global PASS, FAIL
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    if not url or not key or "your-project" in url:
        print("ERROR: SUPABASE_URL / SUPABASE_ANON_KEY not set or still placeholders in .env")
        sys.exit(1)

    print(f"Supabase URL: {url}")
    sb = create_client(url, key)

    #  1. List tables 
    print("\n Connection & Tables ")
    try:
        resp = sb.table("call_sessions").select("id").limit(1).execute()
        check("call_sessions table accessible", True)
    except Exception as e:
        check(f"call_sessions accessible: {e}", False)

    tables = {
        "call_sessions": False,
        "transcripts": False,
        "crm_records": False,
        "opportunity_reports": False,
        "email_drafts": False,
        "coaching_reports": False,
    }
    for t in tables:
        try:
            sb.table(t).select("id").limit(1).execute()
            tables[t] = True
        except Exception:
            tables[t] = False
        check(f"table '{t}' exists", tables[t])

    if not all(tables.values()):
        print("\n  Some tables are missing. Run `python scripts/setup_db.py` first.")
        if FAIL > 0:
            sys.exit(1)

    #  2. Read seed data 
    print("\n Seed Data (should have 5 demo sessions) ")
    try:
        resp = sb.table("call_sessions").select("id, status").execute()
        rows = resp.data if hasattr(resp, "data") else []
        check(f"call_sessions has {len(rows)} rows", len(rows) >= 5)
    except Exception as e:
        check(f"read call_sessions: {e}", False)
        rows = []

    if rows:
        cid = rows[0]["id"]
        for t, label in [
            ("transcripts", "transcripts"),
            ("crm_records", "CRM records"),
            ("opportunity_reports", "opportunity reports"),
            ("email_drafts", "email drafts"),
            ("coaching_reports", "coaching reports"),
        ]:
            try:
                r = sb.table(t).select("id").eq("call_id", cid).execute()
                data = r.data if hasattr(r, "data") else []
                check(f"  related {label} found", len(data) > 0)
            except Exception as e:
                check(f"  related {label}: {e}", False)

    #  3. Write & clean up a test record 
    print("\n Write / Read / Delete ")
    test_id = str(uuid.uuid4())
    try:
        sb.table("call_sessions").upsert({
            "id": test_id,
            "audio_file_name": "_verify_test.wav",
            "status": "pending",
        }).execute()
        check("insert test session", True)
    except Exception as e:
        check(f"insert test session: {e}", False)

    try:
        r = sb.table("call_sessions").select("status").eq("id", test_id).execute()
        data = r.data if hasattr(r, "data") else []
        check(f"read test session back", data and data[0]["status"] == "pending")
    except Exception as e:
        check(f"read test session: {e}", False)

    try:
        sb.table("call_sessions").delete().eq("id", test_id).execute()
        check("delete test session", True)
    except Exception as e:
        check(f"delete test session: {e}", False)

    try:
        r = sb.table("call_sessions").select("id").eq("id", test_id).execute()
        data = r.data if hasattr(r, "data") else []
        check("test session actually gone", len(data) == 0)
    except Exception as e:
        check(f"verify deletion: {e}", False)

    #  Summary 
    total = PASS + FAIL
    print(f"\n Results: {PASS}/{total} passed, {FAIL}/{total} failed ")
    if FAIL > 0:
        sys.exit(1)
    print("All checks passed!")


if __name__ == "__main__":
    main()
