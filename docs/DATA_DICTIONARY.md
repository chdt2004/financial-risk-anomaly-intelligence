# Data dictionary and grains

All identifiers are synthetic strings. GBP only. Date strings: YYYY-MM-DD. Timestamp strings: YYYY-MM-DD HH:MM:SS, interpreted as UTC. Raw numeric amounts have two decimals.

| File | Grain / key | Fields and interpretation |
|---|---|---|
| ACCOUNTS | ACCOUNT_ID | ACCOUNT_TYPE Personal/Business; OPEN_DATE |
| MERCHANTS | MERCHANT_ID | MERCHANT_CATEGORY; MERCHANT_REGION fictional UK region |
| TRANSACTION_TYPES | TYPE_ID | TYPE_NAME; one supported type CARD_PAYMENT |
| DATES | TX_DATE | YEAR; MONTH_NUMBER; daily calendar, 180 rows |
| TRANSACTIONS | TRANSACTION_ID | ACCOUNT_ID, MERCHANT_ID, TX_TIMESTAMP, AMOUNT_GBP, TYPE_ID, CURRENCY |
| SCENARIO_LABELS | TRANSACTION_ID | SCENARIO_LABEL 0/1; SCENARIO_TYPE; evaluation ONLY |
| REVIEWS | REVIEW_ID | TRANSACTION_ID; REVIEW_TIMESTAMP; REVIEW_STATUS DEMO_PENDING. Event grain; aggregate before joining transactions. |
| TRANSACTION_RISK | TRANSACTION_ID | Transaction fields plus features and scores below; no labels/review outcomes |
| THRESHOLD_METRICS | SPLIT + POLICY_ID | Validation/test population, fixed threshold and confusion counts per policy |
| DAILY_RISK | TX_DATE + MERCHANT_CATEGORY + RISK_BAND + SPLIT | Additive transaction count/value and alert count/value |

## Transaction risk columns
| Column | Definition | Aggregation |
|---|---|---|
| TX_COUNT | Constant 1 | SUM |
| ALERT_FLAG | 1 if score >= Q98 threshold | SUM = alert count |
| AMOUNT_GBP | Payment amount | SUM |
| ALERT_AMOUNT_GBP | AMOUNT_GBP * ALERT_FLAG | SUM; not loss |
| TX_DATE | Date portion of UTC timestamp | Dimension |
| SPLIT | TRAIN / VALIDATION / TEST | Dimension |
| PRIOR_HISTORY_COUNT | Number of earlier account payments | Detail attribute |
| PRIOR_MEAN_GBP | Earlier account payment mean; fixed 100 on first payment | Detail attribute; do not SUM |
| PRIOR_COUNT_1H | Earlier account events at most 3600s before current event | Detail attribute |
| GAP_SECONDS | Seconds since prior account event; 86400 on first event | Detail attribute |
| LOG_AMOUNT | Natural log(1+amount) | Model input; detail attribute |
| AMOUNT_RATIO | Amount / prior mean; capped at 100 | Model input; detail attribute |
| LOG_GAP_SECONDS | Natural log(1+min(gap,604800)) | Model input; detail attribute |
| NIGHT_FLAG | Hour <6 UTC | Model input; detail attribute |
| ANOMALY_SCORE | Negative native IsolationForest score_samples | Detail attribute; never SUM |
| RISK_BAND | High anomaly >=Q98; Elevated >=Q95 and <Q98; Baseline otherwise | Dimension |
| SCORE_BIN | Fixed score intervals with inclusive lower, exclusive upper bounds | Dimension |
| INDICATOR_AMOUNT | AMOUNT_RATIO >=5 | Detail 0/1 attribute |
| INDICATOR_VELOCITY | PRIOR_COUNT_1H >=3 | Detail 0/1 attribute |
| INDICATOR_SHORT_GAP | GAP_SECONDS <60 | Detail 0/1 attribute |
| INDICATOR_NIGHT | NIGHT_FLAG | Detail 0/1 attribute |
| REVIEW_HINT | Contextual indicator text; not exact model attribution | Dimension/detail attribute |

V_RISK_DETAIL adds ACCOUNT_TYPE, OPEN_DATE, MERCHANT_CATEGORY, MERCHANT_REGION, TYPE_NAME, REVIEW_COUNT and REVIEW_STATUS. Review rows are grouped by transaction to prevent fanout. All supplied statuses are identical; MAX(REVIEW_STATUS) is not a general latest-status algorithm and must be replaced if real heterogeneous review history is introduced.

THRESHOLD_METRICS: TRANSACTION_COUNT, ALERT_COUNT, ALERT_VALUE_GBP, TP/FP/FN/TN are additive only within one policy and split. THRESHOLD, PRECISION, RECALL and ALERT_RATE are not additive. Policies repeat the same population: always select exactly one for KPI totals. No date/category filters apply to this whole-period summary.
