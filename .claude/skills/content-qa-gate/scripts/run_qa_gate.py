#!/usr/bin/env python3
"""
Pre-Publish EOS Content Team QA Gate & Content-to-Clients Atomizer CLI wrapper for head-of-content.
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
    raise FileNotFoundError("Social Intelligence Engine CLI not found.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run EOS Content Team QA Gate or Content-to-Clients Atomizer")
    sub = parser.add_subparsers(dest="mode", required=True)

    p_qa = sub.add_parser("qa", help="Audit draft against 2026 platform matrix, Brand ICP/Anti-ICP, AEO & Editor QA")
    p_qa.add_argument("--text", required=True)
    p_qa.add_argument("--platform", default="instagram")
    p_qa.add_argument("--format", default="reel")
    p_qa.add_argument("--duration", type=float, default=28.0)
    p_qa.add_argument("--slides", type=int, default=7)
    p_qa.add_argument("--vacancy", action="store_true")

    p_at = sub.add_parser("atomize", help="Generate LinkedIn + 7-Slide IG Carousel + Canonical AEO Webpage + Lead Magnet")
    p_at.add_argument("--topic", required=True)
    p_at.add_argument("--story", required=True)
    p_at.add_argument("--lesson", required=True)
    p_at.add_argument("--cta", default="Request Coastline Equity's Asset Stewardship Audit")

    args = parser.parse_args()
    cli_path = resolve_engine_cli()

    if args.mode == "qa":
        cmd = [
            sys.executable, str(cli_path), "qa-gate",
            "--text", args.text,
            "--platform", args.platform,
            "--format", args.format,
            "--duration", str(args.duration),
            "--slides", str(args.slides),
        ]
        if args.vacancy:
            cmd.append("--vacancy")
        subprocess.run(cmd, check=True)
    else:
        cmd = [
            sys.executable, str(cli_path), "atomize",
            "--topic", args.topic,
            "--story", args.story,
            "--lesson", args.lesson,
            "--cta", args.cta,
        ]
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
