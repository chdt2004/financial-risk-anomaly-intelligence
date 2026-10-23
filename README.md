# Financial Risk, Fraud Signals & Anomaly Analytics Platform

Educational transaction anomaly monitoring with **Python, SQL, SAP Datasphere and SAP Analytics Cloud**. All records are synthetic; amounts are positive GBP card payments. No bank data, personal information or confirmed fraud outcomes.

**Open [START_HERE.md](START_HERE.md) first.** Windows instructions use VS Code and PowerShell. Python 3.11–3.13 recommended; tested runtime and results are recorded in `outputs/model_metadata.json` and `outputs/RUN_SUMMARY.md`.

## Business purpose
Prioritise unusual payments for analyst review, understand alert volume and inspect a transaction's historical features. A score is NOT a fraud probability. Alert value is the sum of flagged payment amounts, NOT financial loss, prevented fraud or savings.

## Architecture
Synthetic CSV sources → Python prior-history features → train-only Isolation Forest → validation capacity thresholds → risk CSV → Datasphere fact and dimensions → analytic models → live SAC monitoring and investigation.
SQLite executes the analytical joins and validations locally. `sql/` is SQLite; `datasphere/` contains separate HANA-compatible SELECT bodies for Standard Query SQL Views.

## What is included
- 200 accounts, 40 merchants; January–June 2025 fixed historical demonstration.
- Seeded ordinary payments, legitimate large purchases and injected unusual scenarios.
- Chronological train/validation/test split; no labels, account IDs or scenario descriptions in model inputs.
- Threshold sensitivity, synthetic-label precision/recall, PR curve and average precision.
- SQL validation and amount/count reconciliation, data dictionary, model card and tests.
- Manual Datasphere and SAC build guides, upload manifest and checkpoint instructions.

## Deployment status
Python and SQLite were run and tested in the package-building environment. Review `outputs/QA.md` for exact checks. **Datasphere and SAC must be built manually in your academy tenants; they have not been deployed or tenant-tested by the package author.** There is no importable SAP transport, prebuilt SAC story, streaming deployment or production fraud engine. `Evidence/` is for your real tenant screenshots/PDF later.

## Run
```powershell
python -m pip install -r requirements.txt
python src/run_project.py
python src/verify_project.py
```
The supplied CSVs already exist. Normal runs preserve and validate them; `python src/run_project.py --regenerate` deliberately recreates all synthetic raw inputs from seed 42. No model binary is needed: the fit is reproducible in source.

## Evidence and interpretation
Open `outputs/RUN_SUMMARY.md`, `outputs/validation.json`, `outputs/model_metadata.json`, `outputs/precision_recall.png`, `outputs/threshold_tradeoff.png` and `data/processed/THRESHOLD_METRICS.csv`. Test threshold rows are a descriptive sensitivity analysis, not permission to tune on the test set. `SCENARIO_LABELS.csv` is evaluation-only; it is not a bank review outcome and is not uploaded to the transaction risk model.

See [MODEL_CARD.md](MODEL_CARD.md), [data dictionary](docs/DATA_DICTIONARY.md), [Datasphere](docs/02_DATASPHERE.md), [SAC](docs/03_SAC.md), and [GitHub](docs/04_GITHUB.md).
