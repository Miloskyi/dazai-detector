"""Builds and stores automatic high-risk reports.

Builder pattern: `ReportBuilder` assembles a `Report` from independent optional
pieces so each piece can be tested/reasoned about on its own.

Runnable standalone: python platform/backend/services/report_service.py
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_PLATFORM_DIR = _PROJECT_ROOT / "platform"
for _p in (_PROJECT_ROOT, _PLATFORM_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from backend.repositories.report_repository import ReportRepository
from backend.services.narrative_service import NarrativeService
from intelligence.pipeline import config
from mcp_server.tools import alert_tools, stats_tools

HIGH_RISK_TIERS = {"HIGH", "CRITICAL"}


@dataclass
class Report:
    generated_at: str
    tier_counts: dict
    total_flagged_amount: float
    top_alerts: list = field(default_factory=list)
    patterns: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at,
            "tier_counts": self.tier_counts,
            "total_flagged_amount": self.total_flagged_amount,
            "top_alerts": self.top_alerts,
            "patterns": self.patterns,
        }

    def to_markdown(self) -> str:
        lines = [
            "# High-Risk Fraud Report",
            f"Generated: {self.generated_at}",
            "",
            "## Summary",
            f"- Total flagged amount: ${self.total_flagged_amount:,.2f}",
        ]
        for tier, count in self.tier_counts.items():
            lines.append(f"- {tier}: {count}")

        lines += ["", "## Top Alerts", "", "| ID | Amount | Tier | Score | Narrative |", "|---|---|---|---|---|"]
        if not self.top_alerts:
            lines.append("| - | - | - | - | No high-risk alerts in this window |")
        for a in self.top_alerts:
            lines.append(
                f"| {a['id']} | ${a['amount']:,.2f} | {a['risk_tier']} | "
                f"{a['risk_score']:.2f} | {a['narrative']} |"
            )

        lines += ["", "## Patterns", "", "**By hour of day:**"]
        for hour, count in self.patterns.get("by_hour", {}).items():
            lines.append(f"- {hour}: {count}")
        lines += ["", "**By amount bucket:**"]
        for bucket, count in self.patterns.get("by_amount_bucket", {}).items():
            lines.append(f"- {bucket}: {count}")

        return "\n".join(lines) + "\n"


class ReportBuilder:
    def __init__(self, narrative_service: NarrativeService | None = None):
        self._narrative_service = narrative_service or NarrativeService()
        self._high_risk: list[dict] = []
        self._tier_counts: dict = {}
        self._total_amount: float = 0.0
        self._patterns: dict = {}
        self._top_alerts: list[dict] = []

    def with_alerts(self) -> "ReportBuilder":
        self._high_risk = [a for a in alert_tools.all_alerts() if a["risk_tier"] in HIGH_RISK_TIERS]
        return self

    def with_summary_stats(self) -> "ReportBuilder":
        self._tier_counts = stats_tools.tier_distribution()
        self._total_amount = sum(a["amount"] for a in self._high_risk)
        self._top_alerts = sorted(self._high_risk, key=lambda a: a["risk_score"], reverse=True)[:5]
        return self

    def with_patterns(self) -> "ReportBuilder":
        self._patterns = {
            "by_hour": stats_tools.alerts_by_hour(),
            "by_amount_bucket": stats_tools.alerts_by_amount_bucket(),
        }
        return self

    def with_narratives(self) -> "ReportBuilder":
        for alert in self._top_alerts:
            alert["narrative"] = self._narrative_service.narrate(alert)
        return self

    def build(self) -> Report:
        return Report(
            generated_at=datetime.now(timezone.utc).isoformat(),
            tier_counts=self._tier_counts,
            total_flagged_amount=round(self._total_amount, 2),
            top_alerts=self._top_alerts,
            patterns=self._patterns,
        )


def generate_report() -> Report:
    return (
        ReportBuilder()
        .with_alerts()
        .with_summary_stats()
        .with_patterns()
        .with_narratives()
        .build()
    )


def main() -> None:
    report = generate_report()
    repo = ReportRepository()
    report_id = f"report_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"
    repo.save(report_id, report.to_dict(), report.to_markdown())
    print(f"Wrote {report_id}.json / .md to {config.REPORTS_DIR}")
    print(f"High-risk alerts in report: {len(report.top_alerts)}")


if __name__ == "__main__":
    main()
