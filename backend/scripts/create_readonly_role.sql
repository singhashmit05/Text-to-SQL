-- Run this once against your PostgreSQL database (as an admin/superuser).
-- Creates the read-only role the agent connects as. This is guardrail
-- layer #2 — even if the app-level checks in db/guardrails.py were
-- somehow bypassed, Postgres itself would reject any write.
--
-- SUPABASE: run this in the Supabase Dashboard > SQL Editor (it runs as
-- the "postgres" superuser automatically, so you don't need a separate
-- psql connection). Replace 'yourdb' below with 'postgres' — Supabase
-- projects use a single database named "postgres".

CREATE ROLE sql_agent_ro LOGIN PASSWORD 'CHANGE_ME';

GRANT CONNECT ON DATABASE postgres TO sql_agent_ro;
GRANT USAGE ON SCHEMA public TO sql_agent_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO sql_agent_ro;

-- Ensures future tables are also read-only for this role automatically.
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO sql_agent_ro;

-- Optional but recommended: cap how long any one query can run for this role.
ALTER ROLE sql_agent_ro SET statement_timeout = '15s';
