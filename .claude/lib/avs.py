"""Evidence-aware v2.1 research scoring. All weights are internal policy.

Full AVS is withheld when any weighted signal is missing. Observed contribution
is a partial weighted sum, never renormalized to hide coverage gaps. Outliers
compare only identical signal coverage, profile, denominator, and format.
"""
from __future__ import annotations

from collections import defaultdict
import json
import math
from pathlib import Path
import statistics

POLICY = json.loads(Path(__file__).with_name("social_policy_2026.json").read_text())


def number(value):
    """Accept nonnegative finite numbers; retain unknown, including malformed data."""
    if isinstance(value, bool) or value is None:
        return None
    try:
        value = float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) and value >= 0 else None


def first(record, *keys):
    for key in keys:
        value = record
        for part in key.split("."):
            value = value.get(part) if isinstance(value, dict) else None
        if value is not None:
            return number(value)
    return None


def fraction(value):
    value = number(value)
    return value if value is not None and value <= 1 else None


def rate(record, numerator, denominator):
    n = first(record, *numerator)
    d = first(record, *denominator)
    if n is None or d is None or d <= 0:
        return None
    return fraction(n / d)


def score_post(post, platform, surface=None):
    """Read explicit unit-interval signals and conservative count/exposure aliases.

    Dwell, satisfaction, watch time, reply depth and SEO assessments must be
    supplied as `signals` with their normalization/source recorded by the caller.
    Likes are never treated as watch time, total comments as substantive comments,
    or public shares as private sends. Invalid or missing ratios stay null.
    """
    profile = platform
    if platform == "instagram":
        surface = surface or post.get("surface", "unconnected")
        if surface not in {"connected", "unconnected"}:
            raise ValueError("Instagram surface must be connected or unconnected")
        profile = "instagram_" + surface
    if platform == "youtube":
        media_format = post.get("format")
        if media_format not in {"shorts", "longform"}:
            return {"version": POLICY["version"], "profile": None, "score": None,
                    "observed_contribution": None, "coverage": 0,
                    "status": "missing_format", "missing": ["format: shorts or longform"],
                    "signals": {}, "sources": {}, "denominator": "views"}
        profile = "youtube_" + media_format
    if profile not in POLICY["weights"]:
        raise ValueError("Unsupported platform profile: " + profile)
    weights = POLICY["weights"][profile]
    supplied = post.get("signals") if isinstance(post.get("signals"), dict) else {}
    signals = {name: fraction(supplied.get(name)) for name in weights}
    sources = {name: "signals." + name for name, value in signals.items() if value is not None}
    if platform in {"instagram", "facebook"}:
        denominator = ("reach", "Reach", "accountsReached")
    elif platform == "linkedin":
        denominator = ("impressions", "Impressions")
    else:
        denominator = ("views", "viewCount", "view_count", "playCount", "statistics.viewCount")
    aliases = {
        "likes": ("likesCount", "likeCount", "diggCount", "numLikes", "likes", "Likes", "Reactions", "statistics.likeCount"),
        "comments": ("commentsCount", "commentCount", "replyCount", "numComments", "comments", "Comments"),
        "shares": ("shareCount", "sharesCount", "shares", "Shares"),
        "sends": ("sendCount", "dmSends", "sends"),
        "saves": ("savesCount", "collectCount", "bookmarkCount", "saves", "Saves"),
        "profile_visits": ("profileVisits", "profile_visits"),
        "substantive_comments": ("substantiveCommentsCount",),
        "author_replies": ("authorEngagedReplies",),
        "reposts_quotes": ("repostsQuotesCount",),
        "saves_sends": ("savesSendsCount",),
        "profile_actions": ("profileActionsCount",),
        "meaningful_threads": ("meaningfulThreadsCount",),
        "clicks": ("clicks", "Clicks"),
        "subscribes": ("subscribes", "subscribersGained"),
    }
    for name, numerator in aliases.items():
        if name in signals and signals[name] is None and name not in supplied:
            value = rate(post, numerator, denominator)
            if value is not None:
                signals[name] = value
                sources[name] = {"numerator_aliases": numerator, "denominator_aliases": denominator}
    missing = [name for name, value in signals.items() if value is None]
    covered = sum(weights[name] for name, value in signals.items() if value is not None)
    contribution = sum(weights[name] * value * 100 for name, value in signals.items() if value is not None)
    complete = not missing and math.isclose(sum(weights.values()), 1.0)
    return {
        "version": POLICY["version"], "provenance": POLICY["provenance"],
        "profile": profile, "score": round(contribution, 6) if complete else None,
        "observed_contribution": round(contribution, 6) if covered else None,
        "coverage": round(covered, 6), "status": "complete_policy_score" if complete else "partial_evidence",
        "missing": missing, "signals": signals, "sources": sources,
        "denominator": denominator[0], "unassigned_weight": round(1 - sum(weights.values()), 6),
        "modifiers_applied": False,
        "modifier_note": "Research outliers use signal weights only. Editorial multipliers/bonuses are configured separately, not inferred from engagement counts.",
    }


def media_format(post):
    for key in ("format", "type", "Post Type", "Content Type"):
        value = post.get(key)
        if isinstance(value, str) and value.strip():
            value = value.strip().lower()
            if value in {"unknown", "none", "null", "n/a"}:
                continue
            return {"sidecar": "carousel", "pdf": "document_carousel", "document": "document_carousel"}.get(value, value)
    return None


def infer_tiktok_format(item):
    """Preserve provider format evidence, including photo/slideshow posts."""
    if item.get("isSlideshow") is True:
        return "slideshow"
    declared = media_format(item)
    if declared in {"video", "reel", "photo", "image", "carousel", "slideshow"}:
        return declared
    duration = first(item, "videoMeta.duration", "videoDuration")
    return "video" if duration is not None and duration > 0 else None


def identify_policy_outliers(posts, platform, threshold_multiplier=2.0):
    groups = defaultdict(list)
    for post in posts:
        result = score_post(post, platform)
        post["_avs"] = result
        post["_matrix_version"] = POLICY["version"]
        post["_engagement_score"] = result["score"]
        post["_engagement_rate"] = None  # legacy key retained; AVS is not an engagement rate
        if result["observed_contribution"] is not None and media_format(post) is not None:
            key = (result["profile"], media_format(post),
                   result["denominator"], tuple(result["sources"]))
            groups[key].append(post)
    selected = []
    for group in groups.values():
        if len(group) < 3:
            continue
        values = [p["_avs"]["observed_contribution"] for p in group]
        deviation = statistics.stdev(values)
        if deviation == 0:
            continue
        cutoff = statistics.mean(values) + threshold_multiplier * deviation
        for post in group:
            if post["_avs"]["observed_contribution"] > cutoff:
                post["_outlier_basis"] = "descriptive_same_coverage_policy_contribution"
                post["_comparison_count"] = len(group)
                selected.append(post)
    return sorted(selected, key=lambda p: p["_avs"]["observed_contribution"], reverse=True)
