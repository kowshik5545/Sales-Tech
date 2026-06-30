"""Seed demo users into Supabase for RBAC."""
import sys, os, bcrypt
from dotenv import load_dotenv
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from supabase import create_client

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_ANON_KEY")
sb = create_client(url, key)

users = [
    ("admin@example.com", "admin123", "Admin User", "admin"),
    ("manager@example.com", "manager123", "Sarah Manager", "manager"),
    ("rep1@example.com", "rep123", "John Rep", "rep"),
    ("rep2@example.com", "rep123", "Lisa Rep", "rep"),
]

for email, pw, name, role in users:
    pw_hash = bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    r = sb.table("users").upsert({
        "email": email,
        "password_hash": pw_hash,
        "name": name,
        "role": role,
    }).execute()
    data = getattr(r, "data", []) or []
    uid = data[0]["id"] if data else "unknown"
    print(f"  Seeded {email} ({role}) -> {uid[:8]}...")

r = sb.table("users").select("id,email,name,role").execute()
print(f"\nVerified: {len(r.data)} users in Supabase")
for u in r.data:
    print(f"  {u['email']} ({u['role']})")
