"""FastAPI application entry point.

Run with: python platform/backend/main.py
"""

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_PLATFORM_DIR = _PROJECT_ROOT / "platform"
for _p in (_PROJECT_ROOT, _PLATFORM_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import alerts, chat, reports, stats
from intelligence.pipeline import config

app = FastAPI(title="Dazai Detector API", version="1.0.0")

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

    # Hosts like Hugging Face Spaces assign the listen port via $PORT.
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
