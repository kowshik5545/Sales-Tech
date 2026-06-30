-- Intelligent Sales Rep Assistant — Supabase Schema
-- Run this in the Supabase SQL Editor (Dashboard → SQL Editor → New Query)
-- or use: psql $SUPABASE_DATABASE_URL -f docs/supabase_schema.sql
--
-- This is the source of truth matched to models/schemas.py

-- Drop existing tables (for re-runs)
drop table if exists coaching_reports cascade;
drop table if exists email_drafts cascade;
drop table if exists opportunity_reports cascade;
drop table if exists crm_records cascade;
drop table if exists transcripts cascade;
drop table if exists call_sessions cascade;
drop table if exists users cascade;

-- ─── 0. users (for RBAC) ─────────────────────────────────
create table if not exists users (
    id              uuid primary key default gen_random_uuid(),
    email           text unique not null,
    password_hash   text not null,
    name            text not null,
    role            text not null check (role in ('admin', 'manager', 'rep')),
    created_at      timestamptz not null default now()
);

-- ─── 1. call_sessions ───────────────────────────────────
create table if not exists call_sessions (
    id              uuid primary key default gen_random_uuid(),
    audio_file_name text not null,
    status          text not null default 'pending',
    error_message   text,
    user_id         uuid references users(id) on delete set null,
    created_at      timestamptz not null default now(),
    completed_at    timestamptz
);

-- ... rest of tables remain the same ...

-- ─── 2. transcripts ─────────────────────────────────────
create table if not exists transcripts (
    id               uuid primary key default gen_random_uuid(),
    call_id          uuid not null references call_sessions(id) on delete cascade,
    audio_file_name  text not null default '',
    full_text        text not null default '',
    segments         jsonb not null default '[]',
    duration_seconds float not null default 0
);

-- ─── 3. crm_records ─────────────────────────────────────
create table if not exists crm_records (
    id             uuid primary key default gen_random_uuid(),
    call_id        uuid not null references call_sessions(id) on delete cascade,
    contact_name   text not null,
    contact_email  text not null default '',
    company        text not null,
    deal_stage     text not null,
    pain_points    jsonb not null default '[]',
    next_steps     text not null default '',
    call_date      date
);

-- ─── 4. opportunity_reports ─────────────────────────────
create table if not exists opportunity_reports (
    id                uuid  primary key default gen_random_uuid(),
    call_id           uuid  not null references call_sessions(id) on delete cascade,
    buying_signals    jsonb not null default '[]',
    opportunity_flags jsonb not null default '[]'
);

-- ─── 5. email_drafts ────────────────────────────────────
create table if not exists email_drafts (
    id      uuid primary key default gen_random_uuid(),
    call_id uuid not null references call_sessions(id) on delete cascade,
    subject text not null default '',
    body    text not null default ''
);

-- ─── 6. coaching_reports ────────────────────────────────
create table if not exists coaching_reports (
    id                   uuid  primary key default gen_random_uuid(),
    call_id              uuid  not null references call_sessions(id) on delete cascade,
    rubric_scores        jsonb not null default '[]',
    talk_ratio_rep       float not null default 0,
    talk_ratio_customer  float not null default 0,
    strengths            jsonb not null default '[]',
    areas_to_improve     jsonb not null default '[]',
    recommended_actions  jsonb not null default '[]'
);

-- ─── Indexes for performance ────────────────────────────
create index if not exists idx_transcripts_call_id on transcripts(call_id);
create index if not exists idx_crm_records_call_id on crm_records(call_id);
create index if not exists idx_opportunity_reports_call_id on opportunity_reports(call_id);
create index if not exists idx_email_drafts_call_id on email_drafts(call_id);
create index if not exists idx_coaching_reports_call_id on coaching_reports(call_id);
create index if not exists idx_call_sessions_status on call_sessions(status);
create index if not exists idx_call_sessions_created_at on call_sessions(created_at desc);

-- ─── Row Level Security (optional — disable for dev) ────
alter table call_sessions disable row level security;
alter table transcripts disable row level security;
alter table crm_records disable row level security;
alter table opportunity_reports disable row level security;
alter table email_drafts disable row level security;
alter table coaching_reports disable row level security;

-- ─── Verify tables ──────────────────────────────────────
select table_name from information_schema.tables
where table_schema = 'public'
order by table_name;
