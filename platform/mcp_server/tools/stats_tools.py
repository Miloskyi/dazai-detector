"""Aggregate statistics over alerts — the single implementation used by both
the automatic report builder and the pattern-analysis chat agent.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime

from mcp_server.tools import alert_tools


def tier_distribution() -> dict[str, int]:
    alerts = alert_tools.all_alerts()
    return dict(Counter(a["risk_tier"] for a in alerts))


def alerts_by_hour() -> dict[str, int]:
    alerts = alert_tools.all_alerts()
    counts: Counter[str] = Counter()
    for a in alerts:
        hour = datetime.fromisoformat(a["timestamp"]).strftime("%H:00")
        counts[hour] += 1
    return dict(sorted(counts.items()))


def alerts_by_amount_bucket() -> dict[str, int]:
    buckets = [
        (0, 50, "$0-50"),
        (50, 200, "$50-200"),
        (200, 1000, "$200-1000"),
        (1000, float("inf"), "$1000+"),
    ]
    counts = {label: 0 for *_range, label in buckets}
    for a in alert_tools.all_alerts():
        amount = a["amount"]
        for low, high, label in buckets:
            if low <= amount < high:
                counts[label] += 1
                break
    return counts


def summary() -> dict:
    alerts = alert_tools.all_alerts()
    total_amount = sum(a["amount"] for a in alerts)
    return {
        "total_alerts": len(alerts),
        "total_flagged_amount": round(total_amount, 2),
        "tier_distribution": tier_distribution(),
    }
