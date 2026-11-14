---
name: historical-calibrator
description: |
  Ingest multi-year Meta (Facebook/Instagram JSON/ZIP & Business Suite CSV),
  LinkedIn (Creator Analytics XLSX/CSV & Archive Shares.csv), and Metricool CSV exports
  to deduplicate overlapping records, detect 2021-2024 vs 2025-2026 algorithm regime shifts,
  and calibrate Empirical Bayes format, hook, and publish-hour multipliers.
---

# Historical Social Export Calibrator

Bridges `head-of-content` directly with the Social Intelligence Engine (`~/.gemini/skills/social-data-calibrator/scripts/engine/cli.py` or `SOCIAL_ENGINE_ROOT`) to calibrate platform scoring weights from your actual multi-year historical data.

## Supported Historical Exports
1. **Meta Account Information ZIP/JSON** (auto-repairs UTF-8/Latin-1 Mojibake & joins `past_instagram_insights`) + **Meta Business Suite CSV**.
2. **LinkedIn Creator Analytics `.xlsx` / `.csv`** (skips metadata preamble rows automatically) + **LinkedIn Data Archive `Shares.csv`**.
3. **Metricool Multi-Network CSV** (comma & semicolon dialects across IG, FB, LinkedIn, TikTok, X, YouTube).

## Workflow

```bash
python3 .claude/skills/historical-calibrator/scripts/calibrate_exports.py \
  --export-dir ~/Downloads/social_exports \
  --output content-plans/calibrated_intelligence_report.json
```
