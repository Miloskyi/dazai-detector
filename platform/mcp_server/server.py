"""FastMCP server exposing grounded fraud-investigation tools.

Any MCP-compatible client (not just this project's own frontend/backend) can
call `investigate` and get the same anti-hallucination guarantee: every
answer is traced back to a tool call over real pipeline output.

Run with: python platform/mcp_server/server.py
"""

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_PLATFORM_DIR = _PROJECT_ROOT / "platform"
for _p in (_PROJECT_ROOT, _PLATFORM_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fastmcp import FastMCP

from mcp_server.agents.router import IntentRouter
from mcp_server.tools import alert_tools, stats_tools
from mcp_server.tools.rag_tools import search_similar as _search_similar

mcp = FastMCP("dazai-fraud-detector")
_router = IntentRouter()


@mcp.tool()
def list_alerts(tier: str | None = None, limit: int = 20) -> list[dict]:
    """List fraud alerts, optionally filtered by risk tier (LOW/MEDIUM/HIGH/CRITICAL)."""
    return alert_tools.list_alerts(tier=tier, limit=limit)


@mcp.tool()
def get_alert(alert_id: str) -> dict | None:
    """Fetch one alert by its transaction ID, e.g. TXN-000123."""
    return alert_tools.get_alert(alert_id)


@mcp.tool()
def alerts_by_hour() -> dict:
    """Count of flagged alerts grouped by hour of day."""
    return stats_tools.alerts_by_hour()


@mcp.tool()
def alerts_by_amount_bucket() -> dict:
    """Count of flagged alerts grouped by transaction amount bucket."""
    return stats_tools.alerts_by_amount_bucket()


@mcp.tool()
def tier_distribution() -> dict:
    """Count of alerts per risk tier."""
    return stats_tools.tier_distribution()


@mcp.tool()
def search_similar(query: str, k: int = 5, tier_filter: str | None = None) -> list[dict]:
    """Semantic search over past alert narratives using the ChromaDB RAG store."""
    return _search_similar(query, k=k, tier_filter=tier_filter)


@mcp.tool()
def investigate(question: str) -> dict:
    """Answer a free-form fraud investigation question, grounded in real tool calls.

    Routes the question through the intent router to one of: alert lookup,
    similar-case search, pattern analysis, or report summary.
    """
    return _router.dispatch(question)


if __name__ == "__main__":
    import os

    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport == "stdio":
        mcp.run()
    else:
        mcp.run(
            transport=transport,
            host=os.getenv("MCP_HOST", "0.0.0.0"),
            port=int(os.getenv("MCP_PORT", "8001")),
        )
