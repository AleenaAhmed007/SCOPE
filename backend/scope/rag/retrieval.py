"""Hybrid retrieval: dense bi-encoder + Okapi BM25, fused with RRF, then reranked.

Pipeline
--------
1. Dense   : cosine similarity against bge-small-en-v1.5 passage vectors.
2. Lexical : Okapi BM25 over the same chunks.
3. Fusion  : Reciprocal Rank Fusion of the two ranked lists.
4. Rerank  : cross-encoder (ms-marco-MiniLM) over the top fused candidates.

Each stage is independently skippable and the retrieval mode actually used is
recorded on every hit, so an ablation can report dense-only, BM25-only, fused
and fused+reranked quality separately.
"""

from __future__ import annotations

from typing import Any, Iterable, Sequence

import numpy as np

from scope.rag.bm25 import BM25Index
from scope.rag.embeddings import encode_query, rerank

RRF_K = 60
DENSE_CANDIDATES = 50
LEXICAL_CANDIDATES = 50
RERANK_CANDIDATES = 25


def ranked_indices(scores: Sequence[float]) -> list[int]:
    """Indices sorted by descending score (stable for ties)."""
    return [int(i) for i in np.argsort(-np.asarray(scores, dtype=float), kind="stable")]


def fuse_reciprocal_rank(rank_lists: Iterable[Sequence[int]], k: int = RRF_K) -> list[tuple[int, float]]:
    """Reciprocal Rank Fusion over several ranked index lists."""
    combined: dict[int, float] = {}
    for ranks in rank_lists:
        for position, index in enumerate(ranks, start=1):
            combined[int(index)] = combined.get(int(index), 0.0) + 1.0 / (k + position)
    return sorted(combined.items(), key=lambda item: -item[1])


def _restrict(chunks: Sequence[dict[str, Any]], doc_types: Sequence[str] | None) -> list[int]:
    if not doc_types:
        return list(range(len(chunks)))
    allowed = {value.lower() for value in doc_types}
    return [i for i, chunk in enumerate(chunks) if chunk.get("document_type", "").lower() in allowed]


def search(
    query: str,
    chunks: Sequence[dict[str, Any]],
    *,
    dense_vectors: np.ndarray | None = None,
    bm25: BM25Index | None = None,
    top_k: int = 5,
    doc_types: Sequence[str] | None = None,
    use_rerank: bool = True,
) -> list[dict[str, Any]]:
    """Run the hybrid retrieval pipeline over an in-memory index."""
    if not chunks:
        return []

    candidates = _restrict(chunks, doc_types) or list(range(len(chunks)))
    if not candidates:
        return []

    rank_lists: list[list[int]] = []
    dense_scores = np.zeros(len(chunks), dtype=float)
    lexical_scores = np.zeros(len(chunks), dtype=float)
    components: list[str] = []

    vector = encode_query(query) if dense_vectors is not None else None
    if vector is not None and dense_vectors is not None:
        dense_scores = np.asarray(dense_vectors @ vector, dtype=float)
        order = [i for i in ranked_indices(dense_scores) if i in set(candidates)]
        rank_lists.append(order[:DENSE_CANDIDATES])
        components.append("dense")

    if bm25 is not None:
        lexical_scores = np.asarray(bm25.scores(query), dtype=float)
        order = [i for i in ranked_indices(lexical_scores) if i in set(candidates)]
        rank_lists.append(order[:LEXICAL_CANDIDATES])
        components.append("bm25")

    if not rank_lists:  # no retriever available at all
        return []

    fused = fuse_reciprocal_rank(rank_lists)
    fused = [(index, score) for index, score in fused if index in set(candidates)]
    candidates_top = fused[: max(top_k, RERANK_CANDIDATES)]

    rerank_scores: dict[int, float] = {}
    if use_rerank and candidates_top:
        passages = [chunks[index]["text"] for index, _ in candidates_top]
        scores = rerank(query, passages)
        if scores is not None and len(scores) == len(passages):
            rerank_scores = {index: float(score) for (index, _), score in zip(candidates_top, scores)}
            candidates_top = sorted(
                candidates_top, key=lambda item: rerank_scores.get(item[0], float("-inf")), reverse=True
            )
            components.append("cross_encoder_rerank")

    mode = "hybrid_rrf+rerank" if rerank_scores else ("hybrid_rrf" if len(rank_lists) > 1 else "single_retriever")

    results: list[dict[str, Any]] = []
    for rank, (index, rrf_score) in enumerate(candidates_top[:top_k], start=1):
        chunk = dict(chunks[index])
        chunk["dense_score"] = float(dense_scores[index])
        chunk["lexical_score"] = float(lexical_scores[index])
        chunk["rrf_score"] = float(rrf_score)
        chunk["rerank_score"] = rerank_scores.get(index)
        chunk["score"] = (
            float(rerank_scores[index]) if index in rerank_scores else float(rrf_score)
        )
        chunk["rank"] = rank
        chunk["retrieval"] = mode
        chunk["retrieval_components"] = components
        results.append(chunk)
    return results


def dense_only_ranking(
    query: str, chunks: Sequence[dict[str, Any]], dense_vectors: np.ndarray | None, top_k: int
) -> list[int]:
    """Ablation helper: dense-only ranking, no fusion or reranking."""
    if dense_vectors is None:
        return []
    vector = encode_query(query)
    if vector is None:
        return []
    return ranked_indices(dense_vectors @ vector)[:top_k]


def lexical_only_ranking(
    query: str, bm25: BM25Index | None, top_k: int
) -> list[int]:
    """Ablation helper: BM25-only ranking."""
    if bm25 is None:
        return []
    return ranked_indices(bm25.scores(query))[:top_k]


def fuse_only_ranking(
    query: str,
    chunks: Sequence[dict[str, Any]],
    dense_vectors: np.ndarray | None,
    bm25: BM25Index | None,
    top_k: int,
) -> list[int]:
    """Ablation helper: fusion without the cross-encoder reranker."""
    hits = search(
        query,
        chunks,
        dense_vectors=dense_vectors,
        bm25=bm25,
        top_k=top_k,
        use_rerank=False,
    )
    lookup = {chunk["chunk_id"]: i for i, chunk in enumerate(chunks)}
    return [lookup[hit["chunk_id"]] for hit in hits]
