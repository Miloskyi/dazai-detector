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
    """Run the full pipeline + RAG ingest if outputs are missing.

    This makes the service self-healing on platforms with ephemeral filesystems
    (Render free tier, any container without a persistent volume).  The check is
    fast when artifacts are already present (just a file-existence test).
    """
    alerts_missing = not config.ALERTS_PATH.exists()
    chroma_missing = not (config.CHROMA_DIR / "chroma.sqlite3").exists()
    report_missing = not any(config.REPORTS_DIR.glob("*.json")) if config.REPORTS_DIR.exists() else True

    if alerts_missing or chroma_missing or report_missing:
        print("[startup] Artifacts missing — running bootstrap pipeline...")

        # 1. Generate synthetic dataset if no raw CSV present
        from intelligence.pipeline.make_sample import main as make_sample
        make_sample()

        # 2. Run hybrid model pipeline → alerts.json
        from intelligence.pipeline.run_pipeline import main as run_pipeline
        run_pipeline()

        # 3. Generate first report
        from backend.services.report_service import generate_report
        from backend.repositories.report_repository import ReportRepository
        from datetime import datetime, timezone
        report = generate_report()
        report_id = f"report_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"
        ReportRepository().save(report_id, report.to_dict(), report.to_markdown())

        # 4. Ingest alerts into ChromaDB
        from rag.ingest import AlertIngestor
        count = AlertIngestor().run()
        print(f"[startup] Bootstrap complete — {count} alerts ingested.")
    else:
        print("[startup] Artifacts present — skipping bootstrap.")


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
