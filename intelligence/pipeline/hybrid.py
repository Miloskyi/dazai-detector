"""Fuses the unsupervised and supervised signals into one risk score.

Facade pattern: callers only ever see `.fit()` / `.score()`, never the two
underlying detectors.
"""

from __future__ import annotations

import pandas as pd

from intelligence.pipeline import config
from intelligence.pipeline.detectors import DBSCANDetector, SupervisedDetector


class HybridFraudDetector:
    def __init__(self):
        self.dbscan = DBSCANDetector()
        self.classifier = SupervisedDetector()

    def fit(self, train_df: pd.DataFrame) -> "HybridFraudDetector":
        X = train_df[config.FEATURE_COLUMNS]
        y = train_df[config.LABEL_COLUMN]
        self.classifier.fit(X, y)
        self.dbscan.fit(X)
        return self

    def score(self, df: pd.DataFrame) -> pd.DataFrame:
        X = df[config.FEATURE_COLUMNS]

        classifier_score = self.classifier.score(X)
        dbscan_score = self.dbscan.score(X)

        risk_score = (
            config.CLASSIFIER_WEIGHT * classifier_score
            + config.DBSCAN_WEIGHT * dbscan_score
        )

        result = df.copy()
        result["classifier_score"] = classifier_score
        result["dbscan_score"] = dbscan_score
        result["risk_score"] = risk_score
        result["risk_tier"] = [config.risk_tier_for(s) for s in risk_score]
        return result
