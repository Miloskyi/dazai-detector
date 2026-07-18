"""Backend-facing view over alert data.

Repository pattern: the backend's services only ever go through this class,
never through `mcp_server.tools.alert_tools` directly — this is the seam that
would let the backend switch storage later without touching any route/service.
"""

from __future__ import annotations

from mcp_server.tools import alert_tools


class AlertRepository:
    def list(self, tier: str | None = None, limit: int | None = None) -> list[dict]:
        return alert_tools.list_alerts(tier=tier, limit=limit)

    def page(
        self, tier: str | None, min_score: float | None, offset: int, limit: int
    ) -> tuple[list[dict], int]:
        return alert_tools.page_alerts(tier=tier, min_score=min_score, offset=offset, limit=limit)

    def get(self, alert_id: str) -> dict | None:
        return alert_tools.get_alert(alert_id)

    def all(self) -> list[dict]:
        return alert_tools.all_alerts()
