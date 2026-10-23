# Model card and evaluation protocol

## Intended use
An educational batch screening prototype for synthetic GBP purchase payments. Human investigation only. No automatic decline, account restriction, fraud allegation or credit decision. Risk bands describe anomaly levels, not customer risk ratings.

## Data and labels
Seed 42, 200 accounts, 40 merchants, 180 days from 1 January 2025. Transaction types include only card purchase payments, intentionally limiting scope. Accounts and merchants are fabricated IDs, with no PII. Account opening dates precede activity. All payments are positive GBP; reversals, transfers, FX and refunds are outside scope.
Ordinary observations follow account-specific lognormal amounts. Large legitimate purchases create difficult negatives. Injected cases include large night payments and rapid bursts, repeated in train, validation and test. This explicit design makes synthetic metrics optimistic and generator-specific. Uninjected records are labelled 0 by construction, not professionally adjudicated negatives. Every burst payment is labelled 1, including the first one that has no prior burst context, so recall need not reach 100%.
`SCENARIO_LABELS` provides complete synthetic ground truth for this generator. `REVIEWS` is a sparse fictional administrative sample marked DEMO_PENDING, with review dates after transactions; no confirmed outcomes, precision or business conversion is inferred from it.

## Features and leakage controls
Five features: log(1+amount), amount/prior account mean (cap 100), previous-hour count excluding current transaction, log(1+seconds since prior payment) (cap gap at 7 days), payment before 06:00 UTC. Account-history mean uses all STRICTLY PRIOR payments; first event uses a fixed GBP 100 prior, and first gap is 86400 seconds. Dataset has no equal account timestamps; validation rejects ties. Hour window includes events exactly 3600 seconds before. Timestamps are timezone-naive strings contractually interpreted as UTC; not local UK daylight saving time.
No scenario labels, scenario types, review fields, merchant/account IDs or future transactions enter the estimator. Features are computed sequentially across all periods: test may use earlier test transactions for historical context, exactly as online arrival would, but never future events or outcomes. This is not model refitting. Historical-only features do not make this a deployed real-time system.

## Fit, score and thresholds
Train: Jan–Mar. Validation: April. Test: May–29 June. Isolation Forest: 200 trees, max_samples=256, random_state=42, n_jobs=1, contamination=auto. No supervised classifier because no reliable real fraud labels exist. No scaling is fitted. Native score_samples is negated so higher = more anomalous; it is not a probability or calibrated 0–100 risk score. Scores may change with library versions.
Capacity policy fixed in advance: Q98 (98th percentile of April scores), inclusive `score >= threshold`. Q95 divides baseline/elevated bands. Four April thresholds Q90/Q95/Q98/Q99 are frozen and applied to validation/test. Q98 targets roughly 2% alerts on validation; ties and distribution shift change actual volume. Jan–Mar scores are in-sample; show TEST by default for performance/monitoring evidence. Test results are reported, not used to select the policy. Operational alerting would need refreshed validation and a governance process.

## Evaluation
TP/FP/FN/TN, precision, recall, alert rate, alert payment value and test average precision plus PR curve. Here positive = an injected synthetic scenario. Synthetic FP means flagged but not injected. These are not real false allegations or fraud outcomes. A policy with no alerts has undefined precision (NULL). AP is average precision, not trapezoidal PR-AUC. Full confusion matrix denominators are retained for aggregation. Do not sum precision, recall, score, ratios or thresholds.

## Investigation indicators
Amount >=5 times prior mean; 3+ prior payments in previous hour; gap <60 seconds; payment before 06:00 UTC. These are transparent contextual rules, NOT exact feature contributions, SHAP values or causal explanations of Isolation Forest. The model can flag combinations with none of these indicators. No unsupported exact attribution is claimed.

## Limitations and next steps
No real bank data, concept-drift validation, unseen-account generalisation claim, investigation workflow/writeback, calibrated probabilities, production monitoring, fairness audit or confirmed monetary loss. Merchant category and region are dashboard dimensions, not model signals. Fresh accounts lack history; analyst context is essential. Review data is a current snapshot and must not be interpreted as status at transaction time. Future work should use lawfully obtained representative outcomes, account/time generalisation tests, rolling validation, drift checks and human review feedback. Do not describe this project as regulatory compliance or proven fraud prevention.
