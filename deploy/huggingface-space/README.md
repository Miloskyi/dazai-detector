---
title: Dazai Detector API
emoji: 🕵️
colorFrom: red
colorTo: gray
sdk: docker
dockerfile: deploy/huggingface-space/Dockerfile
app_port: 7860
pinned: false
---

# Dazai Detector — Backend API

FastAPI backend for the hybrid credit card fraud detection platform (DBSCAN + XGBoost, SHAP
explanations, automatic reports, grounded investigation chat). This Space bakes a synthetic demo
dataset, a trained hybrid model, a report, and a ChromaDB index into the image at build time, since
Spaces' filesystem is ephemeral.

- `GET /` — health check
- `GET /api/alerts` — list alerts
- `GET /api/stats` — dashboard stats
- `GET /api/reports/latest` — latest high-risk report
- `POST /api/chat` — grounded investigation chat

Set `BACKEND_CORS_ORIGINS` in this Space's Settings → Variables to your frontend's deployed origin
(e.g. `https://your-project.pages.dev`) so the frontend can call this API from the browser.
