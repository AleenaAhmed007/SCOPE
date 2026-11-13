"""Synthetic supply-chain documents for RAG development (clearly labeled)."""

from __future__ import annotations

from pathlib import Path

from scope.config.loader import get_project_root

SYNTHETIC_DOCS: dict[str, str] = {
    "SYNTHETIC_shipping_sla.md": """# SYNTHETIC DOCUMENT — Not an official supplier contract

## Shipping Service Level Agreement (Synthetic)

1. Standard air shipments should arrive within the scheduled delivery window.
2. Ocean shipments may experience longer variability; contingency buffers of 7 days are recommended.
3. Vendors must notify the procurement office within 48 hours of any expected delay.
4. Late delivery is defined as delivery after the Scheduled Delivery Date.
5. Critical ARV product shipments should prefer Air mode when clinically urgent.
""",
    "SYNTHETIC_procurement_policy.md": """# SYNTHETIC DOCUMENT — Not an official policy

## Procurement Delay Escalation Policy (Synthetic)

- If a vendor late rate exceeds 20% over the trailing 50 shipments, escalate to category management.
- Purchase orders sent to vendors should be captured; placeholder values such as Date Not Captured require data-quality follow-up.
- Direct Drop and RDC fulfillment have different operational risk profiles.
- Evidence for disruption claims must cite shipment IDs and document sources.
""",
    "SYNTHETIC_vendor_compliance.md": """# SYNTHETIC DOCUMENT — Not official compliance guidance

## Vendor Compliance Checklist (Synthetic)

- Manufacturing site traceability is required for all line items.
- Freight cost fields may be invoiced separately; do not treat missing freight as zero cost without confirmation.
- Inventory fields in analytical datasets may be augmented; do not treat them as warehouse system-of-record without provenance validation.
- Anomaly scores are investigative signals, not automatic proof of fraud.
""",
}


def ensure_synthetic_docs() -> Path:
    root = get_project_root()
    doc_dir = root / "data" / "documents" / "synthetic"
    doc_dir.mkdir(parents=True, exist_ok=True)
    readme = doc_dir / "README.md"
    readme.write_text(
        "# Synthetic documents\n\nThese files are **synthetic** development fixtures, "
        "not real supplier contracts or official policies.\n",
        encoding="utf-8",
    )
    for name, content in SYNTHETIC_DOCS.items():
        (doc_dir / name).write_text(content, encoding="utf-8")
    return doc_dir
