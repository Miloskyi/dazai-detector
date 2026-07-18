"""Backs the dashboard KPIs — thin wrapper over the shared stats tools."""

from __future__ import annotations

from mcp_server.tools import stats_tools


class StatsService:
    def summary(self) -> dict:
        base = stats_tools.summary()
        return {
            **base,
            "by_hour": stats_tools.alerts_by_hour(),
            "by_amount_bucket": stats_tools.alerts_by_amount_bucket(),
        }
