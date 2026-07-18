# Spec 08 — Frontend

## Goal

A dashboard an investigator (or a hackathon judge) can navigate in under a minute: see the risk
landscape, drill into one alert's explanation, read the auto-generated report, and ask the chat a
question.

## Scope

Stack: React + Vite + Tailwind CSS + Recharts + `react-router-dom`.

- `platform/frontend/src/api/client.ts` — single `fetch` wrapper (base URL from `VITE_API_URL`); every
  page calls the backend through this, never `fetch` directly (keeps the API surface in one file).
- `platform/frontend/src/pages/`
  - `Dashboard.tsx` — KPI cards (total alerts, by tier) + Recharts bar chart (alerts by hour) fed by
    `GET /api/stats`.
  - `Alerts.tsx` — sortable/filterable table of alerts (tier, amount, score), links to detail.
  - `AlertDetail.tsx` — alert metadata + SHAP horizontal bar chart (feature → impact) + narrative text,
    fed by `GET /api/alerts/{id}`.
  - `Reports.tsx` — renders the latest report's Markdown (`GET /api/reports/latest/markdown`) with a
    "Generate now" button (`POST /api/reports/generate`).
  - `Chat.tsx` — message list + input; each answer shows its `sources` chips underneath.
- `platform/frontend/src/components/` — shared: `TierBadge`, `RiskScoreBar`, `ShapBarChart`, `NavBar`.

## Contract

- All network calls go through `api/client.ts`; components receive typed data (TypeScript interfaces
  mirroring the backend Pydantic schemas) — no `any` on API responses.

## Acceptance criteria

- `npm run dev` serves the app; Dashboard, Alerts, AlertDetail, Reports, Chat all render against a
  running backend with no console errors.
- AlertDetail's SHAP chart matches the ordering/sign of `shap_explanation` from the backend.
- Chat page successfully round-trips all 4 predefined question types end-to-end through the real backend.
