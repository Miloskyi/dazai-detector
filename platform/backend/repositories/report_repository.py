"""Persists and retrieves generated reports.

Repository pattern: this is the only place that writes/reads report files.
"""

from __future__ import annotations

import json
from pathlib import Path

from intelligence.pipeline import config


class ReportRepository:
    def __init__(self):
        config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    def save(self, report_id: str, json_content: dict, markdown_content: str) -> None:
        (config.REPORTS_DIR / f"{report_id}.json").write_text(json.dumps(json_content, indent=2))
        (config.REPORTS_DIR / f"{report_id}.md").write_text(markdown_content)

    def latest_id(self) -> str | None:
        files = sorted(config.REPORTS_DIR.glob("*.json"))
        return files[-1].stem if files else None

    def get_json(self, report_id: str) -> dict | None:
        path = config.REPORTS_DIR / f"{report_id}.json"
        return json.loads(path.read_text()) if path.exists() else None

    def get_markdown(self, report_id: str) -> str | None:
        path = config.REPORTS_DIR / f"{report_id}.md"
        return path.read_text() if path.exists() else None

    def latest_json(self) -> dict | None:
        report_id = self.latest_id()
        return self.get_json(report_id) if report_id else None

    def latest_markdown(self) -> str | None:
        report_id = self.latest_id()
        return self.get_markdown(report_id) if report_id else None
