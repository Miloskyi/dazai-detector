from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from backend.schemas.models import AlertDetail, AlertPage
from backend.services.alert_service import AlertService
from intelligence.pipeline import config

router = APIRouter(prefix="/alerts", tags=["alerts"])
_service = AlertService()

RiskTier = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


@router.get("", response_model=AlertPage)
def list_alerts(
    tier: RiskTier | None = None,
    min_score: float | None = Query(default=None, ge=0.0, le=1.0),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=config.ALERTS_DEFAULT_LIMIT, ge=1, le=config.ALERTS_MAX_LIMIT),
):
    return _service.page(tier=tier, min_score=min_score, offset=offset, limit=limit)


@router.get("/{alert_id}", response_model=AlertDetail)
def get_alert(alert_id: str):
    alert = _service.get_detail(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    return alert
