 SAP Dashboard Evidence

 SAP Analytics Cloud dashboard

[View the Financial Risk and Anomaly Dashboard PDF](Financial_Risk_Anomaly_Dashboard.pdf)

The Story was built in SAP Analytics Cloud using live SAP Datasphere analytic models:

- `AM_FIN_RISK` — Financial Risk Analytics
- `AM_FIN_THRESHOLDS` — Financial Threshold Analytics

Dashboard pages cover transaction monitoring, transaction investigation and threshold comparisons.
Reconciled monitoring totals

For the TEST period using the fixed Q98 policy:

| Metric                    | Value         |
|--------------------------=|---------------|
| Transactions              |    7,082      |
| Transaction value         | £1,494,171.59 |
| Anomaly alerts            |      65       |
| Flagged transaction value | £113,553.06   |

 Interpretation and verification limits

All data is synthetic. Anomaly alerts are investigation signals, not confirmed fraud. Flagged transaction value is not financial loss.

The PDF is a static export. The live Story requires tenant access.

The investigation table's alert-only filter and its displayed warning remain to be verified. The export has not yet undergone a final readability review.

Python evaluation charts are available separately in `outputs/`.
