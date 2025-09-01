# FirstRead Assessment

## Overview
A two-service application for streaming AI-assisted contract generation:
- **API (FastAPI)**: Auth (JWT), contract generation via Google Gemini, SSE streaming, cancellation.
- **Web (Next.js 15 / React 19 / App Router)**: UI for prompt entry, live streamed contract content, download & preview.
- **PostgreSQL** (expected via `DATABASE_URL`) used by the API (Alembic migrations scaffolded).

---
## Architecture
```
+------------------+          SSE (text/event-stream)         +-----------------------+
|  Web (Next.js)   |  <------------------------------------   |  API (FastAPI)        |
|  - Prompt form   |   POST /api/contracts (proxy)  ------>   |  /contracts           |
|  - Stream parser |                                         |   - Generate Title    |
|  - Cancel button |   DELETE /api/contracts/{id}/stop ---->  |   - TOC (Gemini)      |
|  - HTML preview  |                                         |   - Section streaming |
+---------+--------+                                         +-----------+-----------+
          |                                                              |
          | Auth (register/login -> JWT)                                 | Google Gemini API
          v                                                              v
   LocalStorage (JWT)                                      AI text generation (Gemini)
```

### Architecture
- **Streaming**: Custom SSE formatting splits multi-line AI output into discrete `data:` events to avoid client loss of content.
- **Cancellation**: In-memory map of `contract_id` to `asyncio.Event`; DELETE triggers event to abort generation loop.
- **Resilience**: Section generation wrapped with `tenacity` retries to mitigate transient model errors.
- **Security**: Stateless JWT auth (register returns token; signout just validates); secrets sourced from env.
- **Formatting**: Frontend post-process adds line breaks before sub‑clause numbering (e.g. `1.1`, `2.3.1`).
- **Planner & Writer Agents**: A lightweight *planner* agent first creates the contract title and a structured Table of Contents (the "plan"). Then a *writer* agent is invoked sequentially per section. This avoids a single long prompt that could exceed / approach the model token window, enables partial early delivery (streaming each section), supports cancellation between sections, and isolates retries to only the failed section instead of regenerating the entire contract.

### Design Tradeoffs & Reasoning
| Decision | Tradeoff | Rationale |
|----------|----------|-----------|
| SSE + manual fetch reader | More client code vs EventSource | Precise control over backpressure & custom events. |
| In-memory cancellation registry | Not persistent / not multi-instance | Simplicity for prototype; easy to replace with Redis later. |
| Stateless JWT | Manual token storage | Lightweight; avoids DB session table. |
| Gemini direct calls per section | Latency per section | Parallelism avoided to preserve ordering & manage rate limits. |
| Post-processing clause breaks client-side | Possible mismatch if HTML changes | Avoids extra model tokens / backend parsing complexity. |
| Alembic + SQLAlchemy even w/out full persistence yet | Some unused scaffolding | Future-proof for storing contracts/users. |
| Planner + per-section writer | More round trips / latency per section | Prevents max token context blowout, improves resiliency & allows granular retries and cancellation. |

---
## Environment Variables
Create the following files based on examples:

### API (`apps/api/.env`)
```
DATABASE_URL=postgresql://postgres:postgres@db:5432/contracts
GEMINI_API_KEY=your_gemini_key
SECRET_KEY=your_random_secret 
HASH_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```
The Postgresql url is postgresql://neondb_owner:npg_fw3XyUKTGn9i@ep-snowy-silence-adqzxyf5-pooler.c-2.us-east-1.aws.neon.tech/neondb

#### Generating `SECRET_KEY`
Use any sufficiently long random string (32+ bytes). Examples:
```powershell
# PowerShell (hex string 64 chars ~ 32 bytes)
[guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')

# Python (from project root)
python - <<'PY'
import secrets; print(secrets.token_urlsafe(48))
PY

# OpenSSL (if installed)
openssl rand -base64 48
```
Choose one output and paste into `SECRET_KEY=`.

#### Obtaining `GEMINI_API_KEY`
1. Visit: https://aistudio.google.com/app/apikey
2. Sign in with a Google account & create a new API key.
3. Copy the key and set `GEMINI_API_KEY=<copied value>`.
4. Keep this secret; do **not** commit it. (The `.env` file is excluded from version control.)

### Web (`apps/web/.env.local`)
```
# Internal service URL used by Next.js server (inside container)
API_URL=http://api:8000
# Public browser URL for the API (host -> container mapping)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

> Ensure the `DATABASE_URL` protocol is `postgresql://`; the API derives the async variant automatically.

---
## Local Development (Docker Recommended)

### Prerequisites
- Docker & Docker Compose
- Gemini API key

### Start Services
```powershell
# From repo root
docker compose up --build
```
Services:
- API: http://localhost:8000 (Swagger UI at `/docs`)
- Web: http://localhost:3000 (UI)

### Iterative Dev
```powershell
# Restart only web after frontend changes
docker compose restart web

# View logs
docker compose logs -f api
```

### Without Docker (Alternative)
API:
```powershell
cd apps/api
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -e .
uvicorn src.main:app --reload --port 8000
```
Web:
```powershell
cd apps/web
npm install
npm run dev
```
Set `API_URL` / `NEXT_PUBLIC_API_URL` accordingly when running outside compose.

---
## Deployment Notes
- Containerize both services (already Dockerfile’d). Use a managed Postgres (e.g., RDS / Cloud SQL).
- Provide environment secrets via platform secret manager.
- Scale out API: replace in-memory cancellation with shared store (Redis) & ensure sticky or idempotent stop calls.
- Add rate limiting & audit logging before production.

---
## Extensibility Roadmap (Optional)
- Persist generated contracts (store sections incrementally for resume/replay).
- Add user accounts persistence & role-based access.
- Replace raw HTML accumulation with structured AST -> renderers (HTML/PDF/Docx).
- Streaming diff highlighting for edits / regeneration of specific clauses.
- Observability: OpenTelemetry traces around model calls & streaming loop.

---
## Running Tests
(Currently minimal / none). Suggested next steps:
- Add unit tests for SSE formatter & clause break formatter.
- Integration test simulating full stream consumption.

---
## Troubleshooting
| Symptom | Cause | Fix |
|---------|-------|-----|
| Only first line of a section shows | Multi-line SSE not split | Already handled by updated `sse_format`; ensure rebuild. |
| ECONNREFUSED from web to api | Using `localhost` inside container | Use `http://api:8000` for internal server-side calls. |
| Stop not working | Missing `contract_id` event early | Confirm first SSE event includes JSON with `contract_id`. |
| Clause breaks missing | Post-process not triggered | Ensure generation reached `done` event; check console for errors. |

---
## License
Internal assessment project (no explicit license specified). Add one if distributing.
