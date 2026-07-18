"""ChromaDB client access.

Singleton pattern: one persistent client per process, so we never re-open the
on-disk index (and never fight over its lock file).
"""

from __future__ import annotations

import chromadb

from intelligence.pipeline import config

_client: chromadb.ClientAPI | None = None


class ChromaStore:
    def __init__(self):
        global _client
        if _client is None:
            config.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
            _client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
        self._client = _client

    def collection(self, name: str = config.CHROMA_COLLECTION_NAME):
        return self._client.get_or_create_collection(name)
