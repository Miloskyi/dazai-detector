"""Answers `report_request` questions with a live summary of high-risk activity."""

from __future__ import annotations

from mcp_server.agents.base import Agent, AgentResponse
from mcp_server.tools import alert_tools, stats_tools

HIGH_RISK_TIERS = {"HIGH", "CRITICAL"}


class ReporterAgent(Agent):
    name = "reporter"

    def respond(self, question: str) -> AgentResponse:
        summary = stats_tools.summary()
        high_risk = [a for a in alert_tools.all_alerts() if a["risk_tier"] in HIGH_RISK_TIERS]
        top = sorted(high_risk, key=lambda a: a["risk_score"], reverse=True)[:5]

        if summary["total_alerts"] == 0:
            return AgentResponse(
                answer="No alerts have been generated yet — run the detection pipeline first.",
                sources=["stats_tools.summary"],
            )

        top_ids = ", ".join(f"{a['id']} (${a['amount']:.2f})" for a in top) or "none"
        answer = (
            f"There are {summary['total_alerts']} total alerts flagging "
            f"${summary['total_flagged_amount']:,.2f}. Tier breakdown: "
            f"{summary['tier_distribution']}. Top high-risk alerts: {top_ids}."
        )
        return AgentResponse(
            answer=answer,
            sources=["stats_tools.summary", "alert_tools.all_alerts"],
        )
