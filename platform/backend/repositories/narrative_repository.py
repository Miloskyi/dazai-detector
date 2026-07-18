"""Persists generated narratives to disk instead of an in-process dict.

Repository pattern: this is the only place that touches narratives.json. A
plain in-memory cache would go stale/diverge between multiple worker
processes (e.g. gunicorn with several workers, or independently restarted
containers); reading/writing a shared file keeps every worker consistent.
Narrative generation is deterministic under the template fallback, so a rare
concurrent write race just regenerates the same text — never a correctness
issue, only a wasted narrative call.
"""

from __future__ import annotations

import json
import os

from intelligence.pipeline import config


class NarrativeRepository:
    def __init__(self):
        config.NARRATIVES_PATH.parent.mkdir(parents=True, exist_ok=True)

    def _read_all(self) -> dict[str, str]:
        if not config.NARRATIVES_PATH.exists():
            return {}
        with open(config.NARRATIVES_PATH) as f:
            return json.load(f)

    def get(self, alert_id: str) -> str | None:
        return self._read_all().get(alert_id)

    def set(self, alert_id: str, narrative: str) -> None:
        narratives = self._read_all()
        narratives[alert_id] = narrative

        tmp_path = config.NARRATIVES_PATH.with_suffix(".tmp")
        with open(tmp_path, "w") as f:
            json.dump(narratives, f, indent=2)
        os.replace(tmp_path, config.NARRATIVES_PATH)
