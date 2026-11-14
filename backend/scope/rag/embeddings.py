"""Dense bi-encoder and cross-encoder wrappers (fastembed / onnxruntime).

Both components are optional: if the package or a model is unavailable the
retrieval stack falls back to lexical scoring and reports `dense_available`
/ `reranker_available` in the index metadata, so results are never silently
presented as something they are not.

Models:
  * bi-encoder:  BAAI/bge-small-en-v1.5       (384-d, cosine)
  * cross-encoder: Xenova/ms-marco-MiniLM-L-6-v2 (pairwise relevance)
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Sequence

import numpy as np

DENSE_MODEL_NAME = os.getenv("SCOPE_RAG_DENSE_MODEL", "BAAI/bge-small-en-v1.5")
RERANK_MODEL_NAME = os.getenv("SCOPE_RAG_RERANK_MODEL", "Xenova/ms-marco-MiniLM-L-6-v2")
DISABLE_ENV = "SCOPE_RAG_DISABLE_NEURAL"


def _neural_disabled() -> bool:
    return os.getenv(DISABLE_ENV, "").lower() in {"1", "true", "yes", "off"}


def _normalise(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    return (matrix / norms).astype(np.float32)


@lru_cache(maxsize=1)
def get_dense_encoder() -> Any | None:
    """Cached bi-encoder instance, or None when unavailable."""
    if _neural_disabled():
        return None
    try:
        from fastembed import TextEmbedding

        return TextEmbedding(model_name=DENSE_MODEL_NAME)
    except Exception:  # package missing, offline, or unsupported platform
        return None


@lru_cache(maxsize=1)
def get_cross_encoder() -> Any | None:
    """Cached cross-encoder reranker instance, or None when unavailable."""
    if _neural_disabled():
        return None
    try:
        from fastembed.rerank.cross_encoder import TextCrossEncoder

        return TextCrossEncoder(model_name=RERANK_MODEL_NAME)
    except Exception:
        return None


def encode_passages(texts: Sequence[str]) -> np.ndarray | None:
    """Normalised dense vectors for a batch of passages (None if unavailable)."""
    encoder = get_dense_encoder()
    if encoder is None or not texts:
        return None
    try:
        vectors = np.asarray(list(encoder.embed(list(texts))), dtype=np.float32)
    except Exception:
        return None
    return _normalise(vectors)


def encode_query(text: str) -> np.ndarray | None:
    """Normalised dense vector for a single query (None if unavailable)."""
    encoded = encode_passages([text])
    return None if encoded is None else encoded[0]


def rerank(query: str, passages: Sequence[str]) -> list[float] | None:
    """Cross-encoder relevance scores for (query, passage) pairs."""
    encoder = get_cross_encoder()
    if encoder is None or not passages:
        return None
    try:
        scores = list(encoder.rerank(query, list(passages)))
    except Exception:
        return None
    return [float(score) for score in scores]


def neural_availability() -> dict[str, bool]:
    """Report availability without forcing a model download."""
    if _neural_disabled():
        return {
            "dense_available": False,
            "reranker_available": False,
            "reason": f"{DISABLE_ENV} is set",
        }
    try:
        import fastembed  # noqa: F401
    except Exception:
        return {
            "dense_available": False,
            "reranker_available": False,
            "reason": "fastembed not installed",
        }
    try:
        from fastembed.rerank.cross_encoder import TextCrossEncoder  # noqa: F401
    except Exception:
        return {
            "dense_available": True,
            "reranker_available": False,
            "reason": "cross-encoder API unavailable in installed fastembed",
        }
    return {"dense_available": True, "reranker_available": True, "reason": "fastembed"}
