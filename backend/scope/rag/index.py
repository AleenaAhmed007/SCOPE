"""RAG index: corpus collection, chunking, dense + BM25 indexing, evaluation.

Only ``data/documents/`` is indexed (synthetic fixtures plus user uploads).
Project reports and documentation are deliberately **excluded** — indexing them
let an investigation cite the project's own output as evidence, which is
circular and was flagged in the completeness audit.

The index artifact stores the chunk table, the dense passage matrix and the
BM25 statistics, so retrieval needs no corpus re-read at request time.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from scope.config.loader import get_project_root
from scope.logging_config import setup_logging
from scope.rag.answer import GroundedAnswer, build_answer
from scope.rag.bm25 import BM25Index
from scope.rag.chunking import chunk_markdown, is_synthetic
from scope.rag.documents import (
    SYNTHETIC_SUBDIR,
    UPLOAD_SUBDIR,
    ensure_synthetic_docs,
    infer_document_type,
    synthetic_doc_dir,
    upload_doc_dir,
)
from scope.rag.embeddings import encode_passages, neural_availability
from scope.rag.retrieval import (
    dense_only_ranking,
    lexical_only_ranking,
    search,
)

logger = setup_logging()

INDEX_DIR = Path("reports") / "models" / "rag_index"
INDEX_FILE = "index.joblib"
METADATA_FILE = "metadata.json"
INDEX_VERSION = "2.0"

# (query, expected file, expected section substring) — gold labels for retrieval.
RETRIEVAL_CASES: tuple[tuple[str, str, str], ...] = (
    ("How long is the recommended ocean shipment contingency buffer?", "SYNTHETIC_shipping_sla.md", "delivery windows"),
    ("When must a vendor notify procurement about an expected delay?", "SYNTHETIC_shipping_sla.md", "delay notification"),
    ("Which mode should clinically urgent ARV shipments use?", "SYNTHETIC_shipping_sla.md", "mode selection"),
    ("What service credit applies for a late delivery?", "SYNTHETIC_supplier_agreement.md", "penalties"),
    ("What is the maximum penalty cap for repeated late weeks?", "SYNTHETIC_supplier_agreement.md", "penalties"),
    ("Which events are excluded from force majeure relief?", "SYNTHETIC_supplier_agreement.md", "force majeure"),
    ("How long must shipment and delivery records be retained?", "SYNTHETIC_supplier_agreement.md", "audit rights"),
    ("At what vendor late rate must procurement escalate?", "SYNTHETIC_procurement_policy.md", "escalation trigger"),
    ("How many shipments must a vendor quarter contain to be reviewed?", "SYNTHETIC_procurement_policy.md", "cadence"),
    ("What must a disruption claim cite as evidence?", "SYNTHETIC_procurement_policy.md", "evidence requirements"),
    ("Below how many days of stock cover is it an inventory emergency?", "SYNTHETIC_inventory_policy.md", "stock cover"),
    ("When does a stockout occur?", "SYNTHETIC_inventory_policy.md", "stockout"),
    ("What temperature range must cold chain products be kept in?", "SYNTHETIC_cold_chain_policy.md", "temperature range"),
    ("What happens after a temperature excursion longer than two hours?", "SYNTHETIC_cold_chain_policy.md", "excursion"),
    ("What defect rate triggers a quality review?", "SYNTHETIC_quality_policy.md", "defect rate"),
    ("Can a missing temperature record block batch release?", "SYNTHETIC_quality_policy.md", "release decision"),
    ("How quickly must a Severity 1 disruption be acknowledged?", "SYNTHETIC_escalation_matrix.md", "response times"),
    ("What must an escalation record reference?", "SYNTHETIC_escalation_matrix.md", "mandatory evidence"),
    ("Are anomaly scores proof of fraud?", "SYNTHETIC_vendor_compliance.md", "anomaly"),
    ("Must missing freight cost be treated as zero?", "SYNTHETIC_vendor_compliance.md", "freight cost"),
)

_SUFFIXES = {".md", ".txt", ".markdown"}


def index_dir() -> Path:
    return get_project_root() / INDEX_DIR


def corpus_files() -> list[Path]:
    """Document files eligible to become evidence (synthetic fixtures + uploads)."""
    ensure_synthetic_docs()
    files: list[Path] = []
    for directory in (synthetic_doc_dir(), upload_doc_dir()):
        if not directory.exists():
            continue
        for path in sorted(directory.iterdir()):
            if path.is_file() and path.suffix.lower() in _SUFFIXES:
                files.append(path)
    return files


def _chunk_document(path: Path) -> list[dict[str, Any]]:
    root = get_project_root()
    text = path.read_text(encoding="utf-8", errors="ignore")
    document_type = infer_document_type(path.name, text)
    synthetic = is_synthetic(text, path.name) or SYNTHETIC_SUBDIR in str(path)
    chunks: list[dict[str, Any]] = []
    for ordinal, chunk in enumerate(chunk_markdown(text), start=1):
        section = chunk.section
        if chunk.n_parts > 1:
            section = f"{chunk.section} (part {chunk.part}/{chunk.n_parts})"
        chunks.append(
            {
                "chunk_id": f"{path.stem}::c{ordinal}",
                "document_id": path.stem,
                "file_name": path.name,
                "document_type": document_type,
                "source": str(path.relative_to(root)),
                "page": ordinal,
                "section": section,
                "text": chunk.text,
                "synthetic": synthetic,
                "in_uploads": UPLOAD_SUBDIR in str(path),
            }
        )
    return chunks


def build_chunk_table() -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    for path in corpus_files():
        chunks.extend(_chunk_document(path))
    return chunks


def build_rag_index() -> dict[str, Any]:
    """(Re)build the hybrid index and write the artifact + metadata."""
    chunks = build_chunk_table()
    passages = [chunk["text"] for chunk in chunks]

    dense_vectors = encode_passages(passages)
    bm25 = BM25Index.build(passages) if passages else None
    availability = neural_availability()

    out_dir = index_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "version": INDEX_VERSION,
            "chunks": chunks,
            "dense_vectors": dense_vectors,
            "bm25": bm25,
        },
        out_dir / INDEX_FILE,
    )

    sections = sorted({(c["file_name"], c["section"]) for c in chunks})
    meta: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "index_version": INDEX_VERSION,
        "n_chunks": len(chunks),
        "n_documents": len({c["document_id"] for c in chunks}),
        "n_sections": len(sections),
        "corpus": sorted({c["file_name"] for c in chunks}),
        "document_types": sorted({c["document_type"] for c in chunks}),
        "indexed_dirs": [f"data/documents/{SYNTHETIC_SUBDIR}", f"data/documents/{UPLOAD_SUBDIR}"],
        "retrieval_stack": {
            "dense": "BAAI/bge-small-en-v1.5" if dense_vectors is not None else None,
            "dense_dim": int(dense_vectors.shape[1]) if dense_vectors is not None else None,
            "lexical": "Okapi BM25 (k1=1.5, b=0.75)",
            "fusion": "Reciprocal Rank Fusion (k=60)",
            "reranker": "Xenova/ms-marco-MiniLM-L-6-v2",
        },
        "neural": availability,
        "synthetic_corpus": all(c["synthetic"] for c in chunks) if chunks else True,
        "note": "Synthetic fixtures only; project reports and docs are excluded from evidence.",
        "artifact_dir": str(out_dir),
    }

    # Evaluate against the freshly built index: passing it in avoids
    # load_index() rebuilding recursively on a cold start.
    current = {
        "version": INDEX_VERSION,
        "chunks": chunks,
        "dense_vectors": dense_vectors,
        "bm25": bm25,
    }
    meta["retrieval_evaluation"] = evaluate_retrieval(index=current)
    (out_dir / METADATA_FILE).write_text(json.dumps(meta, indent=2), encoding="utf-8")
    logger.info("RAG index built: %d chunks from %d documents", meta["n_chunks"], meta["n_documents"])
    return meta


def load_index() -> dict[str, Any]:
    """Load the persisted index, rebuilding it when missing or stale."""
    path = index_dir() / INDEX_FILE
    if path.exists():
        try:
            index = joblib.load(path)
            if index.get("version") == INDEX_VERSION and index.get("chunks"):
                return index
        except Exception as exc:  # corrupt artifact
            logger.warning("RAG index unreadable (%s); rebuilding", exc)
    build_rag_index()
    return joblib.load(path)


def retrieve(
    query: str,
    top_k: int = 5,
    *,
    doc_types: list[str] | None = None,
    use_rerank: bool = True,
) -> list[dict[str, Any]]:
    """Hybrid retrieval entry point used by the API and the agents."""
    index = load_index()
    return search(
        query,
        index["chunks"],
        dense_vectors=index.get("dense_vectors"),
        bm25=index.get("bm25"),
        top_k=top_k,
        doc_types=doc_types,
        use_rerank=use_rerank,
    )


def answer_with_citations(
    query: str,
    top_k: int = 5,
    *,
    doc_types: list[str] | None = None,
) -> dict[str, Any]:
    """Retrieve, then generate a grounded answer with claim-level citations."""
    hits = retrieve(query, top_k=top_k, doc_types=doc_types)
    if not hits:
        return {
            "query": query,
            "answer": "Insufficient grounded evidence found in the document index.",
            "claims": [],
            "citations": [],
            "retrieved": [],
            "grounded": False,
            "generator": "none",
            "note": "No passage passed the retrieval threshold.",
        }
    answer: GroundedAnswer = build_answer(query, hits)
    payload = answer.to_dict()
    payload["coverage"] = document_coverage()
    return payload


def document_coverage() -> dict[str, Any]:
    """What the non-answering corpus can and cannot support (honesty guard)."""
    index = load_index()
    chunks = index["chunks"]
    return {
        "n_documents": len({c["document_id"] for c in chunks}),
        "document_types": sorted({c["document_type"] for c in chunks}),
        "all_synthetic": all(c["synthetic"] for c in chunks) if chunks else True,
        "note": "Synthetic fixtures are non-authoritative and cannot be cited as official policy.",
    }


def list_documents() -> list[dict[str, Any]]:
    """Corpus inventory for the Documents page."""
    index = load_index()
    by_document: dict[str, dict[str, Any]] = {}
    for chunk in index["chunks"]:
        entry = by_document.setdefault(
            chunk["document_id"],
            {
                "document_id": chunk["document_id"],
                "file_name": chunk["file_name"],
                "document_type": chunk["document_type"],
                "source": chunk["source"],
                "synthetic": chunk.get("synthetic", False),
                "in_uploads": chunk.get("in_uploads", False),
                "n_chunks": 0,
                "sections": [],
            },
        )
        entry["n_chunks"] += 1
        if chunk["section"] not in entry["sections"]:
            entry["sections"].append(chunk["section"])
    return sorted(by_document.values(), key=lambda item: item["file_name"])


def _gold_rank(ranking: list[int], chunks: list[dict[str, Any]], file_name: str, section: str) -> int | None:
    """1-based rank of the first chunk matching the gold file and section."""
    wanted = section.lower()
    for position, index in enumerate(ranking, start=1):
        chunk = chunks[index]
        if chunk["file_name"] != file_name:
            continue
        if wanted in chunk["section"].lower():
            return position
    return None


def _evaluate_variant(
    name: str,
    ranker,
    chunks: list[dict[str, Any]],
    top_k: int,
) -> dict[str, Any]:
    reciprocal_ranks: list[float] = []
    hits_at: dict[int, list[bool]] = {k: [] for k in (1, 3, top_k)}
    file_hits_at: dict[int, list[bool]] = {k: [] for k in (1, 3, top_k)}
    cases: list[dict[str, Any]] = []

    for query, file_name, section in RETRIEVAL_CASES:
        ranking = ranker(query)
        rank = _gold_rank(ranking, chunks, file_name, section)
        file_rank = next(
            (position for position, index in enumerate(ranking, start=1) if chunks[index]["file_name"] == file_name),
            None,
        )
        reciprocal_ranks.append(1.0 / rank if rank else 0.0)
        for k in hits_at:
            hits_at[k].append(bool(rank and rank <= k))
            file_hits_at[k].append(bool(file_rank and file_rank <= k))
        cases.append(
            {
                "query": query,
                "expected_file": file_name,
                "expected_section": section,
                "section_rank": rank,
                "file_rank": file_rank,
                "top_file": chunks[ranking[0]]["file_name"] if ranking else None,
                "top_section": chunks[ranking[0]]["section"] if ranking else None,
            }
        )

    n = len(RETRIEVAL_CASES)
    return {
        "variant": name,
        "n_queries": n,
        "mrr": float(np.mean(reciprocal_ranks)) if n else None,
        "section_recall": {str(k): float(np.mean(v)) if v else 0.0 for k, v in hits_at.items()},
        "file_recall": {str(k): float(np.mean(v)) if v else 0.0 for k, v in file_hits_at.items()},
        "cases": cases,
    }


def evaluate_retrieval(top_k: int = 5, index: dict[str, Any] | None = None) -> dict[str, Any]:
    """Ablation over the retrieval stack: dense / BM25 / fused / fused+reranked."""
    index = index or load_index()
    chunks = index["chunks"]
    dense = index.get("dense_vectors")
    bm25 = index.get("bm25")
    depth = max(top_k, 10)

    variants = {
        "dense_only": lambda query: dense_only_ranking(query, chunks, dense, depth),
        "bm25_only": lambda query: lexical_only_ranking(query, bm25, depth),
        "hybrid_rrf": lambda query: [
            next(i for i, c in enumerate(chunks) if c["chunk_id"] == hit["chunk_id"])
            for hit in search(query, chunks, dense_vectors=dense, bm25=bm25, top_k=depth, use_rerank=False)
        ],
        "hybrid_rrf_rerank": lambda query: [
            next(i for i, c in enumerate(chunks) if c["chunk_id"] == hit["chunk_id"])
            for hit in search(query, chunks, dense_vectors=dense, bm25=bm25, top_k=depth, use_rerank=True)
        ],
    }

    results = {name: _evaluate_variant(name, ranker, chunks, top_k) for name, ranker in variants.items()}
    primary = results["hybrid_rrf_rerank"]

    payload = {
        "evaluation_type": "gold_section_retrieval_benchmark",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_queries": primary["n_queries"],
        "n_chunks": len(chunks),
        "metrics": "MRR and Recall@k over 20 questions with gold document+section labels",
        "primary": {
            "variant": primary["variant"],
            "mrr": primary["mrr"],
            "section_recall_at_k": primary["section_recall"],
            "file_recall_at_k": primary["file_recall"],
        },
        "ablations": {
            name: {
                "mrr": result["mrr"],
                "section_recall_at_k": result["section_recall"],
                "file_recall_at_k": result["file_recall"],
            }
            for name, result in results.items()
        },
        "cases": primary["cases"],
        "limitation": (
            "Corpus is small and synthetic; absolute scores indicate wiring and rank quality, "
            "not performance on real procurement documents."
        ),
    }

    path = get_project_root() / "reports" / "metrics" / "rag_retrieval_evaluation.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


if __name__ == "__main__":
    print(json.dumps(build_rag_index(), indent=2)[:1500])
    demo = answer_with_citations("How quickly must a Severity 1 disruption be acknowledged?")
    print(demo["answer"])
