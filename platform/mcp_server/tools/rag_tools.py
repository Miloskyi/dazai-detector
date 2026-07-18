"""Thin, grounded wrapper over the RAG retriever — the only way agents reach Chroma."""

from __future__ import annotations

from rag.retriever import AlertRetriever

_retriever: AlertRetriever | None = None


def _get_retriever() -> AlertRetriever:
    global _retriever
    if _retriever is None:
        _retriever = AlertRetriever()
    return _retriever


def search_similar(query: str, k: int = 5, tier_filter: str | None = None) -> list[dict]:
    return _get_retriever().search(query, k=k, tier_filter=tier_filter)
