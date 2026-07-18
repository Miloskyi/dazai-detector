"""Produce data/processed/sample.csv.

Uses a stratified sample of the real Kaggle dataset when data/raw/creditcard.csv
is present; otherwise generates a synthetic dataset with the same schema, so the
rest of the platform always has something to run against.
"""

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import numpy as np
import pandas as pd

from intelligence.pipeline import config


def _sample_from_raw() -> pd.DataFrame:
    df = pd.read_csv(config.RAW_DATA_PATH)

    fraud = df[df[config.LABEL_COLUMN] == 1]
    normal = df[df[config.LABEL_COLUMN] == 0]

    normal_budget = max(config.SAMPLE_SIZE - len(fraud), 0)
    normal_sample = normal.sample(
        n=min(normal_budget, len(normal)),
        random_state=config.RANDOM_STATE,
    )

    sample = pd.concat([fraud, normal_sample]).sample(
        frac=1, random_state=config.RANDOM_STATE
    )
    return sample.reset_index(drop=True)


def _generate_synthetic() -> pd.DataFrame:
    rng = np.random.default_rng(config.RANDOM_STATE)
    n_rows = config.SYNTHETIC_ROWS
    n_fraud = max(int(n_rows * config.SYNTHETIC_FRAUD_RATE), 1)
    n_normal = n_rows - n_fraud

    def make_block(n: int, pca_shift: float, amount_scale: float, label: int) -> pd.DataFrame:
        pca_features = rng.normal(loc=pca_shift, scale=1.0, size=(n, 28))
        time = rng.uniform(0, 172_800, size=n)  # 48h window, matches Kaggle's `Time` range
        amount = np.abs(rng.exponential(scale=amount_scale, size=n))

        data = {"Time": time}
        for i in range(28):
            data[f"V{i + 1}"] = pca_features[:, i]
        data["Amount"] = amount
        data[config.LABEL_COLUMN] = label
        return pd.DataFrame(data)

    normal_df = make_block(n_normal, pca_shift=0.0, amount_scale=60.0, label=0)
    fraud_df = make_block(n_fraud, pca_shift=3.5, amount_scale=250.0, label=1)

    df = pd.concat([normal_df, fraud_df]).sample(
        frac=1, random_state=config.RANDOM_STATE
    )
    return df[config.FEATURE_COLUMNS + [config.LABEL_COLUMN]].reset_index(drop=True)


def main() -> None:
    config.PROCESSED_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

    if config.RAW_DATA_PATH.exists():
        print(f"Found raw dataset at {config.RAW_DATA_PATH}, sampling from it.")
        df = _sample_from_raw()
    else:
        print("No raw dataset found, generating a synthetic dataset instead.")
        df = _generate_synthetic()

    df.to_csv(config.PROCESSED_DATA_PATH, index=False)
    fraud_rate = df[config.LABEL_COLUMN].mean() if config.LABEL_COLUMN in df else float("nan")
    print(
        f"Wrote {len(df)} rows to {config.PROCESSED_DATA_PATH} "
        f"(fraud rate: {fraud_rate:.4%})"
    )


if __name__ == "__main__":
    main()
