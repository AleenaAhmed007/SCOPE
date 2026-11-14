"""Structure-aware markdown chunking for the SCOPE document corpus.

Unlike fixed-width character slicing, chunks are aligned to markdown
headings so every retrieval hit carries a meaningful `section` label
(useful for citations such as ``supplier_contract.md §4 Penalties``).
Oversized sections are split into overlapping windows that still inherit
the section title.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

DEFAULT_MAX_CHARS = 900
DEFAULT_OVERLAP = 150
_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_SYNTHETIC_MARKER = "SYNTHETIC DOCUMENT"


@dataclass(frozen=True)
class Section:
    """A contiguous markdown section with its heading trail."""

    title: str
    text: str


@dataclass(frozen=True)
class TextChunk:
    """A retrievable unit of text with section provenance."""

    section: str
    text: str
    part: int = 1
    n_parts: int = 1


def split_sections(markdown: str) -> list[Section]:
    """Split markdown into heading-delimited sections (H1/H2/H3 levels)."""
    sections: list[Section] = []
    title = "preamble"
    buffer: list[str] = []

    for line in markdown.splitlines():
        heading = _HEADING.match(line)
        if heading:
            if any(chunk.strip() for chunk in buffer):
                sections.append(Section(title=title, text="\n".join(buffer).strip()))
            title = heading.group(2).strip()
            buffer = []
            continue
        buffer.append(line)

    if any(chunk.strip() for chunk in buffer):
        sections.append(Section(title=title, text="\n".join(buffer).strip()))
    return sections


def chunk_markdown(
    markdown: str,
    *,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap: int = DEFAULT_OVERLAP,
) -> list[TextChunk]:
    """Chunk a markdown document on headings, then window long sections."""
    chunks: list[TextChunk] = []
    for section in split_sections(markdown):
        if len(section.text) <= max_chars:
            chunks.append(TextChunk(section=section.title, text=section.text))
            continue
        windows = _window(section.text, max_chars=max_chars, overlap=overlap)
        for part, window in enumerate(windows, start=1):
            chunks.append(
                TextChunk(
                    section=section.title,
                    text=window,
                    part=part,
                    n_parts=len(windows),
                )
            )
    return chunks


def _window(text: str, *, max_chars: int, overlap: int) -> list[str]:
    windows: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        windows.append(text[start:end].strip())
        if end == len(text):
            break
        start = max(0, end - overlap)
    return windows


def is_synthetic(markdown: str, file_name: str) -> bool:
    """Synthetic fixtures are labelled in the filename or the first lines."""
    head = markdown[:400].upper()
    return "SYNTHETIC" in file_name.upper() or _SYNTHETIC_MARKER in head
