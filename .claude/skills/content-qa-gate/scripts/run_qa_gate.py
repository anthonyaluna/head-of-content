#!/usr/bin/env python3
"""Forward explicit draft/evidence JSON to the canonical Coastline QA/atomizer."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


def resolve_engine_cli(root=None):
    configured = root or os.environ.get("COASTLINE_AGENT_OS_ROOT")
    if not configured:
        raise ValueError("Set --canonical-root or COASTLINE_AGENT_OS_ROOT to the reviewed canonical checkout")
    repo = Path(configured).expanduser().resolve()
    cli = repo / "skills" / "social-data-calibrator" / "cli.py"
    if not cli.is_file():
        raise FileNotFoundError("Canonical social-data-calibrator CLI not found")
    return repo, cli


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["qa", "qa-gate", "atomize"])
    parser.add_argument("--input", required=True, help="Draft + explicit evidence JSON; no fabricated default runtime/slides")
    parser.add_argument("--canonical-root")
    args = parser.parse_args()
    repo, cli = resolve_engine_cli(args.canonical_root)
    input_path = Path(args.input).expanduser().resolve()
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        parser.error("Input must be a JSON object")
    mode = "qa-gate" if args.mode == "qa" else args.mode
    return subprocess.run([sys.executable, str(cli), mode, "--input", str(input_path),
                           "--repo-root", str(repo)], check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
