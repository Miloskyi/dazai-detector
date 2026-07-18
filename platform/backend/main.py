"""FastAPI application entry point.

Run with: python platform/backend/main.py

On platforms like Render (free tier) the filesystem is ephemeral — artifacts
and ChromaDB are lost on every restart.  The startup handler below detects this
and re-runs the full pipeline before serving any traffic, so the service is
always self-healing regardless of deployment environment.
"""

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_PLATFORM_DIR = _PROJECT_ROOT / "platform"
for _p in (_PROJECT_ROOT, _PLATFORM_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import alerts, chat, reports, stats
from intelligence.pipeline import config


def _bootstrap() -> None:
    """Run the full pipeline + RAG ingest if outputs are missing."""
    import traceback

    print(f"[startup] PROJECT_ROOT = {config.PROJECT_ROOT}")
    print(f"[startup] ALERTS_PATH  = {config.ALERTS_PATH}")
    print(f"[startup] CHROMA_DIR   = {config.CHROMA_DIR}")

    alerts_missing = not config.ALERTS_PATH.exists()
    chroma_missing = not (config.CHROMA_DIR / "chroma.sqlite3").exists()
    report_missing = (
        not any(config.REPORTS_DIR.glob("*.json"))
        if config.REPORTS_DIR.exists()
        else True
    )

    print(f"[startup] alerts_missing={alerts_missing} chroma_missing={chroma_missing} report_missing={report_missing}")

    if not (alerts_missing or chroma_missing or report_missing):
        print("[startup] All artifacts present — skipping bootstrap.")
        return

    print("[startup] Running bootstrap pipeline...")
    try:
        # 1. Ensure output dirs exist
        config.OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        config.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        (config.PROJECT_ROOT / "data" / "processed").mkdir(parents=True, exist_ok=True)

        # 2. Generate synthetic dataset
        print("[startup] Step 1/4: generating synthetic dataset...")
        from intelligence.pipeline.make_sample import main as make_sample
        make_sample()
        print(f"[startup] Dataset written to {config.PROCESSED_DATA_PATH}")

        # 3. Run hybrid model pipeline → alerts.json
        print("[startup] Step 2/4: running hybrid pipeline...")
        from intelligence.pipeline.run_pipeline import main as run_pipeline
        run_pipeline()
        print(f"[startup] Alerts written: {config.ALERTS_PATH.exists()}")

        # 4. Generate first report
        print("[startup] Step 3/4: generating report...")
        from backend.services.report_service import generate_report
        from backend.repositories.report_repository import ReportRepository
        from datetime import datetime, timezone
        report = generate_report()
        report_id = f"report_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"
        ReportRepository().save(report_id, report.to_dict(), report.to_markdown())
        print("[startup] Report saved.")

        # 5. Ingest alerts into ChromaDB
        print("[startup] Step 4/4: ingesting into ChromaDB...")
        from rag.ingest import AlertIngestor
        count = AlertIngestor().run()
        print(f"[startup] Bootstrap complete — {count} alerts ingested.")

    except Exception:
        print("[startup] ERROR during bootstrap:")
        traceback.print_exc()
        print("[startup] Service will start with empty data.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _bootstrap()
    yield


app = FastAPI(title="Dazai Detector API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.BACKEND_CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(alerts.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


@app.get("/")
def health_check():
    return {"status": "ok", "service": "dazai-detector-backend"}


if __name__ == "__main__":
    import os

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
