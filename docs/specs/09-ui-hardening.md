# Spec 09 — UI Hardening & Explainability Panels

## Goal

Close the gaps between "works" and "demo-ready": a generic-looking dashboard, a chat that leaks raw
errors, an unbounded alerts endpoint, an in-memory-only narrative cache, and no visible "why/who
answered" trail for the chat.

## Scope

- **Visual theme** (`platform/frontend`): dark near-black background, violet accent, pill badges,
  card-based layout with a left sidebar — modeled after a reference SaaS dashboard design. New shared
  components: `StatCard`, `TypingIndicator`, `EmptyState`, `AgentBadge`, `SignalBreakdown`. `Sidebar`
  replaces the old top `NavBar`.
- **Chat robustness**:
  - `mcp_server/agents/router.py` — `IntentRouter.dispatch` now also returns `agent` (the specialist's
    name), so both the backend and any MCP client can show which agent answered.
  - `backend/services/chat_service.py` — never lets an exception reach the route. A blank/whitespace
    question or any tool/router failure returns a friendly `ok:false` payload listing the 4 supported
    question types instead of a 500.
  - `backend/schemas/models.py` — `ChatRequest.question` bounded (1–500 chars, 422 on empty);
    `ChatResponse` gains `agent: str` and `ok: bool`.
  - Frontend `Chat.tsx` — history persisted in `sessionStorage`, typing indicator while waiting, a
    distinct failed-message bubble with Retry, agent badge + source chips per answer.
- **Alerts pagination + validation**:
  - `mcp_server/tools/alert_tools.py` — `page_alerts(tier, min_score, offset, limit)` alongside the
    existing `list_alerts` (still used by agents/MCP tools).
  - `backend/repositories/alert_repository.py` — `page(...)` wrapper.
  - `backend/api/routes/alerts.py` — `GET /api/alerts` validates `tier` against the 4 known tiers,
    `limit` (1–100, default 25), `offset` (>=0), optional `min_score` (0–1); returns `AlertPage`
    (`items, total, limit, offset`) instead of a bare list.
- **Persistent narrative cache**:
  - `backend/repositories/narrative_repository.py` — narratives stored at `data/outputs/narratives.json`
    (atomic write via tmp file + `os.replace`), read/written by `alert_service.get_detail` instead of a
    module-level dict. Safe across multiple worker processes; a rare concurrent regeneration is
    harmless since the template fallback is deterministic.
- **Explainability panel**:
  - `alert_service.get_detail` computes `signal_breakdown`:
    `{classifier: {score, weight, contribution}, dbscan: {...}, risk_score}` from the alert's stored
    scores and `config.CLASSIFIER_WEIGHT`/`DBSCAN_WEIGHT` — no new model inference, just surfacing the
    existing fusion math. `AlertDetail.tsx` renders it as a labeled two-bar breakdown between the
    narrative and the SHAP chart.

## Contract changes

- `GET /api/alerts` response shape changed from `list[Alert]` to `AlertPage`. The only consumer is this
  project's own frontend, updated in the same change.
- `POST /api/chat` response gains `agent` and `ok` — additive, does not break existing consumers.
- `AlertDetail` gains `signal_breakdown` — additive.

## Acceptance criteria

- `GET /api/alerts?limit=1000` and `?tier=BOGUS` return 422; a valid paginated request returns
  `{items, total, limit, offset}` with `len(items) <= limit`.
- `POST /api/chat` with an empty question returns 422; a question that would normally raise (e.g. the
  RAG store being unreachable) returns HTTP 200 with `ok:false` and the 4-question guidance text — never
  a 500.
- Two consecutive `GET /api/alerts/{id}` calls produce the identical narrative and only one entry is
  written to `narratives.json`.
- Chat history in the frontend survives a page reload (verified via `sessionStorage`); a network
  failure shows a Retry button that resends the last question.
- `AlertDetail` page shows three explanation cards in order: narrative, signal breakdown (classifier vs
  DBSCAN weighted contribution), SHAP feature impact.
