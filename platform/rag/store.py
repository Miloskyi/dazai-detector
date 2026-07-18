"""ChromaDB client access.

Singleton pattern: one persistent client per process, so we never re-open the
on-disk index (and never fight over its lock file).

Uses a lightweight hash-based embedding by default to avoid the 79MB ONNX model
download that kills the process on memory-constrained free-tier hosts (Render 512MB).
Set CHROMA_USE_ONNX=true to use the full all-MiniLM-L6-v2 model instead.
"""

from __future__ import annotations

import hashlib
import os

import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings

from intelligence.pipeline import config

_client: chromadb.ClientAPI | None = None


class _LightweightEmbeddingFunction(EmbeddingFunction):
    """Character-level hash embedding — no model download, no RAM spike.
    Dimensionality: 384 floats (same as MiniLM for collection compatibility).
    Sufficient for keyword-based fraud investigation queries.
    """

    DIM = 384

    def __call__(self, input: Documents) -> Embeddings:
        result = []
        for text in input:
            vec = [0.0] * self.DIM
            words = text.lower().split()
            for i, word in enumerate(words):
                h = int(hashlib.md5(word.encode()).hexdigest(), 16)
                idx = h % self.DIM
                vec[idx] += 1.0 / (i + 1)
            norm = sum(x * x for x in vec) ** 0.5 or 1.0
            result.append([x / norm for x in vec])
        return result


def _get_embedding_fn():
    if os.getenv("CHROMA_USE_ONNX", "false").lower() == "true":
        return None  # ChromaDB default = all-MiniLM-L6-v2
    return _LightweightEmbeddingFunction()


class ChromaStore:
    def __init__(self):
        global _client
        if _client is None:
            config.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
            _client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
        self._client = _client

    def collection(self, name: str = config.CHROMA_COLLECTION_NAME):
        return self._client.get_or_create_collection(
            name,
            embedding_function=_get_embedding_fn(),
        )
