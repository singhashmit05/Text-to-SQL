# Text-to-SQL Agent

Ask questions about your PostgreSQL database in plain English and get
accurate SQL queries, results, and a plain-English answer — via a React
chat UI backed by a Gemini-powered LangChain agent (using Google AI
Studio's free tier — no billing required).

Built on the workflow from [langchain-ai/text-to-sql-agent](https://github.com/langchain-ai/text-to-sql-agent),
extended with a full web UI, PostgreSQL, and SQL-injection/write guardrails.

## Architecture

```
frontend/   React + Vite chat UI          → deployed on Vercel
backend/    FastAPI + LangChain agent      → deployed on Render/Railway
            PostgreSQL (read-only role)
```

```
User → React chat UI → FastAPI /api/query → LangChain agent (Gemini)
                                                 │
                                    ┌────────────┼────────────┐
                                 list tables  get schema   run_guarded_sql_query
                                                                 │
                                                    guardrails.validate_query()
                                                                 │
                                                     PostgreSQL (read-only role)
```

## Agent workflow

1. **Discover** – list tables
2. **Inspect** – get schema + sample rows for relevant tables
3. **Generate** – Gemini writes a SQL query
4. **Validate** – `guardrails.validate_query()` rejects anything that isn't
   a single, clean `SELECT` (see below)
5. **Execute** – query runs against the read-only DB role, with a
   statement timeout
6. **Retry** – on rejection/error, Gemini rewrites and tries again
   (bounded by `MAX_AGENT_RETRIES`)
7. **Format** – Gemini turns the rows into a plain-English answer

## Bring-your-own-dataset

Users can upload a CSV or Excel file directly from the chat UI ("+ Add your
own dataset") and immediately ask questions about it — no manual DB setup
needed.

**How it works:**
1. The file is parsed with pandas.
2. Table + column names are sanitized (untrusted input) into safe Postgres
   identifiers.
3. The table is created via a separate **admin connection**
   (`DATABASE_ADMIN_URL`) that has `CREATE`/`INSERT` privileges — the
   agent's own connection (`DATABASE_URL`, the `sql_agent_ro` role) never
   gets write access, even for this feature.
4. `sql_agent_ro` is granted `SELECT` on just the new table.
5. The agent reflects the schema fresh on every query, so the new table is
   queryable immediately — no restart needed.

Limits (`backend/.env`): `MAX_UPLOAD_MB` (default 15) and
`MAX_UPLOAD_ROWS` (default 200,000).

## Guardrails (three independent layers)

| Layer | Where | What it stops |
|---|---|---|
| 1. Static SQL validation | `backend/app/db/guardrails.py` | Non-SELECT statements, blocked keywords (INSERT/UPDATE/DELETE/DROP/...), multi-statement injection, oversized LIMIT |
| 2. DB role privileges | Postgres, via `backend/scripts/create_readonly_role.sql` | Any write, even if layer 1 were bypassed |
| 3. Statement timeout | `backend/app/db/session.py` + role setting | Runaway/expensive queries hanging the API |

## Local setup

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in GOOGLE_API_KEY (free, from aistudio.google.com/apikey) + DATABASE_URL
```
Create the read-only role — open the **Supabase Dashboard → SQL Editor**,
paste in `scripts/create_readonly_role.sql`, and run it (Supabase runs
this as the `postgres` superuser automatically, no extra connection needed).

Then get your connection string: **Project Settings → Database →
Connection string → Session pooler**, swap in the `sql_agent_ro`
username/password, and append `?sslmode=require`. Put that in
`DATABASE_URL` in `.env`. (Use the *Session* pooler, not *Transaction*
pooler — the transaction pooler doesn't support prepared statements,
which SQLAlchemy's connection pool needs.)

Also set `DATABASE_ADMIN_URL` — this is your default Supabase `postgres`
role's connection string (same Session pooler format, no role swap needed).
It's used only by the dataset-upload feature to create tables; the agent
itself never touches it.

Run the API:
```bash
uvicorn app.main:app --reload --port 8000
```
Docs at `http://localhost:8000/docs`.

### Frontend
```bash
cd frontend
npm install
cp .env.example .env   # VITE_API_URL=http://localhost:8000
npm run dev
```
Open `http://localhost:5173`.

## Deployment

**Frontend → Vercel**
1. Push this repo to GitHub.
2. Import it in Vercel, set root directory to `frontend`.
3. Add env var `VITE_API_URL` = your deployed backend URL.
4. Deploy — Vercel auto-detects Vite via `vercel.json`.

**Backend → Render** (recommended over Vercel serverless — the agent's
multi-step tool loop can exceed serverless timeouts and needs a stable
Postgres connection pool)
1. In Render, "New Web Service" → connect repo → root directory `backend`.
2. It picks up `render.yaml` and `Dockerfile` automatically.
3. Set `GOOGLE_API_KEY`, `DATABASE_URL` (your read-only role's URL),
   and `CORS_ALLOW_ORIGINS` (your Vercel URL) as env vars.
4. Deploy. Once live, update the frontend's `VITE_API_URL` to point here.

*(Railway or Fly.io work the same way if you prefer them to Render.)*

## Optional: LangSmith tracing

Set in `backend/.env`:
```
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_key
LANGCHAIN_PROJECT=text2sql-agent
```
Every agent run — tool calls, tokens, retries — will show up at
https://smith.langchain.com/

## Requirements

- Python 3.11+, Node 18+
- A PostgreSQL database (Supabase — any schema; point `DATABASE_URL` at it)
- Google API key (free — https://aistudio.google.com/apikey)

## License

MIT
