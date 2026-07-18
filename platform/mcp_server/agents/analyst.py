"""Answers `pattern_analysis` questions using real aggregate statistics."""

from __future__ import annotations

from mcp_server.agents.base import Agent, AgentResponse
from mcp_server.tools import stats_tools


class AnalystAgent(Agent):
    name = "analyst"

    def respond(self, question: str) -> AgentResponse:
        by_hour = stats_tools.alerts_by_hour()
        by_amount = stats_tools.alerts_by_amount_bucket()
        tiers = stats_tools.tier_distribution()

        if not by_hour and not by_amount:
            return AgentResponse(
                answer="No alerts are available yet to analyze patterns from.",
                sources=["stats_tools.alerts_by_hour", "stats_tools.alerts_by_amount_bucket"],
            )

        peak_hour = max(by_hour, key=by_hour.get) if by_hour else "unknown"
        peak_bucket = max(by_amount, key=by_amount.get) if by_amount else "unknown"

        answer = (
            f"The busiest flagged hour is {peak_hour} with {by_hour.get(peak_hour, 0)} alerts. "
            f"The most common flagged amount range is {peak_bucket} "
            f"({by_amount.get(peak_bucket, 0)} alerts). "
            f"Tier distribution: {tiers}."
        )
        return AgentResponse(
            answer=answer,
            sources=["stats_tools.alerts_by_hour", "stats_tools.alerts_by_amount_bucket", "stats_tools.tier_distribution"],
        )
