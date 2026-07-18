from fastapi import APIRouter

from backend.schemas.models import StatsSummary
from backend.services.stats_service import StatsService

router = APIRouter(prefix="/stats", tags=["stats"])
_service = StatsService()


@router.get("", response_model=StatsSummary)
def get_stats():
    return _service.summary()
