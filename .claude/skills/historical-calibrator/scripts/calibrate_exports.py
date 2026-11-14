#!/usr/bin/env python3
"""
Bridge script for head-of-content to ingest multi-year Meta, LinkedIn, and Metricool exports
and compute Empirical Bayes calibrated platform weights + regime-shift diagnostics.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys


def resolve_engine_cli() -> Path:
    candidates = [
        Path(os.environ.get("SOCIAL_ENGINE_ROOT", "")) / "cli.py" if os.environ.get("SOCIAL_ENGINE_ROOT") else None,
        Path.home() / ".gemini" / "skills" / "social-data-calibrator" / "scripts" / "engine" / "cli.py",
        Path.home() / "social-intelligence-engine" / "cli.py",
        Path("/home/antigravity/social-intelligence-engine/cli.py"),
    ]
    for c in candidates:
        if c and c.exists():
            return c
    raise FileNotFoundError(
        "Social Intelligence Engine CLI not found. Set SOCIAL_ENGINE_ROOT or install ~/.gemini/skills/social-data-calibrator."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest & calibrate multi-year Meta, LinkedIn & Metricool exports")
    parser.add_argument("--export-dir", "-d", required=True, help="Folder containing Meta/LinkedIn/Metricool exports")
    parser.add_argument("--output", "-o", default="calibrated_intelligence_report.json", help="Output report JSON")
    parser.add_argument("--db", default="", help="Optional custom SQLite path")
    args = parser.parse_args()

    cli_path = resolve_engine_cli()
    ingest_cmd = [sys.executable, str(cli_path), "ingest", "--auto-dir", str(Path(args.export_dir).expanduser())]
    if args.db:
        ingest_cmd.extend(["--db", args.db])
    subprocess.run(ingest_cmd, check=True)

    analyze_cmd = [sys.executable, str(cli_path), "analyze", "--out", str(Path(args.output).resolve())]
    if args.db:
        analyze_cmd.extend(["--db", args.db])
    subprocess.run(analyze_cmd, check=True)


if __name__ == "__main__":
    main()
