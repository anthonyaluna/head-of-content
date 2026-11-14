#!/usr/bin/env python3
"""
Identify outlier Instagram posts/reels based on engagement metrics.
Outputs JSON with outliers and metadata for report generation.
"""

import json
import argparse
import statistics
from datetime import datetime
from pathlib import Path
from collections import Counter
import re


def load_posts(input_path: str) -> list[dict]:
    """Load posts from JSON file."""
    with open(input_path, 'r') as f:
        return json.load(f)


def calculate_engagement_score(post: dict) -> float:
    """
    Calculate 2026 Instagram Dual-Mode Algorithmic Value Score (AVS) raw weighted engagement.
    2026 Mosseri Ranking Priorities:
    1. Watch Time / Completion Velocity (Unconnected Reels/Explore primary gate)
    2. DM Sends / Reshares per Reach (~5x weight — #1 Unconnected expansion signal)
    3. Saves / Bookmarks per Reach (~4x weight — #1 Connected Feed retention signal)
    4. Substantive Comments (~3x weight)
    5. Likes (~1x weight — passive approval)
    Penalties:
    - Reels > 180s excluded from non-follower Explore/Reels recommendation pools (0.72x)
    - > 5 hashtags triggers 2026 hashtag-stuffing classifier demotion (0.85x)
    """
    likes = post.get('likesCount', 0) or 0
    comments = post.get('commentsCount', 0) or 0
    shares = (
        post.get('sharesCount')
        or post.get('reshareCount')
        or post.get('sendCount')
        or 0
    )
    saves = post.get('savesCount') or post.get('collectCount') or 0
    video_views = post.get('videoViewCount', 0) or post.get('videoPlayCount', 0) or 0
    duration = float(post.get('videoDuration') or post.get('duration') or 0)
    caption = post.get('caption', '') or ''
    tag_count = len(post.get('hashtags') or re.findall(r'#(\w+)', caption))

    weighted = (
        likes
        + (3.0 * comments)
        + (5.0 * shares)
        + (4.0 * saves)
        + (0.12 * video_views)
    )
    penalty_mult = 1.0
    if duration > 180:
        penalty_mult *= 0.72
    if tag_count > 5:
        penalty_mult *= 0.85
    return round(weighted * penalty_mult, 2)


def calculate_engagement_rate(post: dict) -> float:
    """
    Calculate 2026 exposure-normalized engagement & Unconnected Reach velocity rate.
    Blends Reach/Play-normalized action density (60%) with Follower breakout velocity (40%)
    so non-follower Reels breakouts and high-save carousels are surfaced accurately.
    """
    followers = post.get('ownerFollowersCount', 0) or 0
    plays = post.get('videoPlayCount', 0) or post.get('videoViewCount', 0) or post.get('reach', 0) or 0
    engagement = calculate_engagement_score(post)

    denom_followers = max(followers, 100) if followers > 0 else max(plays, 100)
    follower_rate = (engagement / denom_followers) * 100.0

    if plays > 0:
        play_rate = (engagement / max(plays, 100)) * 100.0
        unconnected_breakout = min(3.0, plays / max(denom_followers, 1))
        return round((0.55 * play_rate + 0.45 * follower_rate) * (0.85 + 0.15 * unconnected_breakout), 3)
    return round(follower_rate, 3)


def identify_outliers(posts: list[dict], threshold_multiplier: float = 2.0) -> list[dict]:
    """
    Identify outlier posts with 2026 AVS engagement rate > mean + (threshold × std_dev).
    """
    if not posts:
        return []

    for post in posts:
        post['_engagement_score'] = calculate_engagement_score(post)
        post['_engagement_rate'] = calculate_engagement_rate(post)
        followers = max(1, post.get('ownerFollowersCount', 0) or 1)
        plays = post.get('videoPlayCount', 0) or post.get('videoViewCount', 0) or 0
        post['_unconnected_reach_ratio'] = round(plays / followers, 2) if plays else 0.0
        post['_matrix_version'] = '2026.1-dual-mode-sends-saves'

    rates = [p['_engagement_rate'] for p in posts]
    if len(rates) < 2:
        return posts

    mean_rate = statistics.mean(rates)
    std_dev = statistics.stdev(rates) if len(rates) > 1 else 0
    threshold = mean_rate + (threshold_multiplier * std_dev)

    outliers = [p for p in posts if p['_engagement_rate'] > threshold]
    outliers.sort(key=lambda x: x['_engagement_score'], reverse=True)
    return outliers


def extract_topics(posts: list[dict]) -> dict:
    """Extract trending hashtags, mentions, and keywords."""
    hashtags = Counter()
    keywords = Counter()

    stop_words = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who',
        'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both', 'few',
        'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
        'own', 'same', 'so', 'than', 'too', 'very', 'just', 'and', 'but',
        'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by',
        'for', 'with', 'about', 'against', 'between', 'into', 'through',
        'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up',
        'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further',
        'then', 'once', 'here', 'there', 'your', 'my', 'his', 'her', 'its',
        'our', 'their', 'get', 'got', 'like', 'dont', 'im', 'ive', 'youre',
        'https', 'http', 'amp', 'link', 'bio', 'comment', 'follow', 'check'
    }

    for post in posts:
        caption = post.get('caption', '') or ''

        # Hashtags
        post_hashtags = post.get('hashtags', []) or []
        if isinstance(post_hashtags, list):
            hashtags.update([h.lower().lstrip('#') for h in post_hashtags])
        hashtags.update(re.findall(r'#(\w+)', caption.lower()))

        # Keywords
        text_clean = re.sub(r'https?://\S+', '', caption)
        text_clean = re.sub(r'[@#]\w+', '', text_clean)
        text_words = re.findall(r'\b[a-zA-Z]{4,}\b', text_clean.lower())
        keywords.update([w for w in text_words if w not in stop_words])

    return {
        'hashtags': hashtags.most_common(20),
        'keywords': keywords.most_common(30)
    }


def main():
    parser = argparse.ArgumentParser(description='Identify Instagram outliers')
    parser.add_argument('--input', '-i', required=True, help='Input JSON file')
    parser.add_argument('--output', '-o', required=True, help='Output JSON file')
    parser.add_argument('--threshold', '-t', type=float, default=2.0,
                        help='Outlier threshold multiplier (default: 2.0)')

    args = parser.parse_args()

    print(f"Loading posts from: {args.input}")
    posts = load_posts(args.input)
    print(f"Loaded {len(posts)} posts/reels")

    print(f"Identifying outliers (threshold: {args.threshold}x std dev)...")
    outliers = identify_outliers(posts, args.threshold)
    print(f"Found {len(outliers)} outlier posts")

    print("Extracting topics...")
    topics = extract_topics(posts)

    # Build output with metadata
    output = {
        'generated': datetime.now().isoformat(),
        'total_posts': len(posts),
        'outlier_count': len(outliers),
        'threshold': args.threshold,
        'topics': topics,
        'accounts': list(set(p.get('ownerUsername', '') for p in posts if p.get('ownerUsername'))),
        'outliers': outliers
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print(f"Outliers saved to: {args.output}")
    print(f"- {len(outliers)} outliers identified")
    if topics['hashtags']:
        print(f"- Top hashtag: #{topics['hashtags'][0][0]}")
    if topics['keywords']:
        print(f"- Top keyword: {topics['keywords'][0][0]}")


if __name__ == '__main__':
    main()
