"""Text extraction for uploaded, text-based PDFs."""

from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError, PdfStreamError

MAX_PDF_PAGES = 500
MAX_EXTRACTED_CHARS = 1_000_000


def extract_pdf_markdown(content: bytes, source_name: str) -> tuple[str, int]:
    """Extract page-labelled text from a PDF; reject encrypted/scanned/oversized files."""
    if not content.startswith(b"%PDF-"):
        raise ValueError("The uploaded file is not a valid PDF.")
    try:
        reader = PdfReader(BytesIO(content), strict=False)
    except (PdfReadError, PdfStreamError, ValueError) as exc:
        raise ValueError("The PDF could not be parsed.") from exc
    if reader.is_encrypted:
        raise ValueError("Encrypted PDFs are not supported. Upload an unlocked copy.")
    if len(reader.pages) > MAX_PDF_PAGES:
        raise ValueError(f"PDF exceeds the {MAX_PDF_PAGES}-page upload limit.")

    pages: list[str] = []
    total_chars = 0
    for number, page in enumerate(reader.pages, start=1):
        try:
            text = (page.extract_text() or "").strip()
        except Exception as exc:  # malformed page content
            raise ValueError(f"Text extraction failed on PDF page {number}.") from exc
        if text:
            pages.append(f"## Page {number}\n\n{text}")
            total_chars += len(text)
            if total_chars > MAX_EXTRACTED_CHARS:
                raise ValueError("Extracted PDF text exceeds the 1 MB text limit.")
    if not pages:
        raise ValueError(
            "No selectable text was found. Scanned/image-only PDFs need OCR before upload."
        )
    markdown = (
        f"# Uploaded PDF: {source_name}\n\n"
        "Text extracted with pypdf. Page headings preserve source page references.\n\n"
        + "\n\n".join(pages)
        + "\n"
    )
    return markdown, len(reader.pages)
