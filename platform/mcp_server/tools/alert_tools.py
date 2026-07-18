"""Grounded, side-effect-free access to alerts.json.

This is the single place that reads the alerts file. Every agent and every
backend route that needs alert data goes through these functions — never
through a direct file open elsewhere.
"""

from __future__ import annotations

import json

from intelligence.pipeline import config

_cache: list[dict] | None = None


def _load() -> list[dict]:
    global _cache
    if _cache is None:
        reload()
    return _cache


def reload() -> list[dict]:
    """Force a re-read from disk (call after re-running the pipeline)."""
    global _cache
    if config.ALERTS_PATH.exists():
        with open(config.ALERTS_PATH) as f:
            _cache = json.load(f)
    else:
        _cache = []
    return _cache


def _filtered(tier: str | None, min_score: float | None) -> list[dict]:
    alerts = _load()
    if tier:
        alerts = [a for a in alerts if a["risk_tier"] == tier.upper()]
    if min_score is not None:
        alerts = [a for a in alerts if a["risk_score"] >= min_score]
    return sorted(alerts, key=lambda a: a["risk_score"], reverse=True)


def list_alerts(tier: str | None = None, limit: int | None = 20) -> list[dict]:
    alerts = _filtered(tier, None)
    return alerts[:limit] if limit else alerts


def page_alerts(
    tier: str | None, min_score: float | None, offset: int, limit: int
) -> tuple[list[dict], int]:
    alerts = _filtered(tier, min_score)
    return alerts[offset : offset + limit], len(alerts)


def get_alert(alert_id: str) -> dict | None:
    return next((a for a in _load() if a["id"] == alert_id), None)


def all_alerts() -> list[dict]:
    return _load()
