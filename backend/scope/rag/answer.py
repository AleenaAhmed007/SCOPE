"""Grounded answer generation over retrieved passages.

Two generators share one output contract:

* ``extractive`` — deterministic; each claim is a sentence copied verbatim from
  a retrieved passage, carrying that passage's chunk id.
* ``llm`` — used only when ``SCOPE_LLM_BASE_URL`` is configured (any
  OpenAI-compatible ``/chat/completions`` endpoint). The model must return
  claims as JSON with explicit chunk ids; a claim citing an unknown chunk is
  kept but marked unresolvable so the Checker can reject it rather than letting
  a fabricated citation pass silently.

Every claim therefore has machine-checkable provenance: chunk ids, the cited
text, and the numbers it asserts.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Sequence

from scope.logging_config import setup_logging
from scope.rag.bm25 import tokenize

logger = setup_logging()

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_MAX_CLAIM_CHARS = 320
_DEFAULT_CLAIMS = 4


@dataclass
class Citation:
    index: int
    chunk_id: str
    document_id: str
    file_name: str
    document_type: str
    section: str
    page: int
    source: str
    synthetic: bool
    score: float


@dataclass
class Claim:
    """One asserted statement with the evidence it claims to rest on."""

    text: str
    citation_indices: list[int] = field(default_factory=list)
    chunk_ids: list[str] = field(default_factory=list)
    generator: str = "extractive"

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "citation_indices": self.citation_indices,
            "chunk_ids": self.chunk_ids,
            "generator": self.generator,
        }


@dataclass
class GroundedAnswer:
    query: str
    claims: list[Claim]
    citations: list[Citation]
    retrieved: list[dict[str, Any]]
    grounded: bool
    generator: str
    note: str = ""

    def render(self) -> str:
        if not self.claims:
            return "Insufficient grounded evidence was found in the document index."
        lines: list[str] = []
        for claim in self.claims:
            markers = "".join(f"[{i}]" for i in claim.citation_indices)
            lines.append(f"- {claim.text} {markers}".rstrip())
        body = "\n".join(lines)
        warning = (
            "\n\nRetrieved passages may include clearly labelled synthetic documents."
            if any(c.synthetic for c in self.citations)
            else ""
        )
        return f"{body}{warning}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "answer": self.render(),
            "claims": [claim.to_dict() for claim in self.claims],
            "citations": [
                {
                    "index": c.index,
                    "chunk_id": c.chunk_id,
                    "document_id": c.document_id,
                    "file_name": c.file_name,
                    "document_type": c.document_type,
                    "section": c.section,
                    "page": c.page,
                    "source": c.source,
                    "score": c.score,
                    "synthetic": c.synthetic,
                }
                for c in self.citations
            ],
            "retrieved": self.retrieved,
            "grounded": self.grounded,
            "generator": self.generator,
            "note": self.note,
        }


def _citation_from_hit(index: int, hit: dict[str, Any]) -> Citation:
    return Citation(
        index=index,
        chunk_id=str(hit.get("chunk_id", "")),
        document_id=str(hit.get("document_id", "")),
        file_name=str(hit.get("file_name", "")),
        document_type=str(hit.get("document_type", "")),
        section=str(hit.get("section", "")),
        page=int(hit.get("page", 0) or 0),
        source=str(hit.get("source", "")),
        synthetic=bool(hit.get("synthetic", False)),
        score=float(hit.get("score", 0.0) or 0.0),
    )


def _best_sentence(query_terms: set[str], text: str) -> str:
    """Sentence with the highest query-term overlap, verbatim from the passage."""
    sentences = [s.strip() for s in _SENTENCE_SPLIT.split(text) if s.strip()]
    if not sentences:
        return text.strip()[:_MAX_CLAIM_CHARS]
    scored = []
    for sentence in sentences:
        terms = set(tokenize(sentence))
        overlap = len(query_terms & terms)
        scored.append((overlap, len(terms), sentence))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return scored[0][2][:_MAX_CLAIM_CHARS]


def build_extractive_answer(
    query: str, hits: Sequence[dict[str, Any]], max_claims: int = _DEFAULT_CLAIMS
) -> GroundedAnswer:
    """Claim per passage: the passage sentence that best matches the query."""
    citations = [_citation_from_hit(i, hit) for i, hit in enumerate(hits, start=1)]
    query_terms = set(tokenize(query))
    claims: list[Claim] = []
    for citation, hit in zip(citations, hits):
        sentence = _best_sentence(query_terms, str(hit.get("text", "")))
        if not sentence:
            continue
        claims.append(
            Claim(
                text=sentence,
                citation_indices=[citation.index],
                chunk_ids=[citation.chunk_id],
                generator="extractive",
            )
        )
        if len(claims) >= max_claims:
            break
    return GroundedAnswer(
        query=query,
        claims=claims,
        citations=citations,
        retrieved=list(hits),
        grounded=bool(claims),
        generator="extractive",
        note="Sentences are copied verbatim from retrieved passages; no language model was used.",
    )


def llm_config() -> dict[str, str] | None:
    """Return LLM connection settings, or None when not configured."""
    base = os.getenv("SCOPE_LLM_BASE_URL", "").rstrip("/")
    model = os.getenv("SCOPE_LLM_MODEL", "")
    if not base or not model:
        return None
    return {
        "base_url": base,
        "model": model,
        "api_key": os.getenv("SCOPE_LLM_API_KEY", ""),
        "timeout": os.getenv("SCOPE_LLM_TIMEOUT", "45"),
    }


SYSTEM_PROMPT = (
    "You are a supply-chain evidence assistant. Answer ONLY with claims that are "
    "directly supported by the numbered passages. Return strict JSON: "
    '{"claims":[{"text":"...","chunk_ids":["<passage id>"]}]}. '
    "Every claim must cite at least one passage id exactly as given. "
    "Never invent document names, clauses, numbers or ids. If the passages do not "
    "answer the question, return {\"claims\":[]}."
)


def _call_llm(config: dict[str, str], prompt: str) -> str:
    payload = json.dumps(
        {
            "model": config["model"],
            "temperature": 0.0,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{config['base_url']}/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            **({"Authorization": f"Bearer {config['api_key']}"} if config.get("api_key") else {}),
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=float(config["timeout"])) as response:
        body = json.loads(response.read().decode("utf-8"))
    return body["choices"][0]["message"]["content"]


def _parse_claims(raw: str) -> list[dict[str, Any]]:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        return []
    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return []
    claims = parsed.get("claims")
    return claims if isinstance(claims, list) else []


def build_llm_answer(
    query: str, hits: Sequence[dict[str, Any]], max_claims: int = _DEFAULT_CLAIMS
) -> GroundedAnswer | None:
    """Grounded LLM answer, or None when unconfigured/unsuccessful."""
    config = llm_config()
    if config is None or not hits:
        return None

    citations = [_citation_from_hit(i, hit) for i, hit in enumerate(hits, start=1)]
    by_chunk = {citation.chunk_id: citation for citation in citations}
    passages = "\n\n".join(
        f"[{citation.chunk_id}] ({citation.file_name} § {citation.section})\n{hit.get('text', '')}"
        for citation, hit in zip(citations, hits)
    )
    prompt = f"Question: {query}\n\nPassages:\n{passages}"

    try:
        raw_claims = _parse_claims(_call_llm(config, prompt))
    except Exception as exc:  # network, auth, malformed response
        logger.warning("LLM generation failed (%s); falling back to extractive", exc)
        return None

    claims: list[Claim] = []
    for item in raw_claims[:max_claims]:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text", "")).strip()
        if not text:
            continue
        chunk_ids = [str(cid) for cid in item.get("chunk_ids", []) if isinstance(cid, str)]
        resolved = [by_chunk[cid] for cid in chunk_ids if cid in by_chunk]
        claims.append(
            Claim(
                text=text,
                citation_indices=[c.index for c in resolved],
                chunk_ids=chunk_ids,
                generator=f"llm:{config['model']}",
            )
        )
    if not claims:
        return None
    return GroundedAnswer(
        query=query,
        claims=claims,
        citations=citations,
        retrieved=list(hits),
        grounded=True,
        generator=f"llm:{config['model']}",
        note="Claims were generated by a language model and must pass the Checker.",
    )


def build_answer(query: str, hits: Sequence[dict[str, Any]], max_claims: int = _DEFAULT_CLAIMS) -> GroundedAnswer:
    """LLM answer when configured, otherwise the deterministic extractive answer."""
    return build_llm_answer(query, hits, max_claims) or build_extractive_answer(query, hits, max_claims)
