"""Semantic search over ingested alert narratives.

This is the only object the `similar_cases` chat agent and the MCP `rag_tools`
are allowed to call — it is the single boundary between the chat layer and
the vector store.
"""

from __future__ import annotations

from rag.store import ChromaStore


class AlertRetriever:
    def __init__(self):
        self._collection = ChromaStore().collection()

    def search(self, query: str, k: int = 5, tier_filter: str | None = None) -> list[dict]:
        where = {"risk_tier": tier_filter.upper()} if tier_filter else None
        results = self._collection.query(query_texts=[query], n_results=k, where=where)

        if not results["ids"] or not results["ids"][0]:
            return []

        hits = []
        for i, alert_id in enumerate(results["ids"][0]):
            hits.append(
                {
                    "alert_id": alert_id,
                    "snippet": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if results.get("distances") else None,
                }
            )
        return hits
