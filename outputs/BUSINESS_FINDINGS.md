# Findings — synthetic demonstration only

The strict default Q98 policy flags 65 of 7,082 held-out test payments, detects 65 injected cases and misses 225. Precision against the generator's synthetic labels is 100%, but recall is only 22.4%. This is not evidence of perfect fraud detection: there are no confirmed real fraud outcomes, and the generator makes some scenarios easy to separate.

Q90 generates substantially more alerts and captures more injected cases, including more uninjected transactions for review. Compare the exact counts in data/processed/THRESHOLD_METRICS.csv. Lower review workload and higher scenario recall compete; an analyst team should consider its capacity and the cost of missed cases. No real review cost or fraud loss is supplied, so an optimal financial policy cannot be claimed.

Night activity, large amounts and short gaps are investigation context, not proof. Legitimate large purchases are deliberately present. The first transaction in a rapid burst may look ordinary because future events are unavailable at scoring time. Thresholds were fixed on April score quantiles; differences in May/June alert rates show that a quantile target does not guarantee the same future workload.

Recommended demonstration: show Q98, compare Q90/Q95 on the threshold page, then inspect a flagged test transaction alongside its strictly prior features. Keep the dashboard's investigation policy explicitly Q98. Present synthetic metrics as evidence of correct evaluation and transparent limitations, not as business effectiveness.
