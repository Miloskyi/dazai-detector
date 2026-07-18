"""Cleaning, scaling and splitting for the fraud dataset."""

from __future__ import annotations

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from intelligence.pipeline import config


class Preprocessor:
    """Loads raw transaction data and prepares it for both detectors.

    V1-V28 arrive already PCA-scaled from the source dataset; only `Amount` and
    `Time` need standardization here.
    """

    def __init__(self) -> None:
        self._scaler: StandardScaler | None = None

    def load(self, path=None) -> pd.DataFrame:
        path = path or config.PROCESSED_DATA_PATH
        return pd.read_csv(path)

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        numeric_cols = [c for c in df.columns if c in config.FEATURE_COLUMNS]
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.dropna(subset=numeric_cols)
        return df.reset_index(drop=True)

    def scale(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        df = df.copy()
        scale_cols = ["Time", "Amount"]

        # Keep the original dollar/second values for display (reports, narratives,
        # frontend) — only the *_raw-free columns feed the model as z-scores.
        df["Time_raw"] = df["Time"]
        df["Amount_raw"] = df["Amount"]

        if fit or self._scaler is None:
            self._scaler = StandardScaler()
            df[scale_cols] = self._scaler.fit_transform(df[scale_cols])
            config.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
            joblib.dump(self._scaler, config.SCALER_PATH)
        else:
            df[scale_cols] = self._scaler.transform(df[scale_cols])

        return df

    def load_scaler(self) -> StandardScaler:
        if self._scaler is None:
            self._scaler = joblib.load(config.SCALER_PATH)
        return self._scaler

    def split(self, df: pd.DataFrame):
        stratify = df[config.LABEL_COLUMN] if config.LABEL_COLUMN in df.columns else None
        return train_test_split(
            df,
            test_size=config.TEST_SIZE,
            random_state=config.RANDOM_STATE,
            stratify=stratify,
        )

    def prepare(self, path=None):
        """Convenience pipeline: load -> clean -> scale -> split."""
        df = self.load(path)
        df = self.clean(df)
        df = self.scale(df, fit=True)
        return self.split(df)
