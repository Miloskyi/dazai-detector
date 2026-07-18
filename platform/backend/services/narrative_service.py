"""Generates a plain-language narrative for one alert from its SHAP explanation."""

from __future__ import annotations

import json

from backend.services.llm.provider import LLMProvider, TemplateNarrativeProvider, build_default_provider


class NarrativeService:
    def __init__(self, provider: LLMProvider | None = None):
        self.provider = provider or build_default_provider()
        self._fallback = TemplateNarrativeProvider()

    def narrate(self, alert: dict) -> str:
        context = {
            "amount": alert["amount"],
            "risk_tier": alert["risk_tier"],
            "risk_score": alert["risk_score"],
            "shap_explanation": alert.get("shap_explanation", []),
        }
        prompt = json.dumps(context)

        try:
            return self.provider.generate(prompt)
        except Exception:
            # Any failure (no key, network, quota, timeout) must never break the demo.
            return self._fallback.generate(prompt)
