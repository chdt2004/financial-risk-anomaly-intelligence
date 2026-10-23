# GitHub — only after local run and SAP evidence

Keep Project 2 in its own repository. Username: chdt2004. Suggested repository: financial-risk-anomaly-intelligence.

1. Edit README Deployment status with your ACTUAL Datasphere models/Story and live/acquired connection status. Add relative links to the real Evidence PDF/screenshots. Keep synthetic-data/model limitations.
2. GitHub → top right **+ → New repository**. Owner chdt2004. Repository name `financial-risk-anomaly-intelligence`. Public for portfolio if desired. Do not add README, .gitignore or licence during this step because local files already exist. Click Create repository.
3. VS Code → Terminal → dropdown → **Git Bash** (Git already works for you). Terminal must be inside the folder containing README.md. Paste each command:

```bash
git init
git add .
git status
```

Inspect status: `.venv`, SQLite database, credentials and .env must NOT be staged. Only synthetic CSVs, source, documentation, evaluation plots and actual SAP evidence belong here. The supplied .gitignore handles local environment/database files.

```bash
git commit -m "Build financial transaction anomaly analytics portfolio"
git branch -M main
git remote add origin https://github.com/chdt2004/financial-risk-anomaly-intelligence.git
git push -u origin main
```

If `origin already exists`, run `git remote -v` and inspect it; do not overwrite another repository blindly. If remote is not empty, stop and resolve rather than force-push.

4. Open repository and verify README, src/, data/, datasphere/, docs/ and Evidence/ are visible.

## Honest CV description after deployment
Built a synthetic transaction anomaly analytics pipeline with Python Isolation Forest and SQL validation, modelled transaction risk in SAP Datasphere, and created an SAC Story for alert monitoring and record-level investigation. Evaluated threshold trade-offs on a chronological holdout using injected scenario labels.

Do not claim a real fraud detection rate, bank deployment, proven loss prevention, real confirmed outcomes or exact feature attribution.
