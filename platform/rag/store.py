"""ChromaDB client — lightweight hash embeddings to avoid ONNX on free-tier hosts."""

from __future__ import annotations

import hashlib
import os
from typing import List

import chromadb
from intelligence.pipeline import config

_client: chromadb.ClientAPI | None = None


class _HashEmbedding:
    """384-dim TF-IDF-style hash embedding. No downloads, no RAM spike."""
    DIM = 384

    def name(self) -> str:
        return "hash_embed"

    def __call__(self, input: List[str]) -> List[List[float]]:
        result = []
        for text in input:
            vec = [0.0] * self.DIM
            words = text.lower().split()
            for i, word in enumerate(words):
                h = int(hashlib.md5(word.encode()).hexdigest(), 16)
                vec[h % self.DIM] += 1.0 / (i + 1)
            norm = (sum(x * x for x in vec) ** 0.5) or 1.0
            result.append([x / norm for x in vec])
        return result


def _get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        config.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    return _client


class ChromaStore:
    def collection(self, name: str = config.CHROMA_COLLECTION_NAME):
        client = _get_client()
        use_onnx = os.getenv("CHROMA_USE_ONNX", "false").lower() == "true"
        if use_onnx:
            # Full sentence-transformer model (needs ~200MB RAM extra)
            return client.get_or_create_collection(name)
        # Lightweight path: delete + recreate if no embedding_function was set before
        try:
            col = client.get_collection(name)
            # ChromaDB stores metadata about the embedding function — if collection
            # was created with the default ONNX function, recreate it with ours
            meta = col.metadata or {}
            if meta.get("hnsw:space") != "cosine" or "hash_embed" not in meta.get("embedding_fn", ""):
                # Safe to delete on free-tier because data is regenerated at every cold start
                client.delete_collection(name)
                raise ValueError("recreate")
        except Exception:
            pass
        return client.get_or_create_collection(
            name,
            embedding_function=_HashEmbedding(),
            metadata={"hnsw:space": "cosine", "embedding_fn": "hash_embed"},
        )
