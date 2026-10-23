# Datasphere — exact import and build sequence

Prerequisites: your working academy space, modelling permission, storage and existing SAC live connection from Project 1. Screens differ by tenant release. All names below are technical names, not just business labels. Reuse your space but avoid overwriting Project 1 objects. These names are separate from its commercial objects. If an existing object has a conflicting name, use a dedicated Project 2 space or ask before renaming SQL references.

## A. Import eight files
1. Open SAP Datasphere → **Data Builder** → choose your academy space.
2. Click **Import → Import CSV File** (some versions show **New → Table → Import CSV File**).
3. Select the listed local file using Browse. UTF-8, comma delimiter, first row contains headers.
4. Set the EXACT technical table name in the table. Review EVERY type before import.
5. Save, import data and **Deploy**. Open **Data Preview** and confirm rows exist. Repeat.

| Order | Local file | Technical table | Key |
|---|---|---|---|
| 1 | data/raw/ACCOUNTS.csv | ACCOUNTS | ACCOUNT_ID |
| 2 | data/raw/MERCHANTS.csv | MERCHANTS | MERCHANT_ID |
| 3 | data/raw/TRANSACTION_TYPES.csv | TRANSACTION_TYPES | TYPE_ID |
| 4 | data/raw/DATES.csv | DATES | TX_DATE |
| 5 | data/raw/REVIEWS.csv | REVIEWS | REVIEW_ID |
| 6 | data/processed/TRANSACTION_RISK.csv | TRANSACTION_RISK | TRANSACTION_ID |
| 7 | data/processed/THRESHOLD_METRICS.csv | THRESHOLD_METRICS | SPLIT, POLICY_ID |
| 8 | data/raw/TRANSACTIONS.csv | TRANSACTIONS | TRANSACTION_ID |

TRANSACTIONS is an audit source, not required by analytical SQL views. Do NOT upload SCENARIO_LABELS: evaluation metrics already carry the explicitly synthetic counts. DAILY_RISK is produced locally but the tenant summary is rebuilt from risk detail. No need to upload both.

### Type checklist
- IDs: NVARCHAR(40); category/type/region/status/split/policy/risk band/score bin: NVARCHAR(80); REVIEW_HINT: NVARCHAR(250).
- OPEN_DATE, TX_DATE: DATE. TX_TIMESTAMP and REVIEW_TIMESTAMP: TIMESTAMP. Inspect timestamp parsing; never allow locale day/month swapping.
- AMOUNT_GBP, ALERT_AMOUNT_GBP, ALERT_VALUE_GBP: DECIMAL(18,2).
- ANOMALY_SCORE, THRESHOLD, PRECISION, RECALL, ALERT_RATE, LOG_AMOUNT, AMOUNT_RATIO, LOG_GAP_SECONDS: DECIMAL(18,10).
- PRIOR_MEAN_GBP, GAP_SECONDS: DECIMAL(18,6).
- All count/indicator fields, YEAR, MONTH_NUMBER, TP/FP/FN/TN: INTEGER.
- Empty precision/recall if any: NULL, not zero or literal text. Currency: NVARCHAR(3).

## B. Create seven SQL views
For each row: **Data Builder → New SQL View → SQL (Standard Query)** → open the matching `.sql` in VS Code → Ctrl+A → Ctrl+C → paste entire contents into SAP editor → Validate → Save with exact technical name → Deploy.
Do not paste SQLite CREATE VIEW scripts, Python or Markdown. SELECT bodies are provided specifically for SAP.

| Order | View/file in datasphere/ | Purpose |
|---|---|---|
| 1 | DIM_ACCOUNT.sql | Account dimension |
| 2 | DIM_MERCHANT.sql | Merchant dimension |
| 3 | DIM_TX_TYPE.sql | Payment type dimension |
| 4 | DIM_TX_DATE.sql | Daily date dimension |
| 5 | V_RISK_DETAIL.sql | One row per transaction with preaggregated reviews |
| 6 | V_DAILY_RISK.sql | Daily/category/band/split summary |
| 7 | V_THRESHOLD_METRICS.sql | Synthetic evaluation policy summary |

If `YEAR` or another name is rejected by your release as reserved, quote that column identifier consistently in the affected SQL and check the table's actual technical column name. SQL logical smoke tests do not certify HANA type/semantic behaviour.

## C. Define dimensions
Open each DIM view → output/semantic properties → **Semantic Usage: Dimension** → mark key → Save/Deploy.
- DIM_ACCOUNT: key ACCOUNT_ID; attributes ACCOUNT_TYPE, OPEN_DATE.
- DIM_MERCHANT: key MERCHANT_ID; attributes MERCHANT_CATEGORY, MERCHANT_REGION.
- DIM_TX_TYPE: key TYPE_ID; attribute TYPE_NAME.
- DIM_TX_DATE: key TX_DATE; attributes YEAR, MONTH_NUMBER. This is an ordinary date dimension, not a configured SAP time hierarchy.

## D. Transaction fact and analytic model
1. Open V_RISK_DETAIL → set **Semantic Usage = Fact**.
2. Define SUM measures: TX_COUNT, AMOUNT_GBP, ALERT_FLAG, ALERT_AMOUNT_GBP.
3. Keep TRANSACTION_ID, timestamp, score, prior counts, prior mean, gap, ratio, indicators, risk band, split, score bin and REVIEW_HINT as **attributes**, not SUM measures. Numeric model features are detail attributes. If a tenant cannot display a numeric attribute in SAC, define a display string in a separate view or ask for tenant-specific help; never sum scores to force visibility.
4. Add many-to-one associations: ACCOUNT_ID → DIM_ACCOUNT.ACCOUNT_ID; MERCHANT_ID → DIM_MERCHANT.MERCHANT_ID; TYPE_ID → DIM_TX_TYPE.TYPE_ID; TX_DATE → DIM_TX_DATE.TX_DATE.
5. Save and Deploy. Select **New → Analytic Model**, choose V_RISK_DETAIL (or use Create Analytic Model from the view).
6. Include the four measures, dimension associations and ALL listed investigation attributes. Save/deploy as **AM_FIN_RISK**.
7. If available, set availability/exposure for consumption. Analytic models are the consumption layer; do not switch to deprecated analytical datasets.

## E. Threshold model
V_THRESHOLD_METRICS → Fact. SUM measures: TRANSACTION_COUNT, ALERT_COUNT, ALERT_VALUE_GBP, TP, FP, FN, TN. Attributes: SPLIT, POLICY_ID, THRESHOLD. Do not expose source PRECISION/RECALL/ALERT_RATE as SUM measures.
Create/deploy **AM_FIN_THRESHOLDS**. Calculate aggregate Precision = SUM(TP)/(SUM(TP)+SUM(FP)), Recall = SUM(TP)/(SUM(TP)+SUM(FN)), Alert Rate = SUM(ALERT_COUNT)/SUM(TRANSACTION_COUNT), with NULL on zero denominator. Use formula builder functions available in your tenant. If needed make these in SAC calculation builder. Always keep one policy/split for KPI totals.
V_DAILY_RISK is a reusable optional fact (SUM its four count/value columns) and optional AM_FIN_DAILY; it is not required for the primary Story.

## F. Reconcile before SAC
Open outputs/RUN_SUMMARY.md. In AM_FIN_RISK preview with NO filters compare SUM(TX_COUNT), SUM(AMOUNT_GBP), SUM(ALERT_FLAG) to that summary. Preview one transaction ID against TRANSACTION_RISK.csv. Exactly one row must appear.
Preview TEST + Q98 in AM_FIN_THRESHOLDS and compare TP/FP/FN/TN to THRESHOLD_METRICS.csv. Alert count must equal TP+FP, transaction count TP+FP+FN+TN.

## Refresh
Run Python → REPLACE data in TRANSACTION_RISK and THRESHOLD_METRICS, never append duplicate keys → refresh Story. Raw sources only change if you regenerate/edit them. This is a fixed historical batch demo, not automated ingestion. No credentials belong in GitHub.

## Official references checked for this package
- https://help.sap.com/docs/SAP_DATASPHERE/c8a54ee704e94e15926551293243fd1d/5c1e3d4a49554fcd8fcf199d664d1109.html
- https://learning.sap.com/courses/exploring-sap-datasphere/working-with-analytic-models
- https://help.sap.com/docs/SAP_ANALYTICS_CLOUD/18850a0e13944f53aa8a8b7c094ea29e/ad4281e2875949f0b4d45d1072ff4c38.html
