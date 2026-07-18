# Spec 07 — Backend API

## Goal

Expose everything built so far as a REST API the frontend (and any other client) can consume.

## Scope

- `platform/backend/schemas/` — Pydantic models: `Alert`, `AlertDetail` (adds `shap_explanation`,
  `narrative`, `signal_breakdown` — see spec 09), `AlertPage` (`items, total, limit, offset`), `Report`,
  `ChatRequest`/`ChatResponse`, `StatsSummary`.
- `platform/backend/repositories/`
  - `AlertRepository` (**Repository pattern**): exposes `.list(tier=None, limit=None)`,
    `.page(tier, min_score, offset, limit)`, `.get(alert_id)`. Single place the backend touches alert
    data (delegates to `mcp_server.tools.alert_tools`, the actual single reader of `alerts.json`).
  - `NarrativeRepository` (spec 09): persists generated narratives to `data/outputs/narratives.json`.
  - `ReportRepository`: reused from spec 04.
- `platform/backend/services/`
  - `alert_service.py`: orchestrates `AlertRepository` + `NarrativeRepository` + `NarrativeService`
    (generates once, persists, reuses on every later request) and computes `signal_breakdown`.
  - `report_service.py`: reused from spec 04, exposed via service layer.
  - `chat_service.py`: wraps spec 06's `IntentRouter`; never lets an exception or blank question reach
    the route — see spec 09's fallback contract below.
- `platform/backend/api/routes/`
  - `alerts.py`: `GET /api/alerts` (validated `tier`/`limit`/`offset`/`min_score`, returns `AlertPage`),
    `GET /api/alerts/{id}`.
  - `stats.py`: `GET /api/stats` (tier distribution, totals, time patterns — backs the dashboard KPIs).
  - `reports.py`: `GET /api/reports/latest`, `GET /api/reports/latest/markdown`, `POST
    /api/reports/generate`.
  - `chat.py`: `POST /api/chat` — `{question: str} -> {answer, intent, agent, sources, ok}`.
- `platform/backend/main.py` — FastAPI app, CORS enabled for the Vite dev origin, mounts all routers
  under `/api`, root health check at `/`. Runnable directly with `python platform/backend/main.py`
  (calls `uvicorn.run(...)` in `if __name__ == "__main__"`) so no dotted module path is required.

## Contract

- All routes return the Pydantic schemas above — the frontend never parses a raw dict shape that isn't
  documented here.
- `GET /api/alerts` validates `tier` (must be one of the 4 tiers), `limit` (1–100), `offset` (>=0),
  `min_score` (0–1) — invalid values are a 422, never silently clamped or ignored.
- `ChatResponse.sources` lists which tool(s)/alert ID(s) grounded the answer, so the frontend can show
  "based on: Alert #4231" next to the chat answer (visual proof of no hallucination — good for the demo).
  `ChatResponse.agent` names which specialist answered; `ok:false` means the router/agents could not
  produce a grounded answer and the frontend is showing generic guidance, not a real answer — this is a
  deliberate degraded state, never an unhandled exception.

## Acceptance criteria

- `python platform/backend/main.py` starts the server cleanly.
- Every route in `docs/specs/07-backend-api.md` responds with the documented schema against the
  artifacts produced by specs 01–06.
- `POST /api/chat` answers all 4 predefined question types with a non-empty `sources` list and the
  correct `agent`; an empty question is a 422; a broken downstream tool still returns HTTP 200 with
  `ok:false` (never a 500).
- `GET /api/alerts?limit=1000` or `?tier=BOGUS` is a 422.
