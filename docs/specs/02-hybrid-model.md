# Spec 02 — Hybrid Model (DBSCAN + Supervised)

## Goal

Combine an unsupervised anomaly signal with a supervised classifier into one calibrated risk score per
transaction.

## Scope

- `intelligence/pipeline/detectors.py`
  - `AnomalyDetector` (abstract base, **Strategy pattern**): `.fit(X)`, `.score(X) -> np.ndarray in [0,1]`.
  - `DBSCANDetector(AnomalyDetector)`: fits `sklearn.cluster.DBSCAN(eps, min_samples)` on the scoring
    window; label `-1` (noise) → score `1.0`, clustered → score `0.0`. DBSCAN has no incremental
    `predict`, so it is refit per scoring batch — this is documented, not hidden.
  - `SupervisedDetector(AnomalyDetector)`: wraps `xgboost.XGBClassifier` with `scale_pos_weight` set
    from the training class ratio (compensates the ~0.17%–2% imbalance). `.fit` trains on labeled data;
    `.score` returns `predict_proba[:, 1]`.
- `intelligence/pipeline/hybrid.py`
  - `HybridFraudDetector` (**Facade pattern**): owns one `DBSCANDetector` + one `SupervisedDetector`.
    - `.fit(train_df)` — fits the supervised model on labels; DBSCAN needs no fit-time labels.
    - `.score(df) -> DataFrame` — runs both, computes
      `risk_score = config.CLASSIFIER_WEIGHT * clf_score + config.DBSCAN_WEIGHT * dbscan_score`,
      maps to a tier via `config.RISK_TIERS` (LOW < MEDIUM < HIGH < CRITICAL cutoffs).
- `intelligence/pipeline/run_pipeline.py`: CLI.
  1. Load `data/processed/sample.csv` via `Preprocessor`.
  2. `HybridFraudDetector().fit(train)`; persist the XGBoost model to `artifacts/classifier.joblib`.
  3. Score the held-out split; keep only rows above `config.ALERT_THRESHOLD`.
  4. Emit `data/outputs/alerts.json`: list of
     `{id, timestamp, amount, risk_score, risk_tier, dbscan_score, classifier_score, features: {...}}`.

## Contract

- `alerts.json` is the single artifact every downstream spec (explainability, reports, RAG, backend)
  reads. Its schema (above) must not change without updating all consumers.

## Acceptance criteria

- `python intelligence/pipeline/run_pipeline.py` runs end-to-end on the spec-01 sample and writes a
  non-empty `alerts.json`.
- Every alert has `risk_score` in `[0, 1]` and a valid `risk_tier`.
- PR-AUC / precision-recall reported to stdout for sanity (not a hard gate, informative for the demo).
