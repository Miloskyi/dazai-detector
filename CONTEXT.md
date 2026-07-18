# Project Context

> Living document. Update the **Status** and **Log** sections after each milestone. Everything else stays stable.

## What this is

A hybrid credit card fraud detection platform: unsupervised anomaly detection (DBSCAN) fused with a
supervised classifier (XGBoost) into a single risk score, explained per-transaction with SHAP, narrated
in plain language by an LLM (with a deterministic template fallback), summarized into automatic
high-risk reports, and queryable through a grounded investigation chat routed across specialist agents
backed by a ChromaDB RAG store.

## Why

Pure unsupervised fraud detection (the DBSCAN-only baseline) has good recall on novel anomalies but
weak precision and no calibrated probability. Pure supervised models are precise but blind to fraud
patterns not seen in training. Combining both, then explaining *why* each alert fired, turns a black-box
score into something an investigator can act on and trust.

## Architecture at a glance

```
data/  -> intelligence/pipeline (ML core) -> data/outputs/alerts.json
                                           -> data/outputs/reports/*
platform/rag        <- ingests alerts.json narratives into ChromaDB
platform/mcp_server  -> router agent + 3 specialists, grounded on pipeline outputs + RAG
platform/backend     -> FastAPI, wraps pipeline outputs + RAG + agents as REST
platform/frontend    -> React dashboard, alert explorer, reports, chat
```

Full diagrams and design pattern catalog: `docs/architecture.md`.
Implementation order and contracts: `docs/specs/00-overview.md` onward.

## Key design decisions

- Risk score = `0.7 * classifier_probability + 0.3 * dbscan_is_noise`, mapped to LOW/MEDIUM/HIGH/CRITICAL.
- DBSCAN has no `predict`; it is refit over the scoring window as a batch anomaly signal.
- Chat is never allowed to free-associate: a router classifies intent, and each specialist agent may
  only answer using tool outputs (stored stats, stored SHAP values, RAG hits). No tool result -> no answer.
- Backend and MCP server share the same agent implementations (`platform/mcp_server/agents`) — one brain, two
  entry points (REST for the frontend, MCP tools for external agent clients).
- Narrative generation is provider-agnostic (`LLMProvider` adapter). Without an API key configured, a
  deterministic template narrative is used so the demo never breaks.
- The `platform/mcp` folder was named `platform/mcp_server` to avoid colliding with the real `mcp` PyPI
  package fastmcp depends on. Entry-point scripts bootstrap `sys.path` with the project root (for
  `intelligence.*`) and `platform/` (for `backend.*`, `mcp_server.*`, `rag.*`) — this project never
  imports a top-level module literally named `platform` or `mcp`, to avoid shadowing the stdlib
  `platform` module and the real `mcp` package.

## Status

- [x] Folder scaffolding + specs
- [x] Data pipeline (spec 01)
- [x] Hybrid model (spec 02)
- [x] Explainability (spec 03)
- [x] Reports (spec 04)
- [x] RAG (spec 05)
- [x] MCP multi-agent (spec 06)
- [x] Backend API (spec 07)
- [x] Frontend (spec 08) — functional and verified end-to-end
- [x] Notebooks
- [x] End-to-end verification (pipeline -> report -> RAG -> backend -> MCP -> frontend, all 4 chat intents)
- [x] Docker Compose (`docker compose up --build` — one command, verified end-to-end)
- [x] Free deployment: Hugging Face Space (backend) + Cloudflare Pages (frontend), verified locally
- [x] UI hardening (spec 09) — dark/violet theme, resilient chat, paginated alerts, signal breakdown

## Log

- Project initialized. Folder structure and 9 SDD specs written under `docs/specs/`.
- Full implementation completed and verified end-to-end with a synthetic dataset (no Kaggle file
  present). Fixed two real bugs found during verification:
  1. `Preprocessor.scale()` was overwriting `Amount`/`Time` in place with z-scores, so alerts displayed
     scaled values instead of real dollar amounts — fixed by keeping `Amount_raw`/`Time_raw` alongside
     the scaled columns used only for model input.
  2. The intent router misclassified pattern/report questions mentioning "flagged" as `alert_lookup`
     (the word appears in every intent's natural phrasing) — fixed by checking an explicit alert ID
     first, generic "why was/is/did" phrasing last, and dropping "flagged"/"transaction" as standalone
     lookup signals.
- Next step: a visual design pass on the frontend (current UI is functional Tailwind, not yet polished).
- Python 3.10+ required (code uses PEP 604 `X | None` unions); system default was 3.9.6, so the venv
  was created with `python3.11` explicitly.
- Added Docker: `docker/python.Dockerfile` (shared by `pipeline`/`backend`/`mcp_server`, same deps,
  different CMD) and `platform/frontend/Dockerfile` (multi-stage Node build -> nginx with SPA
  fallback). `docker-compose.yml` runs `pipeline` once (dataset -> model -> report -> RAG ingest) then
  starts `backend` (8000), `mcp_server` (8001, HTTP transport instead of stdio so it's reachable in a
  container), and `frontend` (5173), all with overridable host ports via env vars since local dev
  machines often already have something on 8000/5173. Verified with a real `docker compose up --build`
  run: pipeline exited 0, all 4 chat intents answered correctly through the containerized backend, and
  the MCP server answered a real `initialize` JSON-RPC call over HTTP.
- No Vercel MCP connector is available in this session (only Cidenet-recruiting and Zoho CRM connectors
  are configured) and the `vercel` CLI isn't installed locally. Vercel is also not a great fit for this
  project's backend (FastAPI + XGBoost + ChromaDB need a persistent process/disk, not serverless
  functions) — it would only serve the static frontend well; the backend would need Railway/Render/
  Fly.io/a VPS. Docker Compose is the actual "run everything" answer for this stack.
- Free deployment decision: user asked about Coolify too — it's genuinely free (self-hosted, supports
  our docker-compose.yml almost as-is) but needs a host machine. Oracle Cloud Always Free was the
  obvious free-forever host, but as of June 2026 Oracle halved the ARM allowance (2 OCPU/12GB, down
  from 24GB) and has real-world capacity/suspension risk — too risky for a demo day. User chose the
  safer path: Hugging Face Spaces (Docker SDK, free `cpu-basic`, no card) for the backend + Cloudflare
  Pages (free, no card, unlimited bandwidth) for the frontend.
- Implemented and verified locally (via plain `docker build`/`docker run`, without any HF/Cloudflare
  account — I have no credentials for either): `deploy/huggingface-space/Dockerfile` bakes the dataset,
  hybrid model, report, and ChromaDB index into the image at build time (Spaces' filesystem is
  ephemeral) — confirmed the built image serves alerts/stats/chat correctly with zero mounted volumes.
  `deploy/huggingface-space/push.sh` deploys via a throwaway `hf-deploy` git branch so the project's
  real README/branch are never touched. `platform/backend/main.py` now reads `$PORT` (Spaces convention,
  defaults to 8000 unchanged locally). Frontend production build (`npm run build` with `VITE_API_URL`
  pointed at a placeholder Space URL) verified clean. Full step-by-step in `docs/deployment.md`. Project
  was `git init`'d (no commits made) since both platforms deploy via git and the repo had none yet —
  the user still needs to make the first commit and run the actual push themselves (requires their own
  HF/Cloudflare login).
- First commit made and pushed to `github.com/Juanpacol/Dazai-Detector-` (`main`, no AI attribution —
  confirmed this is a personal/portfolio repo, not the OpenAI hackathon submission, before pushing).
- UI hardening pass (spec 09), driven by a Behance reference ("Aivora" AI workflow dashboard) whose
  extracted design language (near-black bg, violet accent, pill badges, card-based sidebar layout) now
  drives the frontend theme. Also addressed reviewer-style feedback: chat used to leak raw errors and
  had no persisted history; `/api/alerts` had no pagination/limit validation; narrative "cache" was an
  in-memory dict that would diverge across multiple worker processes; there was no visible "why/which
  signal/which agent" trail. All fixed and verified for real (not just written):
  - `chat_service.py` never lets an exception reach the route; drilled this by breaking the Chroma path
    on a cold backend process and confirmed a real `ok:false` friendly-guidance response (HTTP 200, not
    500) — the first attempt at this drill accidentally hit a stale warm process and looked like it
    "worked" without truly testing the exception path; had to kill the actual PID holding the port to
    get a valid cold-start test.
  - `GET /api/alerts` now returns `AlertPage` with real validation (422 on `limit=1000` or `tier=BOGUS`).
  - Narratives persist to `data/outputs/narratives.json` (atomic write) instead of a process-local dict.
  - `AlertDetail` page now shows a `SignalBreakdown` panel (classifier vs DBSCAN weighted contribution)
    between the narrative and the SHAP chart; chat answers show an `AgentBadge` (analyst/investigator/
    reporter) plus source chips.
  - Verified visually with real Playwright screenshots (chromium, zero console errors) of Dashboard,
    Alerts, AlertDetail, Reports, and a live Chat exchange — including confirming chat history survives
    a page reload via `sessionStorage`.
