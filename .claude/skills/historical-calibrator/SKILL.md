---
name: historical-calibrator
description: Run the canonical Coastline social-data-calibrator on explicitly selected CSV/XLS/XLSX exports in an isolated directory. Use for historical benchmarking and backtests with source hashes and honest coverage limitations.
---

# Historical export calibration

Read `.claude/lib/SCORING.md`. Select the reviewed canonical checkout explicitly. Preserve private exports outside Git and create a new run directory outside the source export folder:

```bash
python .claude/skills/historical-calibrator/scripts/calibrate_exports.py \
  --export-dir /path/to/verified-exports \
  --run-dir /path/to/new-calibration-run \
  --canonical-root /path/to/coastline-codex-agent-os
```

The wrapper copies supported input files, records SHA-256 hashes, and calls canonical `ingest` and `analyze` with an isolated database. Existing run directories are rejected. JSON/ZIP archives require the canonical harvesting workflow first. A completed command is not proof of authentic inputs, correct missing-value handling, or causal prediction.

Before applying results, verify platform/account, dates, metric definitions, paid/trial/collaboration status, duplicate coverage, and cohort sizes. Distinguish unavailable metrics from zero. Preserve source limitations even where a legacy importer emits zeros. Never autoload a report solely because its filename looks calibrated. The packaged 235 synthetic posts are test data, not Anthony's platform history. Empirical, synthetic, and editorial-policy evidence remain separate.
