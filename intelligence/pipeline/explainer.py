"""Per-transaction SHAP explanations for the supervised detector."""

from __future__ import annotations

import numpy as np
import pandas as pd
import shap

from intelligence.pipeline import config


class ShapExplainer:
    """Wraps shap.TreeExplainer around a fitted XGBoost model."""

    def __init__(self, model, top_n: int = config.SHAP_TOP_N):
        self._explainer = shap.TreeExplainer(model)
        self.top_n = top_n

    def explain(self, X: pd.DataFrame) -> list[list[dict]]:
        """Returns, per row, the top-N features by absolute SHAP impact."""
        if len(X) == 0:
            return []

        shap_values = self._explainer.shap_values(X)
        if isinstance(shap_values, list):
            shap_values = shap_values[-1]  # binary classification: positive class

        explanations = []
        for row_idx in range(len(X)):
            row_values = shap_values[row_idx]
            row_features = X.iloc[row_idx]

            order = np.argsort(-np.abs(row_values))[: self.top_n]
            explanations.append(
                [
                    {
                        "feature": X.columns[i],
                        "value": round(float(row_features.iloc[i]), 4),
                        "shap_value": round(float(row_values[i]), 4),
                        "direction": "increases" if row_values[i] > 0 else "decreases",
                    }
                    for i in order
                ]
            )
        return explanations
