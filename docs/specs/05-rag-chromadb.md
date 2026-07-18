# Spec 05 — RAG with ChromaDB

## Goal

Let the investigation chat find semantically similar past alerts ("find cases like this one") instead
of only exact-matching on transaction ID.

## Scope

- `platform/rag/store.py`
  - `ChromaStore` (**Singleton pattern** — one persistent client per process): wraps
    `chromadb.PersistentClient(path=config.CHROMA_DIR)`, exposes `.collection("alerts")`.
- `platform/rag/ingest.py`
  - `AlertIngestor.run()`: reads `alerts.json`, builds one document per alert:
    `text = f"{narrative} Amount: {amount}. Tier: {risk_tier}. Top features: {feature_list}."`,
    `metadata = {alert_id, risk_tier, amount, timestamp}`. Upserts into the `alerts` collection
    (Chroma's default embedding function — no external embedding API needed, keeps the demo offline-safe).
- `platform/rag/retriever.py`
  - `AlertRetriever.search(query: str, k=5, tier_filter: str | None = None) -> list[dict]` — semantic
    query against the collection, optional metadata filter, returns matched alert IDs + similarity +
    snippet.

## Contract

- Ingestion is idempotent: re-running `ingest.py` after a new `run_pipeline.py` upserts by `alert_id`
  (no duplicate documents).
- `AlertRetriever` is the only thing the `similar_cases` chat agent and the MCP `rag_tools` are allowed
  to call — no direct Chroma access anywhere else (keeps the grounding boundary in one place).

## Acceptance criteria

- `python platform/rag/ingest.py` populates the collection and prints a count.
- A retriever query for a known alert's narrative text returns that alert as the top or near-top hit.
- Re-ingesting after the underlying `alerts.json` changes does not grow the collection unbounded.
