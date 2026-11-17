#!/usr/bin/env python3
"""
Identify LinkedIn outliers using the user-supplied policy (legacy 360Brew label).
Supports Apify/JSON post arrays, LinkedIn Creator Analytics .csv, and multi-sheet .xlsx exports.
"""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))
from avs import score_post, identify_policy_outliers
import re
import statistics


def load_linkedin_records(input_path: str) -> list[dict]:
    path = Path(input_path)
    suf = path.suffix.lower()
    if suf == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else data.get("posts", data.get("items", []))

    if suf == ".csv":
        rows = []
        with path.open("r", encoding="utf-8-sig", errors="ignore") as f:
            lines = f.readlines()
        header_idx = 0
        for idx, line in enumerate(lines[:15]):
            low = line.lower()
            if "impressions" in low or "sharecommentary" in low or "post link" in low:
                header_idx = idx
                break
        reader = csv.DictReader(lines[header_idx:])
        for r in reader:
            rows.append(dict(r))
        return rows

    if suf == ".xlsx":
        import openpyxl
        wb = openpyxl.load_workbook(path, data_only=True)
        target_ws = wb.worksheets[0]
        for ws in wb.worksheets:
            if "post" in ws.title.lower() or "content" in ws.title.lower():
                target_ws = ws
                break
        all_rows = list(target_ws.iter_rows(values_only=True))
        header_idx = 0
        for idx, r in enumerate(all_rows[:15]):
            joined = " ".join(str(c or "").lower() for c in r)
            if "impressions" in joined or "sharecommentary" in joined or ("likes" in joined and "comments" in joined):
                header_idx = idx
                break
        headers = [str(h or f"col_{i}").strip() for i, h in enumerate(all_rows[header_idx])]
        records = []
        for r in all_rows[header_idx + 1:]:
            if not any(r):
                continue
            records.append({headers[i]: r[i] for i in range(min(len(headers), len(r)))})
        return records

    raise ValueError(f"Unsupported LinkedIn file format: {suf}")


def _text(post: dict) -> str:
    for k in ("text", "commentary", "Post Title", "Post title", "ShareCommentary", "caption", "content"):
        if post.get(k):
            return str(post[k])
    return ""


def calculate_360brew_score(post: dict):
    """Full internal policy score, or None when weighted evidence is missing."""
    return score_post(post, "linkedin")["score"]


def calculate_360brew_rate(post: dict):
    """Legacy interface: no composite AVS can be represented as an engagement rate."""
    return None


def identify_outliers(posts: list[dict], threshold_multiplier: float = 2.0) -> list[dict]:
    return identify_policy_outliers(posts, "linkedin", threshold_multiplier)


def extract_topics(posts: list[dict]) -> dict:
    hashtags = Counter()
    keywords = Counter()
    stop = {"the", "and", "for", "that", "this", "with", "from", "your", "have", "more", "what", "when", "into", "they", "their", "over", "most"}
    for p in posts:
        txt = _text(p)
        hashtags.update(re.findall(r"#(\w+)", txt.lower()))
        clean = re.sub(r"https?://\S+|[@#]\w+", "", txt.lower())
        keywords.update(w for w in re.findall(r"\b[a-z]{4,}\b", clean) if w not in stop)
    return {"hashtags": hashtags.most_common(20), "keywords": keywords.most_common(30)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Identify LinkedIn policy-evidence outliers")
    parser.add_argument("--input", "-i", required=True, help="Input .json, .csv, or .xlsx file")
    parser.add_argument("--output", "-o", required=True, help="Output outliers.json path")
    parser.add_argument("--threshold", "-t", type=float, default=1.8, help="Std-dev multiplier (default: 1.8)")
    args = parser.parse_args()

    posts = load_linkedin_records(args.input)
    outliers = identify_outliers(posts, args.threshold)
    topics = extract_topics(posts)

    out = {
        "generated": datetime.now().isoformat(),
        "matrix": "2026.11-v2.1",
        "total_posts": len(posts),
        "outlier_count": len(outliers),
        "evidence": [p.get("_avs") for p in posts],
        "threshold": args.threshold,
        "topics": topics,
        "outliers": outliers,
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"Analyzed {len(posts)} LinkedIn posts -> {len(outliers)} policy-evidence outliers saved to {args.output}")


if __name__ == "__main__":
    main()
