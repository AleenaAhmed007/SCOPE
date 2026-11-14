# SYNTHETIC DOCUMENT — Not an official contract, SLA or policy

## Inventory and Replenishment Policy
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
