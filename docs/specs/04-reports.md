# Spec 04 — Automatic High-Risk Reports

## Goal

Turn a batch of alerts into a digestible report for someone who will never open the dashboard —
a periodic summary of what happened and where to look first.

## Scope

- `platform/backend/services/report_service.py`
  - `ReportBuilder` (**Builder pattern**): incrementally assembles a report.
    - `.with_alerts(alerts)` — filters to `HIGH`/`CRITICAL` tiers.
    - `.with_summary_stats()` — count by tier, total flagged amount, top 5 by risk score.
    - `.with_patterns()` — cheap aggregate stats: flagged count by hour-of-day bucket, by amount
      bucket (reuses the same aggregation the `pattern_analysis` chat intent uses — one
      implementation, not two).
    - `.with_narratives()` — pulls the (already generated/cached) narrative for each top alert.
    - `.build() -> Report` — dataclass with all of the above.
  - `ReportRepository` (**Repository pattern**): persists a `Report` as both
    `data/outputs/reports/report_<timestamp>.json` (machine-readable) and `.md` (human-readable,
    for the expo demo) and can list/fetch the latest.

## Contract

- `Report.to_markdown()` produces a self-contained document: title, generation date, tier counts,
  top-5 alert table with narrative, pattern summary.
- Backend route `GET /api/reports/latest` returns the most recent report's JSON; `GET
  /api/reports/latest/markdown` returns the rendered text.

## Acceptance criteria

- Running the report builder against `alerts.json` from spec 02/03 produces a non-empty report when at
  least one HIGH/CRITICAL alert exists, and a clearly-labeled empty report otherwise (no crash).
- Markdown report renders cleanly (valid headers, table) when pasted into any Markdown viewer.
