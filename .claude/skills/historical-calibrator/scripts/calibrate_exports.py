#!/usr/bin/env python3
"""Run canonical calibration against isolated copies of explicitly selected exports."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", required=True)
    parser.add_argument("--run-dir", required=True, help="New isolated output directory; existing directories are rejected")
    parser.add_argument("--canonical-root", default=os.environ.get("COASTLINE_AGENT_OS_ROOT"))
    args = parser.parse_args()
    if not args.canonical_root:
        parser.error("Set --canonical-root or COASTLINE_AGENT_OS_ROOT")
    repo = Path(args.canonical_root).expanduser().resolve()
    cli = repo / "skills" / "social-data-calibrator" / "cli.py"
    if not cli.is_file():
        parser.error("Canonical calibrator CLI not found")
    source = Path(args.export_dir).expanduser().resolve()
    run = Path(args.run_dir).expanduser().resolve()
    if not source.is_dir():
        parser.error("Export directory not found")
    if run.exists() or run == source or source in run.parents:
        parser.error("Run directory must be new and outside the input export directory")
    files = sorted(p for p in source.rglob('*') if p.is_file() and p.suffix.lower() in {'.csv', '.xls', '.xlsx'})
    if not files:
        parser.error("No supported CSV/XLS/XLSX exports found; raw JSON/ZIP needs canonical harvesting first")
    if len({p.name for p in files}) != len(files):
        parser.error("Export basenames must be unique for canonical flat ingestion; select noncolliding exports")
    run.mkdir(parents=True)
    inputs = run / "inputs"
    inputs.mkdir()
    receipt = {"status": "pending", "created_at": datetime.now(timezone.utc).isoformat(),
               "engine_cli": str(cli), "engine_sha256": hashlib.sha256(cli.read_bytes()).hexdigest(),
               "source_kind": "user_selected_unverified_exports", "inputs": [],
               "limitations": ["Input hashes do not establish authentic platform provenance or complete metric coverage.",
                                "Inspect canonical report missing-data handling before using it for personalized predictions."]}
    for i, path in enumerate(files):
        relative = path.relative_to(source)
        target = inputs / path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        receipt["inputs"].append({"relative_path": relative.as_posix(), "staged_name": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    receipt_path = run / "provenance.json"
    receipt_path.write_text(json.dumps(receipt, indent=2))
    db = run / "calibration.sqlite"
    commands = [
        [sys.executable, str(cli), "ingest", "--auto-dir", str(inputs), "--db", str(db)],
        [sys.executable, str(cli), "analyze", "--auto-dir", str(run), "--db", str(db), "--repo-root", str(repo)],
    ]
    for step, command in enumerate(commands):
        result = subprocess.run(command, check=False)
        if result.returncode:
            receipt["status"] = "failed"
            receipt["exit_code"] = result.returncode
            receipt_path.write_text(json.dumps(receipt, indent=2))
            return result.returncode
        if step == 0:
            try:
                manifest = json.loads((inputs / "ingest_manifest.json").read_text())
                ingested = [item["file"] for item in manifest["files"]]
                if sorted(ingested) != sorted(path.name for path in files):
                    raise ValueError("Ingest manifest does not cover every selected input exactly once")
            except (OSError, ValueError, TypeError, KeyError) as error:
                receipt["status"] = "ingest_coverage_unverified"
                receipt["error"] = str(error)
                receipt_path.write_text(json.dumps(receipt, indent=2))
                print(str(error), file=sys.stderr)
                return 1
    receipt["status"] = "analysis_completed_provenance_review_required"
    receipt_path.write_text(json.dumps(receipt, indent=2))
    print(str(run / "calibration_report_2026.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
