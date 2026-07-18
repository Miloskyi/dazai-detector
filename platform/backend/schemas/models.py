"""Pydantic schemas — every route response is one of these, nothing else."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ShapFeature(BaseModel):
    feature: str
    value: float
    shap_value: float
    direction: str


class Alert(BaseModel):
    id: str
    timestamp: str
    amount: float
    risk_score: float
    risk_tier: str
    dbscan_score: float
    classifier_score: float


class SignalComponent(BaseModel):
    score: float
    weight: float
    contribution: float


class SignalBreakdown(BaseModel):
    classifier: SignalComponent
    dbscan: SignalComponent
    risk_score: float


class AlertDetail(Alert):
    features: dict[str, float]
    shap_explanation: list[ShapFeature]
    narrative: str
    signal_breakdown: SignalBreakdown


class AlertPage(BaseModel):
    items: list[Alert]
    total: int
    limit: int
    offset: int


class StatsSummary(BaseModel):
    total_alerts: int
    total_flagged_amount: float
    tier_distribution: dict[str, int]
    by_hour: dict[str, int]
    by_amount_bucket: dict[str, int]


class TopAlert(BaseModel):
    id: str
    amount: float
    risk_score: float
    risk_tier: str
    narrative: str


class Report(BaseModel):
    generated_at: str
    tier_counts: dict[str, int]
    total_flagged_amount: float
    top_alerts: list[TopAlert]
    patterns: dict


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class ChatResponse(BaseModel):
    answer: str
    intent: str
    agent: str
    sources: list[str]
    ok: bool = True
