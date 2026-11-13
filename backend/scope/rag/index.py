"""RAG indexing with chunking + TF-IDF/FAISS hybrid retrieval."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from scope.config.loader import get_project_root
from scope.logging_config import setup_logging
from scope.rag.documents import ensure_synthetic_docs

logger = setup_logging()

RETRIEVAL_CASES = (
    ("How long is the recommended ocean shipment contingency buffer?", "SYNTHETIC_shipping_sla.md"),
    ("When should procurement escalate a vendor with a high late rate?", "SYNTHETIC_procurement_policy.md"),
    ("Are augmented inventory fields an official system of record?", "SYNTHETIC_vendor_compliance.md"),
)


@dataclass
class Chunk:
    chunk_id: str
    document_id: str
    file_name: str
    document_type: str
    source: str
    page: int
    text: str
    synthetic: bool = True


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> list[str]:
    """Character-approximate chunking (token proxy)."""
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks


def build_rag_index() -> dict[str, Any]:
    root = get_project_root()
    doc_dir = ensure_synthetic_docs()
    # Also index docs/ markdown as additional corpus
    extra_dirs = [root / "docs", root / "reports"]
    chunks: list[Chunk] = []

    files = list(doc_dir.glob("*.md"))
    for d in extra_dirs:
        if d.exists():
            files.extend(sorted(d.glob("*.md"))[:20])

    for path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        synthetic = "synthetic" in str(path).lower() or text.startswith("# SYNTHETIC")
        parts = chunk_text(text)
        for i, part in enumerate(parts, start=1):
            chunks.append(
                Chunk(
                    chunk_id=f"{path.stem}::c{i}",
                    document_id=path.stem,
                    file_name=path.name,
                    document_type=path.suffix.lstrip("."),
                    source=str(path.relative_to(root)),
                    page=i,
                    text=part,
                    synthetic=synthetic,
                )
            )

    corpus = [c.text for c in chunks]
    vectorizer = TfidfVectorizer(stop_words="english", max_features=5000, ngram_range=(1, 2))
    matrix = vectorizer.fit_transform(corpus)

    out_dir = root / "reports" / "models" / "rag_index"
    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {"vectorizer": vectorizer, "matrix": matrix, "chunks": [asdict(c) for c in chunks]},
        out_dir / "index.joblib",
    )
    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_chunks": len(chunks),
        "n_documents": len({c.document_id for c in chunks}),
        "embedding": "tfidf",
        "vector_store": "sklearn_csr + cosine (FAISS-compatible workflow; local TF-IDF index)",
        "note": "Synthetic docs are labeled. Do not treat as real contracts/policies.",
        "artifact_dir": str(out_dir),
    }
    (out_dir / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    meta["retrieval_evaluation"] = evaluate_retrieval()
    (out_dir / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    logger.info("RAG index built: %d chunks", len(chunks))
    return meta


def evaluate_retrieval(top_k: int = 5) -> dict[str, Any]:
    """Run a small, explicit synthetic query set and report Recall@k and MRR."""
    cases = []
    reciprocal_ranks = []
    for query, expected_file in RETRIEVAL_CASES:
        hits = retrieve(query, top_k=top_k)
        rank = next(
            (index for index, hit in enumerate(hits, start=1) if hit["file_name"] == expected_file),
            None,
        )
        reciprocal_ranks.append(1.0 / rank if rank is not None else 0.0)
        cases.append({
            "query": query,
            "expected_file": expected_file,
            "rank": rank,
            "retrieved_files": [hit["file_name"] for hit in hits],
        })
    result = {
        "evaluation_type": "synthetic_fixture_sanity_check",
        "n_queries": len(cases),
        "mrr": float(np.mean(reciprocal_ranks)) if reciprocal_ranks else None,
        "recall_at_k": {
            str(k): float(np.mean([case["rank"] is not None and case["rank"] <= k for case in cases]))
            for k in (1, 3, top_k)
        },
        "cases": cases,
        "limitation": "Wiring sanity check only: three hand-authored synthetic queries are not a retrieval-quality benchmark.",
    }
    path = get_project_root() / "reports" / "metrics" / "rag_retrieval_evaluation.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def load_index() -> dict[str, Any]:
    path = get_project_root() / "reports" / "models" / "rag_index" / "index.joblib"
    if not path.exists():
        build_rag_index()
    return joblib.load(path)


def _keyword_scores(query: str, chunks: list[dict[str, Any]]) -> np.ndarray:
    """Simple keyword overlap score (BM25-lite / full-text proxy)."""
    terms = [t for t in re.findall(r"[a-z0-9]+", query.lower()) if len(t) > 2]
    if not terms:
        return np.zeros(len(chunks))
    scores = []
    for chunk in chunks:
        text = chunk["text"].lower()
        hits = sum(text.count(t) for t in terms)
        scores.append(hits / (len(terms) + 1e-6))
    arr = np.asarray(scores, dtype=float)
    if arr.max() > 0:
        arr = arr / arr.max()
    return arr


def _rrf_fuse(rank_lists: list[list[int]], k: int = 60) -> list[int]:
    """Reciprocal Rank Fusion over multiple ranked id lists."""
    scores: dict[int, float] = {}
    for ranks in rank_lists:
        for rank, idx in enumerate(ranks, start=1):
            scores[idx] = scores.get(idx, 0.0) + 1.0 / (k + rank)
    return [i for i, _ in sorted(scores.items(), key=lambda x: -x[1])]


def retrieve(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Hybrid retrieval: TF-IDF vector similarity + keyword overlap, fused with RRF."""
    idx = load_index()
    chunks = idx["chunks"]
    vec = idx["vectorizer"].transform([query])
    sims = cosine_similarity(vec, idx["matrix"]).ravel()
    kw = _keyword_scores(query, chunks)

    vector_ranks = list(np.argsort(-sims))
    keyword_ranks = list(np.argsort(-kw))
    fused = _rrf_fuse([vector_ranks[:50], keyword_ranks[:50]])[:top_k]

    results = []
    for rank, i in enumerate(fused, start=1):
        chunk = dict(chunks[i])
        chunk["vector_score"] = float(sims[i])
        chunk["keyword_score"] = float(kw[i])
        chunk["score"] = float(0.6 * sims[i] + 0.4 * kw[i])
        chunk["rank"] = rank
        chunk["retrieval"] = "hybrid_rrf"
        results.append(chunk)
    return results


def answer_with_citations(query: str, top_k: int = 5) -> dict[str, Any]:
    hits = retrieve(query, top_k=top_k)
    if not hits or hits[0]["score"] < 0.01:
        return {
            "answer": "Insufficient grounded evidence found in the document index.",
            "citations": [],
            "retrieved": hits,
            "grounded": False,
        }
    bullets = []
    citations = []
    for h in hits:
        snippet = h["text"][:240].replace("\n", " ")
        cite = f"{h['file_name']}#chunk-{h['page']}"
        bullets.append(f"- {snippet}... [{cite}]")
        citations.append(
            {
                "document_id": h["document_id"],
                "file_name": h["file_name"],
                "page": h["page"],
                "source": h["source"],
                "score": h["score"],
                "synthetic": h.get("synthetic", False),
            }
        )
    answer = (
        f"Grounded summary for query: {query}\n\n"
        + "\n".join(bullets)
        + "\n\nNote: Retrieved passages may include clearly labeled synthetic documents."
    )
    return {
        "answer": answer,
        "citations": citations,
        "retrieved": hits,
        "grounded": True,
    }


if __name__ == "__main__":
    print(build_rag_index())
    print(answer_with_citations("What should happen when a vendor is frequently late?")["answer"][:500])
