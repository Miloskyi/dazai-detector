"""Single source of truth for paths, thresholds and hyperparameters.

Nothing outside this module should hardcode a file path or a model/risk parameter.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

# --- Data paths -------------------------------------------------------------

RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "creditcard.csv"
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "sample.csv"

ARTIFACTS_DIR = PROJECT_ROOT / "intelligence" / "pipeline" / "artifacts"
SCALER_PATH = ARTIFACTS_DIR / "scaler.joblib"
CLASSIFIER_PATH = ARTIFACTS_DIR / "classifier.joblib"

OUTPUTS_DIR = PROJECT_ROOT / "data" / "outputs"
ALERTS_PATH = OUTPUTS_DIR / "alerts.json"
REPORTS_DIR = OUTPUTS_DIR / "reports"
NARRATIVES_PATH = OUTPUTS_DIR / "narratives.json"

CHROMA_DIR = Path(os.getenv("CHROMA_DIR", str(OUTPUTS_DIR / "chroma")))
CHROMA_COLLECTION_NAME = "alerts"

# --- Dataset schema -----------------------------------------------------------

PCA_FEATURE_COLUMNS = [f"V{i}" for i in range(1, 29)]
FEATURE_COLUMNS = ["Time", *PCA_FEATURE_COLUMNS, "Amount"]
LABEL_COLUMN = "Class"

# --- Sampling / split ---------------------------------------------------------

SAMPLE_SIZE = 20_000
SYNTHETIC_ROWS = 20_000
SYNTHETIC_FRAUD_RATE = 0.015
RANDOM_STATE = 42
TEST_SIZE = 0.3

# --- Hybrid model --------------------------------------------------------------

DBSCAN_EPS = 1.5
DBSCAN_MIN_SAMPLES = 5

CLASSIFIER_WEIGHT = 0.7
DBSCAN_WEIGHT = 0.3

ALERT_THRESHOLD = 0.5

RISK_TIERS = {
    "LOW": 0.0,
    "MEDIUM": 0.5,
    "HIGH": 0.75,
    "CRITICAL": 0.9,
}

SHAP_TOP_N = 5

# --- LLM narrative -------------------------------------------------------------

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "none")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")

# --- Backend ---------------------------------------------------------------

BACKEND_CORS_ORIGINS = os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:5173").split(",")

ALERTS_DEFAULT_LIMIT = 25
ALERTS_MAX_LIMIT = 100


def risk_tier_for(score: float) -> str:
    """Map a risk score in [0, 1] to its tier using the highest threshold met."""
    tier = "LOW"
    for name, cutoff in sorted(RISK_TIERS.items(), key=lambda item: item[1]):
        if score >= cutoff:
            tier = name
    return tier
