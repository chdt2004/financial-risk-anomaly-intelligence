# SAC — monitoring and investigation Story

Prerequisites: deployed AM_FIN_RISK and AM_FIN_THRESHOLDS, reconciled as in 02_DATASPHERE.md. These instructions describe a manual build, not a prebuilt Story file. Use your existing working Datasphere live connection from Project 1. Live connection means querying deployed data; it does NOT mean streaming fraud detection.

## Connect and save
1. Open SAC → **Stories → Create → Story**; use **Optimized Design Experience** if offered.
2. **Add Data → Data from an existing connection** → your Datasphere live connection → your space → **AM_FIN_RISK**.
3. Save as **Financial Risk and Anomaly Intelligence**.
4. If model not visible, check deployment, space access and fact/analytic-model setup; a bare SQL view will not substitute for an analytic model.
5. Use a white background, navy title, teal baseline and orange/red alerts. Subtitle every page: **Synthetic educational data | GBP | UTC | Alerts require review**.

## Page 1 — Risk Monitoring
1. Rename first page **Risk Monitoring**.
2. Add page filter **SPLIT = TEST**. This is the default evidence period, May–29 June 2025.
3. Insert → Numeric Point (or chart type Numeric Point): **TX_COUNT** = transaction count. Repeat for **AMOUNT_GBP**, **ALERT_FLAG** and **ALERT_AMOUNT_GBP**. Rename displayed titles accordingly. Last KPI is **Flagged payment value**, never fraud loss.
4. Calculation builder → Calculated Measure → Alert Rate = aggregated ALERT_FLAG / aggregated TX_COUNT; return NULL if denominator zero. Percentage format, one decimal. Do not average transaction ratios.
5. Add line chart: TX_DATE dimension, ALERT_FLAG measure. Title **Daily anomaly alerts — Q98 policy**.
6. Add bar chart: MERCHANT_CATEGORY dimension, ALERT_FLAG measure. Add TX_COUNT to an adjacent table to show category volume context.
7. Add column chart: SCORE_BIN dimension, TX_COUNT measure. Sort by SCORE_BIN ascending. This is the score histogram; do not SUM the score itself.
8. Insert → Input Control: TX_DATE; then MERCHANT_CATEGORY; then RISK_BAND. Scope to this page's AM_FIN_RISK widgets.
9. With RISK_BAND = High anomaly, transaction count equals alert count. Clear risk-band filters to restore the whole-population denominator before interpreting alert rate. Date/category/risk filters apply to all KPIs, so titles should indicate filtered context.

## Page 2 — Investigation (flagship)
1. Add a page named **Investigation**; use AM_FIN_RISK.
2. Page filters: SPLIT = TEST and ALERT_FLAG = 1. If the numeric flag cannot be used as a dimension filter in your tenant, use **RISK_BAND = High anomaly** (equivalent for Q98).
3. Insert → Table. Add TRANSACTION_ID first, then TX_TIMESTAMP, ACCOUNT_ID, MERCHANT_ID, MERCHANT_CATEGORY, RISK_BAND, ANOMALY_SCORE, AMOUNT_RATIO, PRIOR_MEAN_GBP, PRIOR_COUNT_1H, GAP_SECONDS, PRIOR_HISTORY_COUNT, REVIEW_HINT and REVIEW_STATUS as row/detail attributes. Add AMOUNT_GBP as measure. Disable unnecessary totals; use flat/tabular layout when available.
4. If too wide, create a compact alert list (ID, timestamp, merchant, amount, score, hint) and a second detail table controlled by TRANSACTION_ID.
5. Add an input control on **TRANSACTION_ID**. Select one ID from data/processed/TRANSACTION_RISK.csv with ALERT_FLAG=1 and SPLIT=TEST. Confirm the displayed amount, score and indicators match exactly. Include ACCOUNT_ID and merchant as context, without identifying real people.
6. Add MERCHANT_CATEGORY and TX_DATE controls. For summary-to-record investigation ON THIS PAGE, add a merchant-category alert bar chart alongside the table. Enable chart **Linked Analysis** (where supported) to the table. Click one bar and confirm every shown record has that category; clear selection and check counts return. If Linked Analysis is unavailable, use the category input control and label it explicitly.
7. Review hints are contextual rules, NOT exact model contributions. Add a text note explaining this beside the table. A flagged record can have no indicator triggered because Isolation Forest also uses feature combinations.
8. REVIEW_STATUS is a fictional pending/current snapshot, not confirmed fraud and not a writeback workflow. Do not call it the status at transaction time.

## Page 3 — Threshold Trade-offs
1. Add AM_FIN_THRESHOLDS as another Story data source. Add page **Threshold Trade-offs**.
2. Set this data source's page filter **SPLIT = TEST**. Add POLICY_ID selector, single-select; default Q98.
3. Numeric points: ALERT_COUNT, TP, FP, FN. Titles must say synthetic cases, e.g. **Missed injected cases (FN)**.
4. Use calculation builder for Precision = TP/(TP+FP), Recall = TP/(TP+FN), Alert Rate = ALERT_COUNT/TRANSACTION_COUNT, all after aggregation; NULL denominator handling. Format percentages. Do not SUM source rates.
5. Add a comparison table with POLICY_ID rows, THRESHOLD as attribute, ALERT_COUNT, TP, FP, FN and calculated precision/recall. Keep the single-policy selector scoped to KPI widgets only so this table can show all four policies. If your release cannot set that scope, use a separate comparison page with no policy selector.
6. Add clustered column chart POLICY_ID versus TP, FP, FN showing all policies. Do not total across policy rows: each repeats the same population.
7. Add text: **Thresholds fixed using April score percentiles; test results are descriptive. Positive labels are injected synthetic scenarios, not confirmed fraud.**
8. Threshold page has no merchant/date granularity. Never link monitoring-page category/date controls to it. These summaries cannot answer category-specific precision.
9. Changing POLICY_ID here changes summary metrics ONLY. The investigation/monitoring model stays Q98. A dynamic threshold-controlled investigation table is not implemented and must not be claimed.

## Evidence checks
- Clear monitoring category/risk controls: TEST alert count matches TEST/Q98 in threshold model and CSV.
- One flagged transaction matches the CSV exactly; category-linked analysis filters records correctly.
- Q90 vs Q99 changes alert volume; TP/FP/FN match CSV, without changing the monitoring model policy.
- Export Story via File/More → Export → PDF (location varies). Save in Evidence/ as `Financial_Risk_Anomaly_Story.pdf`. Capture real tenant analytic-model and live-connection screenshots with credentials/tenant-sensitive details cropped.
- Update README deployment status only after successful reconciliation. No generated local figure is an SAC screenshot.

## Fallback if live connection fails
Use an SAC acquired model from V_RISK_DETAIL exported CSV after reproducing the local join (risk_warehouse.sqlite), or the simpler TRANSACTION_RISK.csv with separate merchant enrichment. Do not improvise table joins in SAC that duplicate transactions. Ask for help before switching. If fallback is used, document acquired import rather than live Datasphere consumption.
