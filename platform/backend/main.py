"""FastAPI application entry point."""

import sys
import threading
import traceback
import os
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


def _run_bootstrap() -> None:
    """Run the full pipeline in a background thread so the server starts immediately.
    Render free tier kills processes that don't bind a port within ~60s.
    Running the pipeline (~2-3 min) in a thread avoids that timeout.
    """
    try:
        print(f"[bootstrap] PROJECT_ROOT = {config.PROJECT_ROOT}")
        print(f"[bootstrap] cwd          = {os.getcwd()}")
        print(f"[bootstrap] ALERTS_PATH  = {config.ALERTS_PATH}")
        print(f"[bootstrap] CHROMA_DIR   = {config.CHROMA_DIR}")

        alerts_ok = config.ALERTS_PATH.exists()
        chroma_ok = (config.CHROMA_DIR / "chroma.sqlite3").exists()
        report_ok = (
            config.REPORTS_DIR.exists()
            and any(config.REPORTS_DIR.glob("*.json"))
        )

        print(f"[bootstrap] alerts_ok={alerts_ok} chroma_ok={chroma_ok} report_ok={report_ok}")

        if alerts_ok and chroma_ok and report_ok:
            print("[bootstrap] All artifacts present — skipping.")
            return

        print("[bootstrap] Starting pipeline...")

        # Ensure dirs exist
        config.OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        config.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        (config.PROJECT_ROOT / "data" / "processed").mkdir(parents=True, exist_ok=True)

        # Step 1: synthetic dataset
        print("[bootstrap] 1/4 generating dataset...")
        from intelligence.pipeline.make_sample import main as make_sample
        make_sample()

        # Step 2: hybrid model + alerts.json
        print("[bootstrap] 2/4 running hybrid pipeline...")
        from intelligence.pipeline.run_pipeline import main as run_pipeline
        run_pipeline()
        print(f"[bootstrap] alerts.json exists: {config.ALERTS_PATH.exists()}")

        # Step 3: report
        print("[bootstrap] 3/4 generating report...")
        from backend.services.report_service import generate_report
        from backend.repositories.report_repository import ReportRepository
        from datetime import datetime, timezone
        report = generate_report()
        rid = f"report_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"
        ReportRepository().save(rid, report.to_dict(), report.to_markdown())

        # Step 4: ChromaDB ingest
        print("[bootstrap] 4/4 ingesting into ChromaDB...")
        # rag package lives at platform/rag — _PLATFORM_DIR already in sys.path
        from rag.ingest import AlertIngestor
        count = AlertIngestor().run()
        print(f"[bootstrap] Done — {count} alerts ingested.")

    except Exception:
        print("[bootstrap] FAILED:")
        traceback.print_exc()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start bootstrap in background — server binds port immediately
    t = threading.Thread(target=_run_bootstrap, daemon=True)
    t.start()
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


@app.get("/debug")
def debug_info():
    return {
        "project_root": str(config.PROJECT_ROOT),
        "alerts_path": str(config.ALERTS_PATH),
        "alerts_exists": config.ALERTS_PATH.exists(),
        "chroma_sqlite": str(config.CHROMA_DIR / "chroma.sqlite3"),
        "chroma_exists": (config.CHROMA_DIR / "chroma.sqlite3").exists(),
        "cwd": os.getcwd(),
        "sys_path": sys.path[:4],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
