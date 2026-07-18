"""Ingests alert narratives into the ChromaDB vector store.

Idempotent: re-running after a new pipeline run upserts by alert id, it never
duplicates documents.

Run with: python platform/rag/ingest.py
"""

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_PLATFORM_DIR = _PROJECT_ROOT / "platform"
for _p in (_PROJECT_ROOT, _PLATFORM_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from backend.services.narrative_service import NarrativeService
from mcp_server.tools import alert_tools
from rag.store import ChromaStore


class AlertIngestor:
    def __init__(self):
        self._collection = ChromaStore().collection()
        self._narrative_service = NarrativeService()

    def _document_for(self, alert: dict) -> tuple[str, str, dict]:
        narrative = alert.get("narrative") or self._narrative_service.narrate(alert)
        top_features = ", ".join(f["feature"] for f in alert.get("shap_explanation", [])[:3])

        text = (
            f"{narrative} Amount: ${alert['amount']:.2f}. "
            f"Tier: {alert['risk_tier']}. Top features: {top_features}."
        )
        metadata = {
            "alert_id": alert["id"],
            "risk_tier": alert["risk_tier"],
            "amount": alert["amount"],
            "timestamp": alert["timestamp"],
        }
        return alert["id"], text, metadata

    def run(self) -> int:
        alerts = alert_tools.all_alerts()
        if not alerts:
            print("No alerts found — run intelligence/pipeline/run_pipeline.py first.")
            return 0

        ids, documents, metadatas = [], [], []
        for alert in alerts:
            alert_id, text, metadata = self._document_for(alert)
            ids.append(alert_id)
            documents.append(text)
            metadatas.append(metadata)

        self._collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        return len(ids)


def main() -> None:
    count = AlertIngestor().run()
    print(f"Ingested {count} alerts into the '{ChromaStore().collection().name}' collection.")


if __name__ == "__main__":
    main()
