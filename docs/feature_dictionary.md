# Feature Dictionary — Proposed Features (Phase 01)

These are proposed features for later phases. No features were engineered into a training matrix in Phase 01.

## `is_late`

- **Source columns:** Scheduled Delivery Date, Delivered to Client Date
- **Transformation:** 1 if delivered > scheduled else 0; NA if either date invalid
- **Business meaning:** Late delivery classification target
- **Prediction-time availability:** Target only — not a feature
- **Missing-value handling:** Exclude rows without valid date pair
- **Leakage status:** Target
- **Approved model tasks:** classification (Phase 03)

## `delay_days`

- **Source columns:** Scheduled Delivery Date, Delivered to Client Date
- **Transformation:** delivered_date - scheduled_date in days
- **Business meaning:** Schedule deviation in days
- **Prediction-time availability:** Target / evaluation only
- **Missing-value handling:** NA when dates invalid
- **Leakage status:** Target / proxy
- **Approved model tasks:** regression evaluation, EDA

## `country`

- **Source columns:** Country
- **Transformation:** Categorical encode / target encode with CV
- **Business meaning:** Destination country
- **Prediction-time availability:** Likely available at order time
- **Missing-value handling:** None observed in raw — monitor
- **Leakage status:** OK pending confirmation
- **Approved model tasks:** classification, regression, clustering

## `shipment_mode`

- **Source columns:** Shipment Mode
- **Transformation:** Categorical encode; impute missing as Unknown
- **Business meaning:** Transport mode
- **Prediction-time availability:** Likely available at planning time
- **Missing-value handling:** Fill with 'Unknown' (~3.5% missing)
- **Leakage status:** OK pending confirmation
- **Approved model tasks:** classification, regression

## `vendor`

- **Source columns:** Vendor
- **Transformation:** Categorical / frequency / target encode with CV
- **Business meaning:** Supplier identity
- **Prediction-time availability:** Available at PO time
- **Missing-value handling:** None observed
- **Leakage status:** OK — avoid using post-delivery vendor metrics as raw features without time awareness
- **Approved model tasks:** classification, regression, clustering, anomaly

## `product_group`

- **Source columns:** Product Group
- **Transformation:** Categorical encode
- **Business meaning:** Product family
- **Prediction-time availability:** Available at order time
- **Missing-value handling:** None observed
- **Leakage status:** OK
- **Approved model tasks:** classification, regression, clustering

## `line_item_quantity`

- **Source columns:** Line Item Quantity
- **Transformation:** Numeric; optional log1p for skew
- **Business meaning:** Ordered quantity
- **Prediction-time availability:** Available at order time
- **Missing-value handling:** None observed
- **Leakage status:** OK
- **Approved model tasks:** classification, regression, forecasting

## `line_item_value`

- **Source columns:** Line Item Value
- **Transformation:** Numeric; optional log1p
- **Business meaning:** Shipment line monetary value
- **Prediction-time availability:** Likely available at order time
- **Missing-value handling:** None observed
- **Leakage status:** OK pending confirmation
- **Approved model tasks:** classification, regression, anomaly

## `weight_kg_numeric`

- **Source columns:** Weight (Kilograms)
- **Transformation:** Coerce to float; non-numeric text -> NA + indicator
- **Business meaning:** Shipment weight
- **Prediction-time availability:** Uncertain — sometimes recorded later / cross-referenced
- **Missing-value handling:** NA + missing indicator for non-numeric texts
- **Leakage status:** Medium — confirm timing
- **Approved model tasks:** classification, regression — after availability check

## `freight_cost_usd_numeric`

- **Source columns:** Freight Cost (USD)
- **Transformation:** Coerce to float; non-numeric -> NA + indicator
- **Business meaning:** Freight cost
- **Prediction-time availability:** Often post-hoc / invoiced separately
- **Missing-value handling:** NA + missing indicator
- **Leakage status:** Medium/high — confirm timing before modelling
- **Approved model tasks:** EDA; modelling only after availability proof

## `scheduled_month`

- **Source columns:** Scheduled Delivery Date
- **Transformation:** Extract month/quarter from parsed scheduled date
- **Business meaning:** Seasonality of planned delivery
- **Prediction-time availability:** Available when schedule is known
- **Missing-value handling:** Exclude if schedule unparseable
- **Leakage status:** OK
- **Approved model tasks:** classification, regression, forecasting

## `inventory_opening_stock`

- **Source columns:** Inventory_Opening_Stock
- **Transformation:** Numeric as-is
- **Business meaning:** Opening stock (unverified provenance)
- **Prediction-time availability:** Unknown — do not assume authentic
- **Missing-value handling:** None observed
- **Leakage status:** Unknown / caution
- **Approved model tasks:** inventory experiment (Phase 07) only after provenance review

## `inventory_shortage_quantity`

- **Source columns:** Inventory_Shortage_Quantity
- **Transformation:** Numeric target/proxy
- **Business meaning:** Shortage quantity (unverified)
- **Prediction-time availability:** Outcome-like
- **Missing-value handling:** None observed
- **Leakage status:** Target / high leakage if used as feature
- **Approved model tasks:** possible inventory target — not a feature


# Phase 02 Processing Notes

- Prediction moment: After shipment attributes and scheduled delivery date are known, before actual delivery outcome is observed.
- Early-warning features: Country, Managed_By, Fulfill_Via, Vendor_INCO_Term, Shipment_Mode, Product_Group, Sub_Classification, Vendor, Manufacturing_Site, Brand, Dosage_Form, First_Line_Designation, Line_Item_Quantity, Line_Item_Value, Pack_Price, Unit_Price, Unit_Of_Measure_Per_Pack, Weight_Kilograms_Numeric, Freight_Cost_USD_Numeric, Line_Item_Insurance_USD, Scheduled_Month, Scheduled_Quarter, Scheduled_DOW, Weight_NonNumeric_Flag, Freight_NonNumeric_Flag
- Forbidden leakage fields: Delivered_To_Client_Date, Delivery_Recorded_Date, Inventory_Closing_Stock, Inventory_Replenishment_Triggered, Inventory_Shortage_Quantity, Inventory_Stockout_Flag, delay_days, delivery_duration_days, is_late
- Split: {'method': 'chronological_on_Scheduled_Delivery_Date_Parsed', 'counts': {'train': 7226, 'test': 1550, 'val': 1548}, 'train_end': '2013-08-06 00:00:00'}
- Inventory recommendation: A limited experimental classifier may use opening stock / reorder / shipment context only. Do not claim operational authenticity. Constant Stock_In and Lead_Time reduce feature richness. Prefer documenting limitations over over-claiming predictive power.
