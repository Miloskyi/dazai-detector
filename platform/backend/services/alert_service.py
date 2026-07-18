"""Orchestrates alert retrieval, lazy narrative generation, and signal breakdown."""

from __future__ import annotations

from backend.repositories.alert_repository import AlertRepository
from backend.repositories.narrative_repository import NarrativeRepository
from backend.services.narrative_service import NarrativeService
from intelligence.pipeline import config


def _signal_breakdown(alert: dict) -> dict:
    classifier_contribution = config.CLASSIFIER_WEIGHT * alert["classifier_score"]
    dbscan_contribution = config.DBSCAN_WEIGHT * alert["dbscan_score"]
    return {
        "classifier": {
            "score": alert["classifier_score"],
            "weight": config.CLASSIFIER_WEIGHT,
            "contribution": round(classifier_contribution, 4),
        },
        "dbscan": {
            "score": alert["dbscan_score"],
            "weight": config.DBSCAN_WEIGHT,
            "contribution": round(dbscan_contribution, 4),
        },
        "risk_score": alert["risk_score"],
    }


class AlertService:
    def __init__(self):
        self._repository = AlertRepository()
        self._narrative_repository = NarrativeRepository()
        self._narrative_service = NarrativeService()

    def list(self, tier: str | None = None, limit: int | None = None) -> list[dict]:
        return self._repository.list(tier=tier, limit=limit)

    def page(self, tier: str | None, min_score: float | None, offset: int, limit: int) -> dict:
        items, total = self._repository.page(tier=tier, min_score=min_score, offset=offset, limit=limit)
        return {"items": items, "total": total, "limit": limit, "offset": offset}

    def get_detail(self, alert_id: str) -> dict | None:
        alert = self._repository.get(alert_id)
        if alert is None:
            return None

        narrative = self._narrative_repository.get(alert_id)
        if narrative is None:
            narrative = self._narrative_service.narrate(alert)
            self._narrative_repository.set(alert_id, narrative)

        return {**alert, "narrative": narrative, "signal_breakdown": _signal_breakdown(alert)}
