"""Anomaly detection strategies.

Both detectors share the same `AnomalyDetector` interface (Strategy pattern) so
`HybridFraudDetector` can fuse their scores without knowing how each one works
internally.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from xgboost import XGBClassifier

from intelligence.pipeline import config


class AnomalyDetector(ABC):
    """Common interface for any fraud signal source."""

    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series | None = None) -> "AnomalyDetector":
        ...

    @abstractmethod
    def score(self, X: pd.DataFrame) -> np.ndarray:
        """Return a fraud-likelihood score per row, in [0, 1]."""
        ...


class DBSCANDetector(AnomalyDetector):
    """Flags density outliers as likely fraud.

    DBSCAN has no `predict` for unseen points, so it is refit on every scoring
    batch: this is a batch anomaly signal, not an online classifier.
    """

    def __init__(self, eps: float = config.DBSCAN_EPS, min_samples: int = config.DBSCAN_MIN_SAMPLES):
        self.eps = eps
        self.min_samples = min_samples

    def fit(self, X: pd.DataFrame, y: pd.Series | None = None) -> "DBSCANDetector":
        # No persistent state to fit — DBSCAN is refit per batch in `score`.
        return self

    def score(self, X: pd.DataFrame) -> np.ndarray:
        labels = DBSCAN(eps=self.eps, min_samples=self.min_samples).fit_predict(X.values)
        return np.where(labels == -1, 1.0, 0.0)


class SupervisedDetector(AnomalyDetector):
    """XGBoost classifier trained on labeled fraud examples."""

    def __init__(self):
        self._model: XGBClassifier | None = None

    def fit(self, X: pd.DataFrame, y: pd.Series | None = None) -> "SupervisedDetector":
        if y is None:
            raise ValueError("SupervisedDetector.fit requires labels")

        positive = int(y.sum())
        negative = int(len(y) - positive)
        scale_pos_weight = (negative / positive) if positive else 1.0

        self._model = XGBClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.1,
            scale_pos_weight=scale_pos_weight,
            eval_metric="aucpr",
            random_state=config.RANDOM_STATE,
        )
        self._model.fit(X, y)
        return self

    def score(self, X: pd.DataFrame) -> np.ndarray:
        if self._model is None:
            raise RuntimeError("SupervisedDetector must be fit before scoring")
        return self._model.predict_proba(X)[:, 1]

    @property
    def model(self) -> XGBClassifier:
        if self._model is None:
            raise RuntimeError("SupervisedDetector must be fit before accessing the model")
        return self._model
