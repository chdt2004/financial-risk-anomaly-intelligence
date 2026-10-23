# Start here — Windows beginner steps

Do ONLY Phase 1 first. SAP comes after a successful local run.

## Phase 1: download, extract and open
1. Download the ZIP. In Windows File Explorer, open Downloads.
2. Right-click the ZIP → **Extract All…** → **Extract**. Do not run inside the compressed ZIP.
3. Open VS Code → **File → Open Folder…**. Select the folder that directly contains `README.md`, `requirements.txt`, `src` and `data`. There may be an extra outer extraction folder: open the inner project folder if needed.
4. VS Code → **Terminal → New Terminal**. The commands below use **PowerShell**. If your tab says bash, use the dropdown beside the terminal plus button → PowerShell.
5. Paste `python --version`. Python 3.11–3.13 is recommended. If unavailable, try `py --version`; substitute `py` for the first environment-creation command below. If neither exists, install Python from https://www.python.org/downloads/windows/ and reopen VS Code.
6. Paste each line separately. A virtual environment avoids changing other projects. Activation is not required.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src/run_project.py
.\.venv\Scripts\python.exe src/verify_project.py
```

Expected last messages: `SUCCESS: ... transactions; ... checks passed.` and `VERIFIED: ...`. Installation needs internet. The pipeline does not.

7. In VS Code Explorer, open **outputs → RUN_SUMMARY.md**. Right-click → Open Preview (or Ctrl+Shift+V).
8. Open `outputs/precision_recall.png` and `outputs/threshold_tradeoff.png`.
9. Stop and share the success output with your helper before moving to SAP. Do not upload `.venv` or the ZIP to SAP.

## Phase 2: Datasphere
Follow `docs/02_DATASPHERE.md`: import eight named CSVs, create dimensions/views, facts and analytic models. Reconcile totals using `outputs/RUN_SUMMARY.md`.

## Phase 3: SAC
Follow `docs/03_SAC.md` using the same working live connection as Project 1. Save the actual Story and capture evidence.

## Phase 4: GitHub
Follow `docs/04_GITHUB.md`. Update deployment status honestly after tenant checks.

## Common errors
- `requirements.txt not found`: the terminal is in the wrong folder. File → Open Folder again; select the folder containing requirements.txt; create a new terminal.
- `No module named ...`: use the full `.venv` interpreter command shown above for both install and run.
- PowerShell activation blocked: do not activate; the full interpreter path works without changing execution policy.
- Python 3.14 build/install failure: use an installed 3.12/3.13 interpreter, e.g. `py -3.12 -m venv .venv` after removing only a failed new `.venv` from this project.
- Validation failure after editing inputs: inspect the named check; restore the ZIP originals or use `--regenerate` only if you want to discard your raw-data edits.
- Git Bash instead of PowerShell: environment interpreter path is `.venv/Scripts/python.exe`; the guide otherwise assumes PowerShell.
