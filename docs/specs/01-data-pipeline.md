# Spec 01 — Data Pipeline

## Goal

Turn the raw Kaggle Credit Card Fraud dataset (or a synthetic stand-in) into a clean, scaled dataset
ready for both the unsupervised and supervised detectors.

## Scope

- `intelligence/pipeline/config.py`: paths, DBSCAN params (`eps`, `min_samples`), classifier params,
  risk-score weights, tier thresholds. Single source of truth — imported everywhere else.
- `intelligence/pipeline/preprocessing.py`: `Preprocessor` class.
  - `load(path)` — reads CSV, expects columns `Time, V1..V28, Amount, Class` (Class optional at
    inference time).
  - `clean(df)` — drops rows with inf/NaN in numeric columns.
  - `scale(df)` — `StandardScaler` on `Amount` and `Time` (V1–V28 are already PCA-scaled); fitted
    scaler persisted to `intelligence/pipeline/artifacts/scaler.joblib`.
  - `split(df)` — stratified train/score split (default 70/30) when `Class` is present.
- `intelligence/pipeline/make_sample.py`: CLI script.
  - If `data/raw/creditcard.csv` exists, writes a stratified ~20,000-row sample to
    `data/processed/sample.csv` (keeps all fraud rows + a random normal sample) so local dev is fast.
  - If it does not exist, generates a synthetic dataset with the same schema (Gaussian clusters for
    normal transactions, a small injected anomalous cluster for fraud) so the whole platform can run
    with zero external downloads.

## Contract

- Output: `data/processed/sample.csv` with columns `Time, V1..V28, Amount, Class`.
- Anything downstream (`intelligence/pipeline/detectors.py`) reads this file via
  `config.PROCESSED_DATA_PATH` — never a hardcoded string.

## Acceptance criteria

- `python intelligence/pipeline/make_sample.py` runs standalone and always produces a valid CSV, with
  or without the Kaggle file present.
- No NaN/inf values in the output.
- Class imbalance preserved or intentionally documented (synthetic fraud rate ~0.5–2% for the demo,
  close to the real ~0.17% but not so rare that a small sample has zero fraud rows).
