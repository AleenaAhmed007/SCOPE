# Data Dictionary — SCMS_with_inventory.csv

Generated during Phase 01 EDA. Meanings marked Unknown/Needs confirmation are intentional.

Inventory_* fields are treated as **unverified augmented data**.

## `ID`

- **Data type:** `int64`
- **Business meaning:** Unique shipment/line-item identifier
- **Missing %:** 0.0
- **Unique count:** 10324
- **Example values:** ['1', '3', '4', '15', '16']
- **Identifier:** True
- **ML suitability:** No — identifier
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Project Code`

- **Data type:** `object`
- **Business meaning:** Supply-chain project identifier
- **Missing %:** 0.0
- **Unique count:** 142
- **Example values:** ['100-CI-T01', '108-VN-T01', '112-NG-T01', '110-ZM-T01', '109-TZ-T01']
- **Identifier:** True
- **ML suitability:** No — identifier
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `PQ #`

- **Data type:** `object`
- **Business meaning:** Price quote number
- **Missing %:** 0.0
- **Unique count:** 1237
- **Example values:** ['Pre-PQ Process', 'FPQ-4587', 'FPQ-12051', 'FPQ-14827', 'FPQ-9066']
- **Identifier:** True
- **ML suitability:** No — identifier
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `PO / SO #`

- **Data type:** `object`
- **Business meaning:** Purchase order / sales order number
- **Missing %:** 0.0
- **Unique count:** 6233
- **Example values:** ['SCMS-4', 'SCMS-13', 'SCMS-20', 'SCMS-78', 'SCMS-81']
- **Identifier:** True
- **ML suitability:** No — identifier
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `ASN/DN #`

- **Data type:** `object`
- **Business meaning:** Advanced shipping notice / delivery note number
- **Missing %:** 0.0
- **Unique count:** 7030
- **Example values:** ['ASN-8', 'ASN-85', 'ASN-14', 'ASN-50', 'ASN-55']
- **Identifier:** True
- **ML suitability:** No — identifier
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** medium — may be unavailable at prediction time; confirm timing

## `Country`

- **Data type:** `object`
- **Business meaning:** Destination country
- **Missing %:** 0.0
- **Unique count:** 43
- **Example values:** ["Côte d'Ivoire", 'Vietnam', 'Nigeria', 'Zambia', 'Tanzania']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Managed By`

- **Data type:** `object`
- **Business meaning:** Managing organization / office
- **Missing %:** 0.0
- **Unique count:** 4
- **Example values:** ['PMO - US', 'South Africa Field Office', 'Haiti Field Office', 'Ethiopia Field Office']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Fulfill Via`

- **Data type:** `object`
- **Business meaning:** Fulfillment channel (e.g. Direct Drop, RDC)
- **Missing %:** 0.0
- **Unique count:** 2
- **Example values:** ['Direct Drop', 'From RDC']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Vendor INCO Term`

- **Data type:** `object`
- **Business meaning:** Incoterms governing vendor shipment responsibility
- **Missing %:** 0.0
- **Unique count:** 8
- **Example values:** ['EXW', 'FCA', 'DDU', 'CIP', 'DDP']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Shipment Mode`

- **Data type:** `object`
- **Business meaning:** Transport mode (Air, Ocean, Truck, etc.)
- **Missing %:** 3.487
- **Unique count:** 4
- **Example values:** ['Air', 'Truck', 'Air Charter', 'Ocean']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `PQ First Sent to Client Date`

- **Data type:** `object`
- **Business meaning:** Date PQ was first sent to client (may contain process placeholders)
- **Missing %:** 0.0
- **Unique count:** 765
- **Example values:** ['Pre-PQ Process', 'Date Not Captured', '11/18/09', '05/03/2013', '8/19/14']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `PO Sent to Vendor Date`

- **Data type:** `object`
- **Business meaning:** Date PO was sent to vendor (may contain RDC / not-captured placeholders)
- **Missing %:** 0.0
- **Unique count:** 897
- **Example values:** ['Date Not Captured', '11/13/06', '12/01/2006', '12/22/06', '01/10/2007']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Scheduled Delivery Date`

- **Data type:** `object`
- **Business meaning:** Planned delivery date to client
- **Missing %:** 0.0
- **Unique count:** 2006
- **Example values:** ['02-Jun-06', '14-Nov-06', '27-Aug-06', '01-Sept-06', '11-Aug-06']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Delivered to Client Date`

- **Data type:** `object`
- **Business meaning:** Actual delivery date to client
- **Missing %:** 0.0
- **Unique count:** 2093
- **Example values:** ['02-Jun-06', '14-Nov-06', '27-Aug-06', '01-Sept-06', '11-Aug-06']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Unknown / Needs confirmation
- **Leakage risk:** high — often known only after delivery / outcome

## `Delivery Recorded Date`

- **Data type:** `object`
- **Business meaning:** Date delivery was recorded in the system
- **Missing %:** 0.0
- **Unique count:** 2042
- **Example values:** ['02-Jun-06', '14-Nov-06', '27-Aug-06', '01-Sept-06', '11-Aug-06']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Unknown / Needs confirmation
- **Leakage risk:** high — often known only after delivery / outcome

## `Product Group`

- **Data type:** `object`
- **Business meaning:** High-level product category
- **Missing %:** 0.0
- **Unique count:** 5
- **Example values:** ['HRDT', 'ARV', 'ACT', 'MRDT', 'ANTM']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Sub Classification`

- **Data type:** `object`
- **Business meaning:** Product sub-classification
- **Missing %:** 0.0
- **Unique count:** 6
- **Example values:** ['HIV test', 'Pediatric', 'Adult', 'HIV test - Ancillary', 'ACT']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Vendor`

- **Data type:** `object`
- **Business meaning:** Supplier / vendor name
- **Missing %:** 0.0
- **Unique count:** 73
- **Example values:** ['RANBAXY Fine Chemicals LTD.', 'Aurobindo Pharma Limited', 'Abbott GmbH & Co. KG', 'SUN PHARMACEUTICAL INDUSTRIES LTD (RANBAXY LABORATORIES LIMITED)', 'MERCK SHARP & DOHME IDEA GMBH (FORMALLY MERCK SHARP & DOHME B.V.)']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Item Description`

- **Data type:** `object`
- **Business meaning:** Full product/item description
- **Missing %:** 0.0
- **Unique count:** 184
- **Example values:** ['HIV, Reveal G3 Rapid HIV-1 Antibody Test, 30 Tests', 'Nevirapine 10mg/ml, oral suspension, Bottle, 240 ml', 'HIV 1/2, Determine Complete HIV Kit, 100 Tests', 'Lamivudine 150mg, tablets, 60 Tabs', 'Stavudine 30mg, capsules, 60 Caps']
- **Identifier:** False
- **ML suitability:** Maybe — text feature / embedding later; high cardinality
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Molecule/Test Type`

- **Data type:** `object`
- **Business meaning:** Active molecule or diagnostic test type
- **Missing %:** 0.0
- **Unique count:** 86
- **Example values:** ['HIV, Reveal G3 Rapid HIV-1 Antibody Test', 'Nevirapine', 'HIV 1/2, Determine Complete HIV Kit', 'Lamivudine', 'Stavudine']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Brand`

- **Data type:** `object`
- **Business meaning:** Product brand
- **Missing %:** 0.0
- **Unique count:** 48
- **Example values:** ['Reveal', 'Generic', 'Determine', 'Stocrin/Sustiva', 'Aluvia']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Dosage`

- **Data type:** `object`
- **Business meaning:** Dosage strength
- **Missing %:** 16.8152
- **Unique count:** 54
- **Example values:** ['10mg/ml', '150mg', '30mg', '200mg', '200/50mg']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Dosage Form`

- **Data type:** `object`
- **Business meaning:** Formulation / dosage form
- **Missing %:** 0.0
- **Unique count:** 17
- **Example values:** ['Test kit', 'Oral suspension', 'Tablet', 'Capsule', 'Oral solution']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Unit of Measure (Per Pack)`

- **Data type:** `int64`
- **Business meaning:** Units contained in one pack
- **Missing %:** 0.0
- **Unique count:** 31
- **Example values:** ['30', '240', '100', '60', '90']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Line Item Quantity`

- **Data type:** `int64`
- **Business meaning:** Ordered / shipped quantity for the line item
- **Missing %:** 0.0
- **Unique count:** 5065
- **Example values:** ['19', '1000', '500', '31920', '38000']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Line Item Value`

- **Data type:** `float64`
- **Business meaning:** Monetary value of the line item
- **Missing %:** 0.0
- **Unique count:** 8741
- **Example values:** ['551.0', '6200.0', '40000.0', '127360.8', '121600.0']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Pack Price`

- **Data type:** `float64`
- **Business meaning:** Price per pack
- **Missing %:** 0.0
- **Unique count:** 1175
- **Example values:** ['29.0', '6.2', '80.0', '3.99', '3.2']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Unit Price`

- **Data type:** `float64`
- **Business meaning:** Price per unit
- **Missing %:** 0.0
- **Unique count:** 183
- **Example values:** ['0.97', '0.03', '0.8', '0.07', '0.05']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Manufacturing Site`

- **Data type:** `object`
- **Business meaning:** Manufacturing site name
- **Missing %:** 0.0
- **Unique count:** 88
- **Example values:** ['Ranbaxy Fine Chemicals LTD', 'Aurobindo Unit III, India', 'ABBVIE GmbH & Co.KG Wiesbaden', 'Ranbaxy, Paonta Shahib, India', 'MSD South Granville Australia']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `First Line Designation`

- **Data type:** `object`
- **Business meaning:** Whether item is designated first-line therapy/product
- **Missing %:** 0.0
- **Unique count:** 2
- **Example values:** ['Yes', 'No']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Weight (Kilograms)`

- **Data type:** `object`
- **Business meaning:** Shipment weight; may contain cross-reference text
- **Missing %:** 0.0
- **Unique count:** 4688
- **Example values:** ['13', '358', '171', '1855', '7590']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Unknown / Needs confirmation
- **Leakage risk:** medium — may be unavailable at prediction time; confirm timing

## `Freight Cost (USD)`

- **Data type:** `object`
- **Business meaning:** Freight cost; may contain inclusion / cross-reference text
- **Missing %:** 0.0
- **Unique count:** 6733
- **Example values:** ['780.34', '4521.5', '1653.78', '16007.06', '45450.08']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Unknown / Needs confirmation
- **Leakage risk:** medium — may be unavailable at prediction time; confirm timing

## `Line Item Insurance (USD)`

- **Data type:** `float64`
- **Business meaning:** Insurance cost for the line item
- **Missing %:** 2.7799
- **Unique count:** 6722
- **Example values:** ['192.0', '128.0', '224.93', '3.07', '65.75']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** medium — may be unavailable at prediction time; confirm timing

## `Inventory_Product_Key`

- **Data type:** `object`
- **Business meaning:** Augmented inventory product key (provenance unverified)
- **Missing %:** 0.0
- **Unique count:** 184
- **Example values:** ['HIV, Reveal G3 Rapid HIV-1 Antibody Test, 30 Tests', 'Nevirapine 10mg/ml, oral suspension, Bottle, 240 ml', 'HIV 1/2, Determine Complete HIV Kit, 100 Tests', 'Lamivudine 150mg, tablets, 60 Tabs', 'Stavudine 30mg, capsules, 60 Caps']
- **Identifier:** False
- **ML suitability:** Caution — unverified augmented inventory field
- **Availability time:** Unknown / Needs confirmation
- **Leakage risk:** medium/unknown — inventory provenance unverified

## `Inventory_Warehouse_ID`

- **Data type:** `object`
- **Business meaning:** Augmented warehouse identifier (provenance unverified)
- **Missing %:** 0.0
- **Unique count:** 43
- **Example values:** ['SYN-WH-C-TE-D-IVOIRE', 'SYN-WH-VIETNAM', 'SYN-WH-NIGERIA', 'SYN-WH-ZAMBIA', 'SYN-WH-TANZANIA']
- **Identifier:** False
- **ML suitability:** Caution — unverified augmented inventory field
- **Availability time:** Unknown / Needs confirmation
- **Leakage risk:** medium/unknown — inventory provenance unverified

## `Inventory_Date`

- **Data type:** `object`
- **Business meaning:** Augmented inventory snapshot date (provenance unverified)
- **Missing %:** 0.0
- **Unique count:** 2093
- **Example values:** ['02/06/2006', '14/11/2006', '27/08/2006', '01/09/2006', '11/08/2006']
- **Identifier:** False
- **ML suitability:** Caution — unverified augmented inventory field
- **Availability time:** Unknown / Needs confirmation
- **Leakage risk:** medium/unknown — inventory provenance unverified

## `Inventory_Opening_Stock`

- **Data type:** `int64`
- **Business meaning:** Augmented opening stock (provenance unverified)
- **Missing %:** 0.0
- **Unique count:** 5851
- **Example values:** ['57', '3000', '6756', '73800', '71625']
- **Identifier:** False
- **ML suitability:** Caution — unverified augmented inventory field
- **Availability time:** Unknown / Needs confirmation
- **Leakage risk:** medium/unknown — inventory provenance unverified

## `Inventory_Stock_In`

- **Data type:** `int64`
- **Business meaning:** Augmented stock-in quantity (provenance unverified)
- **Missing %:** 0.0
- **Unique count:** 1
- **Example values:** ['0']
- **Identifier:** False
- **ML suitability:** No — constant / non-informative
- **Availability time:** Unknown / Needs confirmation
- **Leakage risk:** medium/unknown — inventory provenance unverified

## `Inventory_Stock_Out`

- **Data type:** `int64`
- **Business meaning:** Augmented stock-out quantity (provenance unverified)
- **Missing %:** 0.0
- **Unique count:** 5065
- **Example values:** ['19', '1000', '500', '31920', '38000']
- **Identifier:** False
- **ML suitability:** Caution — unverified augmented inventory field
- **Availability time:** Unknown / Needs confirmation
- **Leakage risk:** medium — may be unavailable at prediction time; confirm timing

## `Inventory_Closing_Stock`

- **Data type:** `int64`
- **Business meaning:** Augmented closing stock (provenance unverified)
- **Missing %:** 0.0
- **Unique count:** 5195
- **Example values:** ['38', '2000', '6256', '41880', '33625']
- **Identifier:** False
- **ML suitability:** Caution — unverified augmented inventory field
- **Availability time:** Unknown / Needs confirmation
- **Leakage risk:** high — often known only after delivery / outcome

## `Inventory_Reorder_Level`

- **Data type:** `int64`
- **Business meaning:** Augmented reorder threshold (provenance unverified)
- **Missing %:** 0.0
- **Unique count:** 760
- **Example values:** ['29', '1500', '3378', '22730', '23358']
- **Identifier:** False
- **ML suitability:** Caution — unverified augmented inventory field
- **Availability time:** Unknown / Needs confirmation
- **Leakage risk:** medium/unknown — inventory provenance unverified

## `Inventory_Lead_Time_Days`

- **Data type:** `int64`
- **Business meaning:** Augmented lead time in days (provenance unverified)
- **Missing %:** 0.0
- **Unique count:** 1
- **Example values:** ['30']
- **Identifier:** False
- **ML suitability:** No — constant / non-informative
- **Availability time:** Unknown / Needs confirmation
- **Leakage risk:** medium/unknown — inventory provenance unverified

## `Inventory_Stockout_Flag`

- **Data type:** `int64`
- **Business meaning:** Augmented stockout indicator (provenance unverified)
- **Missing %:** 0.0
- **Unique count:** 2
- **Example values:** ['0', '1']
- **Identifier:** False
- **ML suitability:** Caution — unverified augmented inventory field
- **Availability time:** Unknown / Needs confirmation
- **Leakage risk:** high — often known only after delivery / outcome

## `Inventory_Shortage_Quantity`

- **Data type:** `int64`
- **Business meaning:** Augmented shortage quantity (provenance unverified)
- **Missing %:** 0.0
- **Unique count:** 2456
- **Example values:** ['0', '3372', '1123', '2', '4068']
- **Identifier:** False
- **ML suitability:** Caution — unverified augmented inventory field
- **Availability time:** Unknown / Needs confirmation
- **Leakage risk:** high — often known only after delivery / outcome

## `Inventory_Replenishment_Triggered`

- **Data type:** `int64`
- **Business meaning:** Augmented replenishment trigger flag (provenance unverified)
- **Missing %:** 0.0
- **Unique count:** 2
- **Example values:** ['0', '1']
- **Identifier:** False
- **ML suitability:** Caution — unverified augmented inventory field
- **Availability time:** Unknown / Needs confirmation
- **Leakage risk:** high — often known only after delivery / outcome
