# Verification performed

- Executed full pipeline with installed versions pinned in requirements.txt.
- 44 source, SQL, reconciliation and serialised-score checks passed.
- 12 regression checks passed: injected duplicates, orphan accounts, invalid timestamps, negative amounts and missing categories rejected; future-event invariance; own-history exclusion; exact hour boundary; label exclusion; validation-frozen thresholds; confusion matrix and policy monotonicity; multiple-review join fanout protection.
- All seven Datasphere SELECT bodies were executed as SQLite logical smoke tests. This does not certify HANA types, SAP semantic settings or live-connection permissions.
- Repeated full run and compared all 10 CSV files byte-for-byte; see reproducibility.json.
- Exported ZIP excludes virtual environments, Python caches and local SQLite warehouse. Running Python recreates the warehouse.
- Evaluation plots inspected for readable labels and correct threshold trade-offs.
- SAP tenant deployment and SAC widget/filter behaviour remain to be checked manually using the included instructions. The Windows commands are provided for the user's environment; local execution was on Linux, not a Windows test machine.
