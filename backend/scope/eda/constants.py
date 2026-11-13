"""Column groups and known placeholders for Phase 01 EDA."""

from __future__ import annotations

DATE_COLUMNS: list[str] = [
    "PQ First Sent to Client Date",
    "PO Sent to Vendor Date",
    "Scheduled Delivery Date",
    "Delivered to Client Date",
    "Delivery Recorded Date",
    "Inventory_Date",
]

DATE_PLACEHOLDERS: frozenset[str] = frozenset(
    {
        "N/A - From RDC",
        "Date Not Captured",
        "Pre-PQ Process",
    }
)

NUMERICAL_COLUMNS: list[str] = [
    "Line Item Quantity",
    "Line Item Value",
    "Pack Price",
    "Unit Price",
    "Weight (Kilograms)",
    "Freight Cost (USD)",
    "Line Item Insurance (USD)",
    "Inventory_Opening_Stock",
    "Inventory_Stock_In",
    "Inventory_Stock_Out",
    "Inventory_Closing_Stock",
    "Inventory_Reorder_Level",
    "Inventory_Shortage_Quantity",
]

# Columns that may contain non-numeric text and need coercion
DIRTY_NUMERIC_COLUMNS: list[str] = [
    "Weight (Kilograms)",
    "Freight Cost (USD)",
]

CATEGORICAL_COLUMNS: list[str] = [
    "Country",
    "Managed By",
    "Fulfill Via",
    "Vendor INCO Term",
    "Shipment Mode",
    "Product Group",
    "Sub Classification",
    "Vendor",
    "Manufacturing Site",
    "Brand",
    "Dosage Form",
]

INVENTORY_COLUMNS: list[str] = [
    "Inventory_Product_Key",
    "Inventory_Warehouse_ID",
    "Inventory_Date",
    "Inventory_Opening_Stock",
    "Inventory_Stock_In",
    "Inventory_Stock_Out",
    "Inventory_Closing_Stock",
    "Inventory_Reorder_Level",
    "Inventory_Lead_Time_Days",
    "Inventory_Stockout_Flag",
    "Inventory_Shortage_Quantity",
    "Inventory_Replenishment_Triggered",
]

IDENTIFIER_COLUMNS: list[str] = [
    "ID",
    "Project Code",
    "PQ #",
    "PO / SO #",
    "ASN/DN #",
]

# Business meanings — Unknown when not confirmed
COLUMN_MEANINGS: dict[str, str] = {
    "ID": "Unique shipment/line-item identifier",
    "Project Code": "Supply-chain project identifier",
    "PQ #": "Price quote number",
    "PO / SO #": "Purchase order / sales order number",
    "ASN/DN #": "Advanced shipping notice / delivery note number",
    "Country": "Destination country",
    "Managed By": "Managing organization / office",
    "Fulfill Via": "Fulfillment channel (e.g. Direct Drop, RDC)",
    "Vendor INCO Term": "Incoterms governing vendor shipment responsibility",
    "Shipment Mode": "Transport mode (Air, Ocean, Truck, etc.)",
    "PQ First Sent to Client Date": "Date PQ was first sent to client (may contain process placeholders)",
    "PO Sent to Vendor Date": "Date PO was sent to vendor (may contain RDC / not-captured placeholders)",
    "Scheduled Delivery Date": "Planned delivery date to client",
    "Delivered to Client Date": "Actual delivery date to client",
    "Delivery Recorded Date": "Date delivery was recorded in the system",
    "Product Group": "High-level product category",
    "Sub Classification": "Product sub-classification",
    "Vendor": "Supplier / vendor name",
    "Item Description": "Full product/item description",
    "Molecule/Test Type": "Active molecule or diagnostic test type",
    "Brand": "Product brand",
    "Dosage": "Dosage strength",
    "Dosage Form": "Formulation / dosage form",
    "Unit of Measure (Per Pack)": "Units contained in one pack",
    "Line Item Quantity": "Ordered / shipped quantity for the line item",
    "Line Item Value": "Monetary value of the line item",
    "Pack Price": "Price per pack",
    "Unit Price": "Price per unit",
    "Manufacturing Site": "Manufacturing site name",
    "First Line Designation": "Whether item is designated first-line therapy/product",
    "Weight (Kilograms)": "Shipment weight; may contain cross-reference text",
    "Freight Cost (USD)": "Freight cost; may contain inclusion / cross-reference text",
    "Line Item Insurance (USD)": "Insurance cost for the line item",
    "Inventory_Product_Key": "Augmented inventory product key (provenance unverified)",
    "Inventory_Warehouse_ID": "Augmented warehouse identifier (provenance unverified)",
    "Inventory_Date": "Augmented inventory snapshot date (provenance unverified)",
    "Inventory_Opening_Stock": "Augmented opening stock (provenance unverified)",
    "Inventory_Stock_In": "Augmented stock-in quantity (provenance unverified)",
    "Inventory_Stock_Out": "Augmented stock-out quantity (provenance unverified)",
    "Inventory_Closing_Stock": "Augmented closing stock (provenance unverified)",
    "Inventory_Reorder_Level": "Augmented reorder threshold (provenance unverified)",
    "Inventory_Lead_Time_Days": "Augmented lead time in days (provenance unverified)",
    "Inventory_Stockout_Flag": "Augmented stockout indicator (provenance unverified)",
    "Inventory_Shortage_Quantity": "Augmented shortage quantity (provenance unverified)",
    "Inventory_Replenishment_Triggered": "Augmented replenishment trigger flag (provenance unverified)",
}
