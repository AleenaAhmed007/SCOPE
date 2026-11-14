"""Synthetic RAG fixtures and helpers for the evidence corpus.

This module defines synthetic development fixtures, not real supplier
contracts or official policies. The corpus is deliberately small but
structured: each document declares its type, authority and issuing function,
and is divided into sections so retrieval can cite `document § section`.

Official extracts and uploads live in sibling directories. The project's own reports and
documentation are deliberately excluded — citing them would be circular.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scope.config.loader import get_project_root

DOCUMENT_DIR = Path("data") / "documents"
SYNTHETIC_SUBDIR = "synthetic"
OFFICIAL_SUBDIR = "official"
UPLOAD_SUBDIR = "uploads"

_HEADER = "# SYNTHETIC DOCUMENT — Not an official contract, SLA or policy\n\n"


@dataclass(frozen=True)
class SyntheticDocument:
    """Metadata for one synthetic fixture."""

    file_name: str
    doc_type: str
    title: str
    body: str


def _doc(file_name: str, doc_type: str, title: str, body: str) -> SyntheticDocument:
    return SyntheticDocument(file_name=file_name, doc_type=doc_type, title=title, body=body)


SYNTHETIC_DOCUMENTS: tuple[SyntheticDocument, ...] = (
    _doc(
        "SYNTHETIC_shipping_sla.md",
        "sla",
        "Shipping Service Level Agreement",
        """
## 1. Delivery windows and buffers
Standard air shipments should arrive within the scheduled delivery window. Ocean
shipments carry higher transit variability, so a contingency buffer of 7 days is
recommended when planning against the scheduled delivery date.

## 2. Late delivery definition
A shipment is late when the delivered-to-client date is later than the scheduled
delivery date. Lateness is measured in whole days and recorded against the vendor
that received the purchase order, not the freight forwarder.

## 3. Delay notification
Vendors must notify the procurement office within 48 hours of learning of any
expected delay. Notification does not remove the late-delivery classification; it
only changes the escalation path.

## 4. Mode selection
Critical ARV product shipments should prefer Air mode when clinically urgent.
Ocean mode is preferred for high-volume, low-urgency replenishment where the
7-day contingency buffer can absorb transit variance.

## 5. Documentation of delivery
Proof of delivery must record the actual delivery date. Placeholder values such as
"Date Not Captured" are treated as missing documentation and are excluded from
service-level measurement rather than counted as on-time.
""",
    ),
    _doc(
        "SYNTHETIC_procurement_policy.md",
        "policy",
        "Procurement Delay Escalation Policy",
        """
## 1. Escalation trigger
If a vendor late rate exceeds 20% over the trailing 50 shipments, procurement must
escalate the vendor to category management and open a corrective action review.

## 2. Purchase order capture
Purchase orders sent to vendors must be captured with a valid date. Placeholder
values such as "Date Not Captured" require a data-quality follow-up and must not
be back-filled with an assumed date.

## 3. Fulfilment routes
Direct Drop and RDC fulfilment have different operational risk profiles. Direct
Drop shipments bypass central consolidation and therefore carry longer and more
variable delivery durations than From RDC shipments.

## 4. Evidence requirements
Evidence for disruption claims must cite shipment identifiers and document
sources. A claim without a retrievable source is recorded as an assumption, not
as a finding.

## 5. Investigation cadence
Vendor performance reviews are run quarterly. A vendor-quarter is only reviewed
when it contains at least 5 shipments; smaller samples are marked insufficient
history rather than analysed.
""",
    ),
    _doc(
        "SYNTHETIC_vendor_compliance.md",
        "compliance",
        "Vendor Compliance Checklist",
        """
## 1. Manufacturing traceability
Manufacturing site traceability is required for all line items. A shipment whose
manufacturing site is unknown cannot be audited against the vendor agreement.

## 2. Freight cost recording
Freight cost fields may be invoiced separately. Missing freight cost must not be
treated as zero cost without confirmation from the logistics team.

## 3. Inventory data caution
Inventory fields in analytical datasets may be augmented. They must not be
treated as a warehouse system of record without provenance validation, and
derived stockout flags must not be used as model features.

## 4. Anomaly interpretation
Anomaly scores are investigative signals, not automatic proof of fraud or of a
disruption. A flagged record requires human review before any contractual action.

## 5. Data quality ownership
Data-quality defects are raised to the analytics owner. Unresolved defects are
listed in the investigation report rather than silently corrected.
""",
    ),
    _doc(
        "SYNTHETIC_supplier_agreement.md",
        "contract",
        "Master Supplier Agreement (Delivery Terms)",
        """
## 1. Lead-time commitments
The supplier commits to the lead time stated on each purchase order. Air freight
lead time is committed at 45 days; ocean freight lead time is committed at 120
days, measured from purchase order dispatch to client delivery.

## 2. Late delivery penalties
A late delivery attracts a service credit of 2% of line item value per commenced
week of delay, capped at 10% of the line item value. Credits are applied to the
next invoice and do not extinguish the obligation to deliver.

## 3. Repeated failure
Three or more late deliveries within a rolling 90-day window are treated as a
material breach and entitle the buyer to require a remediation plan within 14 days.

## 4. Force majeure
Force majeure relief applies only to events outside the supplier's reasonable
control and requires written notice within 5 business days. Port congestion and
customs backlogs are expressly excluded from force majeure relief.

## 5. Audit rights
The buyer may audit delivery records on 10 business days' notice. The supplier
must retain shipment and delivery records for 3 years from the delivery date.
""",
    ),
    _doc(
        "SYNTHETIC_inventory_policy.md",
        "policy",
        "Inventory and Replenishment Policy",
        """
## 1. Stock cover target
Total network stock cover should be maintained at 45 days of forecast demand.
Stock cover below 30 days is flagged as an inventory risk and below 15 days is an
inventory emergency requiring weekly review.

## 2. Reorder level
The reorder level is set at lead-time demand plus safety stock. When opening stock
falls below the reorder level, replenishment must be triggered in the same
planning cycle.

## 3. Stockout definition
A stockout occurs when opening stock is insufficient to cover the line item
quantity of an order. The stockout flag is a derived quantity and must be
recomputed from opening stock and quantity rather than trusted as a source field.

## 4. Replenishment escalation
A replenishment that is triggered but not dispatched within 5 business days is
escalated to the supply planning lead.

## 5. Lead-time review
Inventory lead times are reviewed every quarter. A lead time that has been
constant across two consecutive quarters is treated as a data-quality defect
until validated against the vendor's stated lead time.
""",
    ),
    _doc(
        "SYNTHETIC_escalation_matrix.md",
        "policy",
        "Disruption Escalation Matrix",
        """
## 1. Severity tiers
Severity 1 covers a confirmed stockout or a late shipment affecting first-line
therapy. Severity 2 covers a late rate above 20% for a vendor. Severity 3 covers
isolated delays with no clinical impact.

## 2. Response times
A Severity 1 disruption requires acknowledgement within 24 hours and a mitigation
plan within 48 hours. Severity 2 requires a review within 5 business days.
Severity 3 is handled in the next scheduled category review.

## 3. Notification chain
The procurement officer notifies the category manager, who notifies the supply
planning lead. First-line therapy impacts additionally require notification of the
programme director.

## 4. Mandatory evidence
Each escalation record must reference the shipment identifiers, the measured late
rate, the affected product groups and the governing policy clause.
""",
    ),
    _doc(
        "SYNTHETIC_cold_chain_policy.md",
        "policy",
        "Cold Chain and Temperature Control Policy",
        """
## 1. Temperature range
Temperature-controlled products must be maintained between 2 and 8 degrees
Celsius for the entire journey, including consolidation and customs holding.

## 2. Excursion handling
A temperature excursion longer than 2 hours requires quarantine of the batch and
a quality assessment before release. Excursions must be recorded against the
shipment even when the delivery itself was on time.

## 3. Air preference
Temperature-sensitive and clinically urgent shipments should use Air mode. Ocean
transit is permitted only with validated reefer containers and a documented
7-day contingency buffer.

## 4. Recalled or rejected batches
A rejected batch is excluded from delivery performance measurement when rejection
is caused by temperature excursion rather than by schedule adherence.
""",
    ),
    _doc(
        "SYNTHETIC_quality_policy.md",
        "compliance",
        "Quality and Defect Management Policy",
        """
## 1. Defect rate threshold
A vendor defect rate above 3% of inspected units over a quarter triggers a quality
review. Defect rate is captured by the quality function and is not present in the
operational shipment dataset.

## 2. Inspection sampling
Incoming batches are sampled using the general inspection level agreed in the
vendor quality agreement. Sampling records are retained with the batch record.

## 3. Release decision
A batch may only be released when identity, potency and temperature records are
complete. A missing temperature record blocks release.

## 4. Corrective actions
Repeated defects require a corrective and preventive action plan within 30 days,
with effectiveness verification at the following quarter.
""",
    ),
)


def synthetic_doc_dir() -> Path:
    return get_project_root() / DOCUMENT_DIR / SYNTHETIC_SUBDIR


def upload_doc_dir() -> Path:
    return get_project_root() / DOCUMENT_DIR / UPLOAD_SUBDIR


def ensure_synthetic_docs() -> Path:
    """Write (or refresh) the synthetic fixtures and return both corpus dirs' root.

    Returns the ``data/documents`` directory; callers enumerate documents via
    :func:`iter_corpus_documents`.
    """
    doc_dir = synthetic_doc_dir()
    doc_dir.mkdir(parents=True, exist_ok=True)
    (get_project_root() / DOCUMENT_DIR / OFFICIAL_SUBDIR).mkdir(parents=True, exist_ok=True)
    upload_doc_dir().mkdir(parents=True, exist_ok=True)

    (doc_dir / "README.md").write_text(
        "# Synthetic documents\n\n"
        "These files are **synthetic** development fixtures, not real supplier "
        "contracts or official policies. They exist so RAG retrieval, citations "
        "and claim verification can be exercised end to end.\n\n"
        "| File | Type |\n|---|---|\n"
        + "\n".join(f"| {d.file_name} | {d.doc_type} |" for d in SYNTHETIC_DOCUMENTS)
        + "\n\nThis directory contains synthetic fixtures. Official-source "
        "extracts live in `official/`; user uploads live in `uploads/`. Project "
        "reports and documentation are excluded to avoid "
        "circular citations.\n",
        encoding="utf-8",
    )

    for document in SYNTHETIC_DOCUMENTS:
        content = f"{_HEADER}## {document.title}\n{document.body.strip()}\n"
        (doc_dir / document.file_name).write_text(content, encoding="utf-8")

    return get_project_root() / DOCUMENT_DIR


def infer_document_type(file_name: str, text: str) -> str:
    """Best-effort document type from filename, then content keywords."""
    name = file_name.lower()
    for token, doc_type in (
        ("contract", "contract"),
        ("agreement", "contract"),
        ("sla", "sla"),
        ("service_level", "sla"),
        ("compliance", "compliance"),
        ("quality", "compliance"),
        ("policy", "policy"),
        ("matrix", "policy"),
    ):
        if token in name:
            return doc_type
    lowered = text.lower()
    for token, doc_type in (
        ("agreement", "contract"),
        ("service level", "sla"),
        ("policy", "policy"),
        ("compliance", "compliance"),
    ):
        if token in lowered:
            return doc_type
    return "policy"
