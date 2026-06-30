"""
One‑command setup: create tables, seed users, then seed 5 demo scenarios into Supabase.

Usage:
    python scripts/setup_db.py

Requires SUPABASE_URL / SUPABASE_ANON_KEY in .env or environment.
"""

import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone

import bcrypt

# Ensure backend/ is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
from supabase import create_client

from scripts.demo_dialogues import ALL_DIALOGUES, build_full_text, build_segments  # noqa: E402

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Also try loading .env.bak for SUPABASE_DATABASE_URL
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env.bak"))

SQL_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "supabase_schema.sql")

SEED_USERS = [
    {
        "email": "admin@example.com",
        "password": "admin123",
        "name": "Admin User",
        "role": "admin",
    },
    {
        "email": "manager@example.com",
        "password": "manager123",
        "name": "Sarah Manager",
        "role": "manager",
    },
    {
        "email": "rep1@example.com",
        "password": "rep123",
        "name": "John Rep",
        "role": "rep",
    },
    {
        "email": "rep2@example.com",
        "password": "rep123",
        "name": "Lisa Rep",
        "role": "rep",
    },
]

# Assign demo calls to users (rep1 gets 3, rep2 gets 2)
SESSION_USER_MAP = [
    "rep1@example.com",
    "rep1@example.com",
    "rep1@example.com",
    "rep2@example.com",
    "rep2@example.com",
]

# Map scenario metadata from ALL_DIALOGUES
SCENARIO_META = {
    "Sarah Chen": {
        "contact_email": "sarah.chen@techcorp.com",
        "pain_points": ["Manual reporting takes 12+ hours/week"],
        "next_steps": "Schedule technical demo for next Tuesday",
        "call_date": "2026-06-20",
        "subject": "Follow-up: Reporting Automation Demo",
        "body": "Hi Sarah, thanks for the great call. As discussed, here is a summary of what we covered. I will send the proposal by end of day tomorrow and look forward to our demo on Tuesday.",
    },
    "Marcus Johnson": {
        "contact_email": "marcus.j@innovatehub.com",
        "pain_points": ["Data silos between sales and marketing"],
        "next_steps": "Send case studies on data unification",
        "call_date": "2026-06-18",
        "subject": "Data Unification Case Studies",
        "body": "Marcus, here are the case studies we discussed. They show how companies similar to InnovateHub achieved unified sales and marketing data with our platform.",
    },
    "Priya Patel": {
        "contact_email": "priya@scaleup.ai",
        "pain_points": ["Scaling customer onboarding without headcount growth", "No analytics on onboarding bottlenecks"],
        "next_steps": "Send pricing proposal by Friday",
        "call_date": "2026-06-15",
        "subject": "Proposal: Onboarding Automation Platform",
        "body": "Priya, as promised, here is the formal proposal for our onboarding automation platform. I have included pricing, implementation timeline, and ROI projections. Let me know if you have any questions.",
    },
    "Alex Rivera": {
        "contact_email": "alex.r@dataflow.io",
        "pain_points": ["High latency in real-time data pipelines", "No visibility into pipeline health"],
        "next_steps": "Review contract terms and prepare discount approval",
        "call_date": "2026-06-12",
        "subject": "Contract Review - DataFlow Inc.",
        "body": "Alex, please find the updated contract with the trial terms and fifteen percent discount reflected. I have also included the SLA details as requested.",
    },
    "Emily Watson": {
        "contact_email": "emily@retailnext.com",
        "pain_points": ["Legacy POS integration limiting omnichannel growth"],
        "next_steps": "Kick-off call scheduled for July 1st",
        "call_date": "2026-06-10",
        "subject": "Welcome to RetailNext - Next Steps",
        "body": "Emily, welcome aboard! Here is your onboarding plan. We will start with a data audit next week and target full launch by early October.",
    },
}


def _tables_exist(sb) -> bool:
    """Check if all required tables exist in Supabase."""
    for t in ["users", "call_sessions", "transcripts", "crm_records", "opportunity_reports", "email_drafts", "coaching_reports"]:
        try:
            sb.table(t).select("id").limit(1).execute()
        except Exception:
            return False
    return True


def _create_tables_via_psql() -> bool:
    """Create tables using psql and SUPABASE_DATABASE_URL."""
    db_url = os.getenv("SUPABASE_DATABASE_URL")
    if not db_url or "your-project" in db_url or "user:password" in db_url:
        print("  SUPABASE_DATABASE_URL not set in .env or .env.bak")
        return False
    if not os.path.isfile(SQL_FILE):
        print(f"  Schema file not found: {SQL_FILE}")
        return False
    try:
        result = subprocess.run(
            ["psql", db_url, "-f", SQL_FILE],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            print(f"  psql error: {result.stderr[:500]}")
            return False
        for line in result.stdout.splitlines():
            if "CREATE TABLE" in line:
                print(f"    {line}")
        print("  Schema applied via psql.")
        return True
    except FileNotFoundError:
        print("  psql not found on PATH")
        return False
    except Exception as e:
        print(f"  psql failed: {e}")
        return False


def _seed_users(sb, user_id_map: dict) -> dict:
    """Seed demo users and return {email: user_id} map."""
    print("\n--- Seeding users ---")
    for u in SEED_USERS:
        existing = sb.table("users").select("id").eq("email", u["email"]).limit(1).execute()
        existing_rows = getattr(existing, "data", []) or []
        if existing_rows:
            uid = existing_rows[0]["id"]
            print(f"  {u['email']} already exists (id={uid[:8]}...)")
            user_id_map[u["email"]] = uid
            continue

        pw_hash = bcrypt.hashpw(u["password"].encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        result = sb.table("users").upsert({
            "email": u["email"],
            "password_hash": pw_hash,
            "name": u["name"],
            "role": u["role"],
        }).execute()
        rows = getattr(result, "data", []) or []
        uid = rows[0]["id"] if rows else str(uuid.uuid4())
        user_id_map[u["email"]] = uid
        print(f"  Created {u['email']} ({u['role']}) -> {uid[:8]}...")

    # Also create a users table via SQL if it doesn't exist yet
    try:
        sb.table("users").select("id").limit(0).execute()
        print("  Users table ready.")
    except Exception:
        print("  WARNING: Users table not accessible via API. Check that it exists in Supabase.")

    return user_id_map


def main():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    if not url or not key or "your-project" in url:
        print("ERROR: SUPABASE_URL / SUPABASE_ANON_KEY not set or still placeholders in .env")
        sys.exit(1)

    print(f"Connecting to Supabase project: {url}")
    sb = create_client(url, key)

    # ── 1. Run schema (if tables missing) ────────────────
    print("\n=== Step 1: Create tables (if missing) ===")
    if _tables_exist(sb):
        print("  All required tables already exist.")
    else:
        print("  Some tables missing. Attempting to create via psql...")
        if _create_tables_via_psql():
            if not _tables_exist(sb):
                print("  WARNING: Tables still not visible after psql.")
        else:
            print("  Could not create tables via psql.")
            print("  Run the SQL manually in Supabase Dashboard -> SQL Editor:")
            print(f"    Open {SQL_FILE} and paste into the editor, then click Run.")
            proceed = input("  Type 'y' to continue with seeding anyway: ").strip().lower()
            if proceed != "y":
                sys.exit(1)

    # ── 2. Seed users ──────────────────────────────────────
    print("\n=== Step 2: Seed users ===")
    user_id_map: dict[str, str] = {}
    user_id_map = _seed_users(sb, user_id_map)

    # ── 3. Seed demo data ────────────────────────────────
    print("\n=== Step 3: Seed 5 demo scenarios ===")

    for i, scenario in enumerate(ALL_DIALOGUES):
        call_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        name = scenario["name"]
        meta = SCENARIO_META[name]
        dialogue = scenario["dialogue"]
        deal_stage = scenario["deal_stage"]
        company = scenario["company"]

        # Assign session to a user
        user_email = SESSION_USER_MAP[i]
        user_id = user_id_map.get(user_email)

        print(f"\n  [{i+1}/5] {name} -- {company} ({deal_stage}) -- {user_email}")

        full_text = build_full_text(dialogue)
        segments = build_segments(dialogue)
        duration = segments[-1]["timestamp_end"] if segments else 60.0

        # call_sessions
        session_payload = {
            "id": call_id,
            "audio_file_name": f"demo_call_{i+1}.wav",
            "status": "complete",
            "created_at": created_at,
            "completed_at": created_at,
        }
        if user_id:
            session_payload["user_id"] = user_id
        sb.table("call_sessions").upsert(session_payload).execute()
        print(f"    OK - call_sessions (user_id={user_id[:8] if user_id else 'None'}...)")

        # transcripts
        sb.table("transcripts").upsert({
            "call_id": call_id,
            "audio_file_name": f"demo_call_{i+1}.wav",
            "full_text": full_text,
            "segments": segments,
            "duration_seconds": duration,
        }).execute()
        print(f"    OK - transcripts ({len(segments)} segments, {duration:.0f}s)")

        # crm_records
        sb.table("crm_records").upsert({
            "call_id": call_id,
            "contact_name": name,
            "contact_email": meta["contact_email"],
            "company": company,
            "deal_stage": deal_stage,
            "pain_points": meta["pain_points"],
            "next_steps": meta["next_steps"],
            "call_date": meta["call_date"],
        }).execute()
        print(f"    OK - crm_records")

        # opportunity_reports
        sb.table("opportunity_reports").upsert({
            "call_id": call_id,
            "buying_signals": [
                {"quote": "Customer asked about pricing options", "signal_type": "pricing_inquiry", "confidence": 0.85},
                {"quote": "Mentioned specific timeline for decision", "signal_type": "timeline", "confidence": 0.7},
            ],
            "opportunity_flags": [
                {"opportunity_type": "upsell", "product_suggestion": "Enterprise plan", "evidence": "Customer confirmed budget for Q3", "confidence": 0.8},
            ],
        }).execute()
        print(f"    OK - opportunity_reports")

        # email_drafts
        sb.table("email_drafts").upsert({
            "call_id": call_id,
            "subject": meta["subject"],
            "body": meta["body"],
        }).execute()
        print(f"    OK - email_drafts")

        # coaching_reports
        sb.table("coaching_reports").upsert({
            "call_id": call_id,
            "rubric_scores": [
                {"dimension": "Discovery", "score": 4, "comment": "Good discovery questions asked"},
                {"dimension": "Objection Handling", "score": 3, "comment": "Could improve response to objections"},
                {"dimension": "Closing", "score": 5 if deal_stage == "Closed Won" else 3, "comment": "Solid closing technique"},
                {"dimension": "Product Knowledge", "score": 4, "comment": "Demonstrated good product knowledge"},
                {"dimension": "Active Listening", "score": 3, "comment": "Some areas to improve listening"},
            ],
            "talk_ratio_rep": 42.0,
            "talk_ratio_customer": 58.0,
            "strengths": ["Good questioning", "Empathy shown"],
            "areas_to_improve": ["Speak slower", "Pause after objections"],
            "recommended_actions": ["Practice discovery questions", "Role-play objection handling"],
        }).execute()
        print(f"    OK - coaching_reports")
        print(f"    -> call_id: {call_id}")

    print("\n=== Setup complete! ===")
    print("Demo users created:")
    for u in SEED_USERS:
        print(f"  {u['email']} / {u['password']} ({u['role']})")
    print()
    print("5 demo scenarios are now stored in Supabase with user associations.")
    print("Restart the backend, then refresh the frontend.")


if __name__ == "__main__":
    main()
