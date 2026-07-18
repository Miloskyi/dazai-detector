# Spec 06 — MCP Multi-Agent Investigation Chat

## Goal

A chat interface that answers investigator questions **without hallucinating** — every answer must be
traceable to a real tool call (stats computed from data, stored SHAP explanations, or RAG hits), never
to the model's imagination.

## Scope

- `platform/mcp_server/tools/` — pure, side-effect-free functions, the *only* source of truth agents may cite:
  - `alert_tools.py`: `get_alert(alert_id)`, `list_alerts(tier=None, limit=20)`.
  - `stats_tools.py`: `alerts_by_hour()`, `alerts_by_amount_bucket()`, `tier_distribution()`.
  - `rag_tools.py`: thin wrapper over `platform/rag/retriever.AlertRetriever.search`.
- `platform/mcp_server/agents/base.py`
  - `Agent` abstract base: `.name`, `.can_handle(intent) -> bool`, `.respond(question, context) -> str`.
    Every concrete agent's `.respond` must call at least one tool and build its answer only from the
    tool's return value — this is a hard rule, not a suggestion, enforced by review: no agent method
    may format an answer using a number it did not receive from a tool call.
- `platform/mcp_server/agents/router.py`
  - `IntentRouter` (**Router + Factory pattern**): classifies the incoming question into one of 4
    intents via keyword/embedding heuristics (no free-form LLM classification needed — keeps it
    deterministic and explainable in the demo):
    1. `alert_lookup` — mentions an explicit alert ID (`TXN-######`), or a narrow "why was/is/did ...".
    2. `pattern_analysis` — mentions "pattern", "time", "hour", "trend", "amount distribution".
    3. `similar_cases` — mentions "similar", "like this", "related cases".
    4. `report_request` — mentions "summary", "report", "overview", "how many high risk".
    Checked in that priority order (similar_cases and an explicit ID first, generic "why" phrasing
    last) so a word like "flagged" — which shows up across every intent's natural phrasing — never by
    itself misroutes a pattern/report question into alert_lookup. Falls back to `pattern_analysis` (the
    safest, always-answerable intent) if no keyword matches, and the response explicitly says the
    question was interpreted broadly.
  - Instantiates the matching specialist agent (`AnalystAgent`, `InvestigatorAgent`, `ReporterAgent`)
    and dispatches. `dispatch()` returns `{intent, agent, answer, sources}` — `agent` is the specialist's
    name, surfaced end-to-end so the chat UI can show which agent produced each answer (spec 09).
- `platform/mcp_server/agents/analyst.py` (pattern_analysis), `investigator.py` (alert_lookup + similar_cases),
  `reporter.py` (report_request) — each calls only the tools listed above.
- `platform/mcp_server/server.py` — `FastMCP` app exposing the tools in `tools/` as MCP tools, and one
  high-level `investigate(question: str)` tool that runs the full router → agent flow, so any external
  MCP client (not just this project's frontend) can use the same grounded chat.

## Contract

- `platform/backend/services/chat_service.py` imports `IntentRouter` directly — the backend and the
  MCP server share one agent implementation; only the transport differs (REST vs MCP tool call).

## Acceptance criteria

- Each of the 4 predefined question types returns an answer grounded in a real tool call (verifiable by
  reading the answer against `alerts.json`/stats — no invented transaction IDs or numbers).
- A question with no matching alert ID (e.g., a made-up ID) returns an explicit "not found" answer, not
  a fabricated one.
- `fastmcp` server starts and lists its tools (`list_alerts`, `alerts_by_hour`, `search_similar`, ...,
  `investigate`).
