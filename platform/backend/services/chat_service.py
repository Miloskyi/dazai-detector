"""Backend entry point into the shared multi-agent chat.

The backend and the MCP server both call `IntentRouter` directly — one agent
implementation, two transports (REST here, MCP tool call in `mcp_server/server.py`).

This layer is the one place responsible for turning any failure — a blank
question, a tool exploding, RAG/Chroma being unreachable — into a friendly,
demo-safe answer instead of a raw 500. The router/agents/tools are trusted to
raise on bad state; this is the boundary that catches it.
"""

from __future__ import annotations

SUPPORTED_QUESTIONS = (
    "Why was a specific alert flagged? (mention its ID, e.g. TXN-000123)",
    "What time/amount patterns exist across flagged transactions?",
    "Which past cases are similar to a given alert?",
    "Can you summarize current high-risk activity?",
)

_FALLBACK_ANSWER = (
    "I couldn't answer that from the data I have. Try one of these instead:\n- "
    + "\n- ".join(SUPPORTED_QUESTIONS)
)


class ChatService:
    def __init__(self):
        # Imported lazily so a broken agent/tool import surfaces as a clean
        # fallback on first use rather than crashing the whole backend at
        # startup.
        from mcp_server.agents.router import IntentRouter

        self._router = IntentRouter()

    def ask(self, question: str) -> dict:
        if not question or not question.strip():
            return self._fallback()

        try:
            return self._router.dispatch(question)
        except Exception:
            return self._fallback()

    def _fallback(self) -> dict:
        return {
            "intent": "fallback",
            "agent": "system",
            "answer": _FALLBACK_ANSWER,
            "sources": [],
            "ok": False,
        }
