"""End-to-end CLI: preprocess -> fit hybrid model -> score -> explain -> emit alerts.json.

Run with: python intelligence/pipeline/run_pipeline.py
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import joblib
from sklearn.metrics import average_precision_score, precision_score, recall_score

from intelligence.pipeline import config
from intelligence.pipeline.explainer import ShapExplainer
from intelligence.pipeline.hybrid import HybridFraudDetector
from intelligence.pipeline.preprocessing import Preprocessor

_DEMO_EPOCH = datetime(2024, 1, 1, tzinfo=timezone.utc)


def _to_timestamp(time_offset_seconds: float) -> str:
    return (_DEMO_EPOCH + timedelta(seconds=float(time_offset_seconds))).isoformat()


def _build_alert(row, explanation: list[dict]) -> dict:
    return {
        "id": f"TXN-{int(row.name):06d}",
        "timestamp": _to_timestamp(row["Time_raw"]),
        "amount": round(float(row["Amount_raw"]), 2),
        "risk_score": round(float(row["risk_score"]), 4),
        "risk_tier": row["risk_tier"],
        "dbscan_score": round(float(row["dbscan_score"]), 4),
        "classifier_score": round(float(row["classifier_score"]), 4),
        "features": {col: float(row[col]) for col in config.FEATURE_COLUMNS},
        "shap_explanation": explanation,
    }


def main() -> None:
    preprocessor = Preprocessor()
    train_df, score_df = preprocessor.prepare()

    print(f"Train rows: {len(train_df)} | Score rows: {len(score_df)}")

    model = HybridFraudDetector().fit(train_df)

    config.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model.classifier.model, config.CLASSIFIER_PATH)

    scored_df = model.score(score_df)

    if config.LABEL_COLUMN in scored_df.columns:
        y_true = scored_df[config.LABEL_COLUMN]
        y_pred = (scored_df["risk_score"] >= config.ALERT_THRESHOLD).astype(int)
        pr_auc = average_precision_score(y_true, scored_df["risk_score"])
        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)
        print(f"PR-AUC: {pr_auc:.4f} | Precision@{config.ALERT_THRESHOLD}: {precision:.4f} | Recall: {recall:.4f}")

    alerted_df = scored_df[scored_df["risk_score"] >= config.ALERT_THRESHOLD].copy()
    print(f"Alerts above threshold {config.ALERT_THRESHOLD}: {len(alerted_df)}")

    explainer = ShapExplainer(model.classifier.model)
    explanations = explainer.explain(alerted_df[config.FEATURE_COLUMNS])

    alerts = [
        _build_alert(row, explanations[i])
        for i, (_, row) in enumerate(alerted_df.iterrows())
    ]

    config.ALERTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(config.ALERTS_PATH, "w") as f:
        json.dump(alerts, f, indent=2)

    print(f"Wrote {len(alerts)} alerts to {config.ALERTS_PATH}")


if __name__ == "__main__":
    main()
