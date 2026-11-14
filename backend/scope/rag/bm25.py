"""Okapi BM25 lexical ranking (no external dependency).

Implements the classic Robertson/Sparck-Jones formulation used for the
keyword half of SCOPE's hybrid retrieval. Kept dependency-free so the
retrieval stack degrades gracefully when no neural encoder is installed.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")

STOPWORDS = frozenset(
    """
    a an and are as at be been being but by can could did do does for from had has
    have how i if in into is it its may might must not of on or our shall should so
    such than that the their them then there these they this those to was were what
    when where which who why will with within would you your
    """.split()
)

# Light suffix normalisation so "shipments"/"shipment" and "delivered"/"delivery"
# do not compete as different terms. Deliberately conservative: no full stemmer.
_SUFFIXES = ("ments", "ment", "ings", "ing", "ies", "ers", "er", "ed", "es", "s")


def tokenize(text: str, *, drop_stopwords: bool = True) -> list[str]:
    """Lowercase alphanumeric tokens with light suffix normalisation."""
    raw = TOKEN_PATTERN.findall(text.lower())
    tokens: list[str] = []
    for token in raw:
        if drop_stopwords and token in STOPWORDS:
            continue
        if len(token) > 4:
            token = _strip_suffix(token)
        tokens.append(token)
    return tokens


def _strip_suffix(token: str) -> str:
    for suffix in _SUFFIXES:
        if token.endswith(suffix) and len(token) - len(suffix) >= 3:
            return token[: -len(suffix)]
    return token


@dataclass
class BM25Index:
    """Bag-of-terms BM25 index over a fixed corpus of documents."""

    k1: float = 1.5
    b: float = 0.75
    term_frequencies: list[Counter[str]] = field(default_factory=list)
    doc_lengths: list[int] = field(default_factory=list)
    document_frequency: Counter[str] = field(default_factory=Counter)
    n_documents: int = 0
    avg_doc_length: float = 0.0

    @classmethod
    def build(cls, documents: list[str], *, k1: float = 1.5, b: float = 0.75) -> "BM25Index":
        index = cls(k1=k1, b=b)
        for document in documents:
            tokens = tokenize(document)
            frequencies = Counter(tokens)
            index.term_frequencies.append(frequencies)
            index.doc_lengths.append(len(tokens))
            index.document_frequency.update(set(tokens))
        index.n_documents = len(documents)
        index.avg_doc_length = (
            sum(index.doc_lengths) / index.n_documents if index.n_documents else 0.0
        )
        return index

    def inverse_document_frequency(self, term: str) -> float:
        df = self.document_frequency.get(term, 0)
        if df == 0:
            return 0.0
        return math.log(1.0 + (self.n_documents - df + 0.5) / (df + 0.5))

    def scores(self, query: str) -> list[float]:
        """BM25 score for every document against the query."""
        terms = tokenize(query)
        if not terms or not self.n_documents:
            return [0.0] * self.n_documents
        average = self.avg_doc_length or 1.0
        results: list[float] = []
        for position, frequencies in enumerate(self.term_frequencies):
            length_norm = self.k1 * (1.0 - self.b + self.b * self.doc_lengths[position] / average)
            score = 0.0
            for term in terms:
                frequency = frequencies.get(term, 0)
                if not frequency:
                    continue
                idf = self.inverse_document_frequency(term)
                score += idf * (frequency * (self.k1 + 1.0)) / (frequency + length_norm)
            results.append(score)
        return results
