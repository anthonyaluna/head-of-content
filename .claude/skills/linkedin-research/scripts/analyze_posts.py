#!/usr/bin/env python3
"""
Identify outlier LinkedIn posts using the 2026 LinkedIn 360Brew ranking matrix.
Supports Apify/JSON post arrays, LinkedIn Creator Analytics .csv, and multi-sheet .xlsx exports.
"""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime
import json
from pathlib import Path
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


def _num(val) -> float:
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    cleaned = re.sub(r"[^0-9.\-]", "", str(val))
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0


def _text(post: dict) -> str:
    for k in ("text", "commentary", "Post Title", "Post title", "ShareCommentary", "caption", "content"):
        if post.get(k):
            return str(post[k])
    return ""


def calculate_360brew_score(post: dict) -> float:
    """
    2026 LinkedIn 360Brew Weighted Engagement & Dwell Score:
    - Comments (8.0x): Substantive professional discussion is the #1 feed multiplier
    - Reposts / Shares (6.0x): Second-degree network graph expansion
    - Saves / Document Clicks (4.5x): Dwell-time proxy ("See more" & PDF slide swipes)
    - Reactions / Likes (1.0x): Passive approval
    Modifiers:
    - Document / Carousel format: 1.34x dwell boost
    - External URL in body: 0.78x reach suppression flag
    """
    likes = _num(post.get("numLikes") or post.get("likes") or post.get("Likes") or post.get("Reactions"))
    comments = _num(post.get("numComments") or post.get("comments") or post.get("Comments"))
    shares = _num(post.get("numShares") or post.get("reposts") or post.get("Reposts") or post.get("Shares"))
    saves = _num(post.get("Saves") or post.get("saves") or 0)
    clicks = _num(post.get("clicks") or post.get("Clicks") or 0)
    impressions = _num(post.get("impressions") or post.get("Impressions") or post.get("views") or 0)

    txt = _text(post)
    ctype = str(post.get("type") or post.get("Post Type") or post.get("Content Type") or "").lower()
    is_carousel = any(k in ctype for k in ("document", "carousel", "pdf"))

    raw = likes + (8.0 * comments) + (6.0 * shares) + (6.5 * saves) + (2.0 * clicks) + (0.03 * impressions)
    mult = 1.34 if is_carousel else 1.0
    if re.search(r"https?://(?!www\.linkedin\.com|lnkd\.in)\S+", txt):
        mult *= 0.78
    return round(raw * mult, 2)


def calculate_360brew_rate(post: dict) -> float:
    impressions = _num(post.get("impressions") or post.get("Impressions") or post.get("views") or 0)
    followers = _num(post.get("authorFollowers") or post.get("followers") or 0)
    score = calculate_360brew_score(post)
    denom = max(impressions, followers, 200.0)
    return round((score / denom) * 100.0, 3)


def identify_outliers(posts: list[dict], threshold_multiplier: float = 1.5) -> list[dict]:
    if not posts:
        return []
    for p in posts:
        p["_engagement_score"] = calculate_360brew_score(p)
        p["_engagement_rate"] = calculate_360brew_rate(p)
        p["_matrix_version"] = "2026.1-linkedin-360brew"

    rates = [p["_engagement_rate"] for p in posts]
    if len(rates) < 2:
        return posts
    mean_rate = statistics.mean(rates)
    std_dev = statistics.stdev(rates)
    if std_dev == 0:
        return []
    cutoff = mean_rate + (threshold_multiplier * std_dev)
    outliers = [p for p in posts if p["_engagement_rate"] > cutoff]
    outliers.sort(key=lambda x: x["_engagement_score"], reverse=True)
    return outliers


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
    parser = argparse.ArgumentParser(description="Identify LinkedIn 360Brew outliers")
    parser.add_argument("--input", "-i", required=True, help="Input .json, .csv, or .xlsx file")
    parser.add_argument("--output", "-o", required=True, help="Output outliers.json path")
    parser.add_argument("--threshold", "-t", type=float, default=1.8, help="Std-dev multiplier (default: 1.8)")
    args = parser.parse_args()

    posts = load_linkedin_records(args.input)
    outliers = identify_outliers(posts, args.threshold)
    topics = extract_topics(posts)

    out = {
        "generated": datetime.now().isoformat(),
        "matrix": "2026.1-linkedin-360brew",
        "total_posts": len(posts),
        "outlier_count": len(outliers),
        "threshold": args.threshold,
        "topics": topics,
        "outliers": outliers,
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"Analyzed {len(posts)} LinkedIn posts -> {len(outliers)} 360Brew outliers saved to {args.output}")


if __name__ == "__main__":
    main()
