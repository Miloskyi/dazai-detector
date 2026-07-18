# Spec 03 — Explainability (SHAP + Narrative)

## Goal

For every alert, surface *which features drove the decision* and turn that into a one-paragraph
plain-language explanation an investigator can read without knowing what SHAP is.

## Scope

- `intelligence/pipeline/explainer.py`
  - `ShapExplainer` wraps `shap.TreeExplainer` around the fitted `SupervisedDetector`'s XGBoost model.
  - `.explain(df, top_n=5) -> list[dict]` — per row, returns the top-N features by `|shap_value|`:
    `[{feature, value, shap_value, direction: "increases"|"decreases"}]`.
  - Called from `run_pipeline.py` right after scoring; results attached to each alert as
    `alert["shap_explanation"]`.
- `platform/backend/services/llm/`
  - `LLMProvider` (abstract, **Adapter pattern**): `.generate(prompt: str) -> str`.
  - `OpenAICompatibleProvider(LLMProvider)`: calls the configured LLM API (env: `LLM_PROVIDER`,
    `LLM_API_KEY`, `LLM_MODEL`). Any OpenAI-compatible endpoint works — provider is swappable.
  - `TemplateNarrativeProvider(LLMProvider)`: **no external call**; renders a deterministic sentence
    template from the SHAP explanation, e.g. *"This transaction of $X was flagged CRITICAL mainly
    because Amount ($X) and V14 (-2.31) pushed the risk score up."* Used automatically when no API key
    is configured, so the demo works offline.
- `platform/backend/services/narrative_service.py`
  - `NarrativeService(provider: LLMProvider)` — builds the prompt from `shap_explanation` + alert
    metadata, calls `provider.generate`, falls back to `TemplateNarrativeProvider` on any exception
    (timeout, quota, network) so a flaky API never breaks the demo.

## Contract

- Each alert gains `shap_explanation` (list, from the pipeline) and `narrative` (string, generated
  lazily by the backend on first request, then cached in the repository).

## Acceptance criteria

- SHAP explanation features are real feature names from the training set, ordered by absolute impact.
- Narrative generation works with **zero** configured API key (template fallback) and improves in
  quality when a real key is set — no code change required to switch.
