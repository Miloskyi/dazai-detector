"""LLM provider adapter.

Adapter pattern: `NarrativeService` only ever calls `.generate(prompt)`. Which
concrete provider runs behind it (a real LLM API, or a deterministic template)
is decided once, at startup, from environment configuration.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import httpx

from intelligence.pipeline import config


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        ...


class OpenAICompatibleProvider(LLMProvider):
    """Calls any OpenAI-compatible chat completions endpoint."""

    def __init__(self, api_key: str, model: str, base_url: str):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    def generate(self, prompt: str) -> str:
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a fraud analyst assistant. Explain, in one short "
                            "paragraph, why a transaction was flagged, using only the "
                            "facts given. Do not invent numbers."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 200,
            },
            timeout=15.0,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()


class TemplateNarrativeProvider(LLMProvider):
    """Deterministic, offline narrative builder — the default and the fallback.

    `prompt` is expected to be the JSON-serialized alert context produced by
    `NarrativeService._build_prompt`; this provider does not call any external
    service, so the demo always has a working narrative.
    """

    def generate(self, prompt: str) -> str:
        import json

        context = json.loads(prompt)
        amount = context["amount"]
        tier = context["risk_tier"]
        top_features = context["shap_explanation"][:2]

        if not top_features:
            return (
                f"This transaction of ${amount:,.2f} was flagged {tier} by the hybrid "
                "risk model, with no single dominant feature."
            )

        feature_phrases = [
            f"{f['feature']} ({f['value']:.2f}, which {f['direction']} the risk score)"
            for f in top_features
        ]
        joined = " and ".join(feature_phrases)
        return (
            f"This transaction of ${amount:,.2f} was flagged {tier} mainly because "
            f"{joined}."
        )


def build_default_provider() -> LLMProvider:
    if config.LLM_PROVIDER == "none" or not config.LLM_API_KEY:
        return TemplateNarrativeProvider()
    return OpenAICompatibleProvider(
        api_key=config.LLM_API_KEY,
        model=config.LLM_MODEL,
        base_url=config.LLM_BASE_URL,
    )
