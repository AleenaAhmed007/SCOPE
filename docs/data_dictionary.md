# Data Dictionary — SCMS_with_inventory.csv

Generated during Phase 01 EDA. Meanings marked Unknown/Needs confirmation are intentional.

Inventory_* fields are treated as **unverified augmented data**.

## `ID`

- **Data type:** `int64`
- **Business meaning:** Unique shipment/line-item identifier
- **Missing %:** 0.0
- **Unique count:** 96470
- **Example values:** ['1', '2', '3', '4', '5']
- **Identifier:** True
- **ML suitability:** No — identifier
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Project Code`

- **Data type:** `object`
- **Business meaning:** Supply-chain project identifier
- **Missing %:** 0.0
- **Unique count:** 27
- **Example values:** ['SP', 'BA', 'GO', 'RN', 'PR']
- **Identifier:** True
- **ML suitability:** No — identifier
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `PQ #`

- **Data type:** `object`
- **Business meaning:** Price quote number
- **Missing %:** 0.0
- **Unique count:** 1
- **Example values:** ['Olist-N/A']
- **Identifier:** True
- **ML suitability:** No — identifier
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `PO / SO #`

- **Data type:** `object`
- **Business meaning:** Purchase order / sales order number
- **Missing %:** 0.0
- **Unique count:** 96470
- **Example values:** ['e481f51cbdc54678b7cc49136f2d6af7', '53cdb2fc8bc7dce0b6741e2150273451', '47770eb9100c2d0c44946d9cf07ec65d', '949d5b44dbf5de918fe9c16f97b45f8a', 'ad21c59c0840e6cb83a9ceb5573f8159']
- **Identifier:** True
- **ML suitability:** No — identifier
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `ASN/DN #`

- **Data type:** `object`
- **Business meaning:** Advanced shipping notice / delivery note number
- **Missing %:** 0.0
- **Unique count:** 96470
- **Example values:** ['e481f51cbdc54678b7cc49136f2d6af7', '53cdb2fc8bc7dce0b6741e2150273451', '47770eb9100c2d0c44946d9cf07ec65d', '949d5b44dbf5de918fe9c16f97b45f8a', 'ad21c59c0840e6cb83a9ceb5573f8159']
- **Identifier:** True
- **ML suitability:** No — identifier
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** medium — may be unavailable at prediction time; confirm timing

## `Country`

- **Data type:** `object`
- **Business meaning:** Destination country
- **Missing %:** 0.0
- **Unique count:** 27
- **Example values:** ['SP', 'BA', 'GO', 'RN', 'PR']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Managed By`

- **Data type:** `object`
- **Business meaning:** Managing organization / office
- **Missing %:** 0.0
- **Unique count:** 2
- **Example values:** ['SameState', 'CrossState']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Fulfill Via`

- **Data type:** `object`
- **Business meaning:** Fulfillment channel (e.g. Direct Drop, RDC)
- **Missing %:** 0.0
- **Unique count:** 2
- **Example values:** ['SingleSeller', 'MultiSeller']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Vendor INCO Term`

- **Data type:** `object`
- **Business meaning:** Incoterms governing vendor shipment responsibility
- **Missing %:** 0.001
- **Unique count:** 4
- **Example values:** ['voucher', 'boleto', 'credit_card', 'debit_card']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Shipment Mode`

- **Data type:** `object`
- **Business meaning:** Transport mode (Air, Ocean, Truck, etc.)
- **Missing %:** 0.0
- **Unique count:** 5
- **Example values:** ['Local', 'Long', 'VeryLong', 'Medium', 'Short']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `PQ First Sent to Client Date`

- **Data type:** `object`
- **Business meaning:** Date PQ was first sent to client (may contain process placeholders)
- **Missing %:** 0.0
- **Unique count:** 612
- **Example values:** ['2017-10-02', '2018-07-24', '2018-08-08', '2017-11-18', '2018-02-13']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `PO Sent to Vendor Date`

- **Data type:** `object`
- **Business meaning:** Date PO was sent to vendor (may contain RDC / not-captured placeholders)
- **Missing %:** 0.0
- **Unique count:** 609
- **Example values:** ['2017-10-02', '2018-07-26', '2018-08-08', '2017-11-18', '2018-02-13']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Scheduled Delivery Date`

- **Data type:** `object`
- **Business meaning:** Planned delivery date to client
- **Missing %:** 0.0
- **Unique count:** 445
- **Example values:** ['2017-10-18', '2018-08-13', '2018-09-04', '2017-12-15', '2018-02-26']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Delivered to Client Date`

- **Data type:** `object`
- **Business meaning:** Actual delivery date to client
- **Missing %:** 0.0
- **Unique count:** 645
- **Example values:** ['2017-10-10', '2018-08-07', '2018-08-17', '2017-12-02', '2018-02-16']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Unknown / Needs confirmation
- **Leakage risk:** high — often known only after delivery / outcome

## `Delivery Recorded Date`

- **Data type:** `object`
- **Business meaning:** Date delivery was recorded in the system
- **Missing %:** 0.0
- **Unique count:** 645
- **Example values:** ['2017-10-10', '2018-08-07', '2018-08-17', '2017-12-02', '2018-02-16']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Unknown / Needs confirmation
- **Leakage risk:** high — often known only after delivery / outcome

## `Product Group`

- **Data type:** `object`
- **Business meaning:** High-level product category
- **Missing %:** 0.0
- **Unique count:** 74
- **Example values:** ['housewares', 'perfumery', 'auto', 'pet_shop', 'stationery']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Sub Classification`

- **Data type:** `object`
- **Business meaning:** Product sub-classification
- **Missing %:** 0.0
- **Unique count:** 22
- **Example values:** ['SP', 'MG', 'ES', 'RS', 'DF']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Vendor`

- **Data type:** `object`
- **Business meaning:** Supplier / vendor name
- **Missing %:** 0.0
- **Unique count:** 22
- **Example values:** ['SP', 'MG', 'ES', 'RS', 'DF']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Item Description`

- **Data type:** `object`
- **Business meaning:** Full product/item description
- **Missing %:** 0.0
- **Unique count:** 74
- **Example values:** ['housewares', 'perfumery', 'auto', 'pet_shop', 'stationery']
- **Identifier:** False
- **ML suitability:** Maybe — text feature / embedding later; high cardinality
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Molecule/Test Type`

- **Data type:** `object`
- **Business meaning:** Active molecule or diagnostic test type
- **Missing %:** 0.0
- **Unique count:** 74
- **Example values:** ['housewares', 'perfumery', 'auto', 'pet_shop', 'stationery']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Brand`

- **Data type:** `object`
- **Business meaning:** Product brand
- **Missing %:** 0.0
- **Unique count:** 22
- **Example values:** ['SP', 'MG', 'ES', 'RS', 'DF']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Dosage`

- **Data type:** `float64`
- **Business meaning:** Dosage strength
- **Missing %:** 100.0
- **Unique count:** 0
- **Example values:** []
- **Identifier:** False
- **ML suitability:** No — constant / non-informative
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Dosage Form`

- **Data type:** `object`
- **Business meaning:** Formulation / dosage form
- **Missing %:** 0.001
- **Unique count:** 4
- **Example values:** ['voucher', 'boleto', 'credit_card', 'debit_card']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Unit of Measure (Per Pack)`

- **Data type:** `float64`
- **Business meaning:** Units contained in one pack
- **Missing %:** 0.0
- **Unique count:** 93880
- **Example values:** ['15.5440625', '19.137766203703706', '26.63971064814815', '26.188819444444444', '12.112048611111112']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Line Item Quantity`

- **Data type:** `int64`
- **Business meaning:** Ordered / shipped quantity for the line item
- **Missing %:** 0.0
- **Unique count:** 17
- **Example values:** ['1', '2', '4', '5', '3']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Line Item Value`

- **Data type:** `float64`
- **Business meaning:** Monetary value of the line item
- **Missing %:** 0.0
- **Unique count:** 7498
- **Example values:** ['29.99', '118.7', '159.9', '45.0', '19.9']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Pack Price`

- **Data type:** `float64`
- **Business meaning:** Price per pack
- **Missing %:** 0.0
- **Unique count:** 6957
- **Example values:** ['29.99', '118.7', '159.9', '45.0', '19.9']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Unit Price`

- **Data type:** `float64`
- **Business meaning:** Price per unit
- **Missing %:** 0.0
- **Unique count:** 6957
- **Example values:** ['29.99', '118.7', '159.9', '45.0', '19.9']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Manufacturing Site`

- **Data type:** `object`
- **Business meaning:** Manufacturing site name
- **Missing %:** 0.0
- **Unique count:** 22
- **Example values:** ['SP', 'MG', 'ES', 'RS', 'DF']
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

- **Data type:** `float64`
- **Business meaning:** Shipment weight; may contain cross-reference text
- **Missing %:** 0.0
- **Unique count:** 2859
- **Example values:** ['0.5', '0.4', '0.42', '0.45', '0.25']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Unknown / Needs confirmation
- **Leakage risk:** medium — may be unavailable at prediction time; confirm timing

## `Freight Cost (USD)`

- **Data type:** `float64`
- **Business meaning:** Freight cost; may contain inclusion / cross-reference text
- **Missing %:** 0.0
- **Unique count:** 7612
- **Example values:** ['8.72', '22.76', '19.22', '27.2', '27.36']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Unknown / Needs confirmation
- **Leakage risk:** medium — may be unavailable at prediction time; confirm timing

## `Line Item Insurance (USD)`

- **Data type:** `float64`
- **Business meaning:** Insurance cost for the line item
- **Missing %:** 0.4945
- **Unique count:** 90272
- **Example values:** ['18.681711262724065', '861.0353666986242', '514.5471404341032', '1821.8026563808453', '29.59309456315452']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** medium — may be unavailable at prediction time; confirm timing

## `Inventory_Product_Key`

- **Data type:** `object`
- **Business meaning:** Augmented inventory product key (provenance unverified)
- **Missing %:** 0.0
- **Unique count:** 74
- **Example values:** ['housewares', 'perfumery', 'auto', 'pet_shop', 'stationery']
- **Identifier:** False
- **ML suitability:** Caution — unverified augmented inventory field
- **Availability time:** Unknown / Needs confirmation
- **Leakage risk:** medium/unknown — inventory provenance unverified

## `Inventory_Warehouse_ID`

- **Data type:** `object`
- **Business meaning:** Augmented warehouse identifier (provenance unverified)
- **Missing %:** 0.0
- **Unique count:** 22
- **Example values:** ['SP', 'MG', 'ES', 'RS', 'DF']
- **Identifier:** False
- **ML suitability:** Caution — unverified augmented inventory field
- **Availability time:** Unknown / Needs confirmation
- **Leakage risk:** medium/unknown — inventory provenance unverified

## `Inventory_Date`

- **Data type:** `object`
- **Business meaning:** Augmented inventory snapshot date (provenance unverified)
- **Missing %:** 0.0
- **Unique count:** 612
- **Example values:** ['2017-10-02', '2018-07-24', '2018-08-08', '2017-11-18', '2018-02-13']
- **Identifier:** False
- **ML suitability:** Caution — unverified augmented inventory field
- **Availability time:** Unknown / Needs confirmation
- **Leakage risk:** medium/unknown — inventory provenance unverified

## `Inventory_Opening_Stock`

- **Data type:** `int64`
- **Business meaning:** Augmented opening stock (provenance unverified)
- **Missing %:** 0.0
- **Unique count:** 31
- **Example values:** ['2', '1', '3', '4', '7']
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
- **Unique count:** 17
- **Example values:** ['1', '2', '4', '5', '3']
- **Identifier:** False
- **ML suitability:** Caution — unverified augmented inventory field
- **Availability time:** Unknown / Needs confirmation
- **Leakage risk:** medium — may be unavailable at prediction time; confirm timing

## `Inventory_Closing_Stock`

- **Data type:** `int64`
- **Business meaning:** Augmented closing stock (provenance unverified)
- **Missing %:** 0.0
- **Unique count:** 21
- **Example values:** ['1', '0', '2', '3', '8']
- **Identifier:** False
- **ML suitability:** Caution — unverified augmented inventory field
- **Availability time:** Unknown / Needs confirmation
- **Leakage risk:** high — often known only after delivery / outcome

## `Inventory_Reorder_Level`

- **Data type:** `int64`
- **Business meaning:** Augmented reorder threshold (provenance unverified)
- **Missing %:** 0.0
- **Unique count:** 16
- **Example values:** ['1', '2', '5', '4', '3']
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
- **Unique count:** 5
- **Example values:** ['0', '1', '2', '3', '4']
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

## `Olist_is_late`

- **Data type:** `int64`
- **Business meaning:** Unknown / Needs confirmation
- **Missing %:** 0.0
- **Unique count:** 2
- **Example values:** ['0', '1']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Olist_distance_km`

- **Data type:** `float64`
- **Business meaning:** Unknown / Needs confirmation
- **Missing %:** 0.4945
- **Unique count:** 90272
- **Example values:** ['18.681711262724065', '861.0353666986242', '514.5471404341032', '1821.8026563808453', '29.59309456315452']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time

## `Olist_estimated_delivery_days`

- **Data type:** `float64`
- **Business meaning:** Unknown / Needs confirmation
- **Missing %:** 0.0
- **Unique count:** 93880
- **Example values:** ['15.5440625', '19.137766203703706', '26.63971064814815', '26.188819444444444', '12.112048611111112']
- **Identifier:** False
- **ML suitability:** Candidate — subject to leakage and availability review
- **Availability time:** Likely available at/before shipment planning — Needs confirmation
- **Leakage risk:** low/unknown — confirm availability at prediction time
