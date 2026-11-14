#!/usr/bin/env python3
"""
Identify outlier TikTok videos based on engagement metrics.
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
    """Load videos from JSON file."""
    with open(input_path, 'r') as f:
        return json.load(f)


def calculate_engagement_score(video: dict) -> float:
    """
    Calculate 2026 TikTok For You Feed (FYF) Algorithmic Value Score.
    2026 TikTok Signal Hierarchy:
    - Shares / Reposts (6.0x): Highest off-feed & DM expansion trigger
    - Saves / Collects (5.0x): Search & evergreen authority index signal
    - Comments (2.5x): Active thread dwell
    - Likes / Diggs (1.0x): Baseline approval
    - Plays (0.06x): Auto-play baseline
    Format & SEO Modifiers:
    - 35–90s narrative/educational sweet spot (1.10x) vs <7s loop-bait clamp (0.85x)
    - >5 hashtags penalty (0.88x since Aug 2025 5-tag limit)
    """
    likes = video.get('diggCount', 0) or 0
    comments = video.get('commentCount', 0) or 0
    shares = video.get('shareCount', 0) or 0
    saves = video.get('collectCount', 0) or 0
    plays = video.get('playCount', 0) or 0
    duration = float(video.get('videoMeta', {}).get('duration', 0) if isinstance(video.get('videoMeta'), dict) else (video.get('duration') or 0))
    text = video.get('text', '') or ''
    tag_count = len(video.get('hashtags') or re.findall(r'#(\w+)', text))

    raw = likes + (2.5 * comments) + (6.0 * shares) + (5.0 * saves) + (0.06 * plays)
    mult = 1.0
    if 35 <= duration <= 90:
        mult *= 1.10
    elif 0 < duration < 7:
        mult *= 0.85
    if tag_count > 5:
        mult *= 0.88
    return round(raw * mult, 2)


def calculate_engagement_rate(video: dict) -> float:
    """
    Calculate 2026 FYF Unconnected Breakout & Action-per-Play rate.
    TikTok's interest graph decouples reach from follower count; we blend
    high-intent action rate per play (65%) with follower breakout velocity (35%).
    """
    followers = video.get('authorFollowers', 0) or (video.get('authorMeta', {}) or {}).get('fans', 0) or 0
    plays = video.get('playCount', 0) or 0
    engagement = calculate_engagement_score(video)

    play_denom = max(plays, 250)
    play_action_rate = (engagement / play_denom) * 100.0
    if followers <= 0:
        return round(play_action_rate, 3)

    follower_rate = (engagement / max(followers, 100)) * 100.0
    breakout_boost = min(2.5, max(0.8, (plays / max(followers, 100)) ** 0.25))
    return round(((0.65 * play_action_rate) + (0.35 * follower_rate)) * breakout_boost, 3)


def identify_outliers(videos: list[dict], threshold_multiplier: float = 2.0) -> list[dict]:
    """
    Identify outlier videos with 2026 AVS rate > mean + (threshold x std_dev).
    """
    if not videos:
        return []

    for video in videos:
        video['_engagement_score'] = calculate_engagement_score(video)
        video['_engagement_rate'] = calculate_engagement_rate(video)
        plays = max(1, video.get('playCount', 0) or 1)
        shares = video.get('shareCount', 0) or 0
        saves = video.get('collectCount', 0) or 0
        video['_share_save_per_1k_plays'] = round(((shares + saves) / plays) * 1000.0, 2)
        video['_matrix_version'] = '2026.1-fyf-completion-trimodal'

    rates = [v['_engagement_rate'] for v in videos]
    if len(rates) < 2:
        return videos

    mean_rate = statistics.mean(rates)
    std_dev = statistics.stdev(rates) if len(rates) > 1 else 0
    threshold = mean_rate + (threshold_multiplier * std_dev)

    outliers = [v for v in videos if v['_engagement_rate'] > threshold]
    outliers.sort(key=lambda x: x['_engagement_score'], reverse=True)
    return outliers


def extract_topics(videos: list[dict]) -> dict:
    """Extract trending hashtags, sounds, and keywords."""
    hashtags = Counter()
    sounds = Counter()
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
        'https', 'http', 'amp', 'link', 'bio', 'comment', 'follow', 'check',
        'fyp', 'foryou', 'foryoupage', 'viral', 'trending', 'xyzbca'
    }

    for video in videos:
        text = video.get('text', '') or ''

        # Hashtags
        video_hashtags = video.get('hashtags', []) or []
        if isinstance(video_hashtags, list):
            for h in video_hashtags:
                if isinstance(h, dict):
                    tag = h.get('name', '') or h.get('title', '')
                else:
                    tag = str(h)
                if tag and tag.lower() not in stop_words:
                    hashtags[tag.lower().lstrip('#')] += 1
        hashtags.update([h.lower() for h in re.findall(r'#(\w+)', text.lower()) if h.lower() not in stop_words])

        # Sounds/Music
        music_name = video.get('musicName')
        if music_name and music_name.strip():
            sounds[music_name.strip()] += 1

        # Keywords
        text_clean = re.sub(r'https?://\S+', '', text)
        text_clean = re.sub(r'[@#]\w+', '', text_clean)
        text_words = re.findall(r'\b[a-zA-Z]{4,}\b', text_clean.lower())
        keywords.update([w for w in text_words if w not in stop_words])

    return {
        'hashtags': hashtags.most_common(20),
        'sounds': sounds.most_common(10),
        'keywords': keywords.most_common(30)
    }


def main():
    parser = argparse.ArgumentParser(description='Identify TikTok outliers')
    parser.add_argument('--input', '-i', required=True, help='Input JSON file')
    parser.add_argument('--output', '-o', required=True, help='Output JSON file')
    parser.add_argument('--threshold', '-t', type=float, default=2.0,
                        help='Outlier threshold multiplier (default: 2.0)')

    args = parser.parse_args()

    print(f"Loading videos from: {args.input}")
    videos = load_posts(args.input)
    print(f"Loaded {len(videos)} videos")

    print(f"Identifying outliers (threshold: {args.threshold}x std dev)...")
    outliers = identify_outliers(videos, args.threshold)
    print(f"Found {len(outliers)} outlier videos")

    print("Extracting topics...")
    topics = extract_topics(videos)

    # Build output with metadata
    output = {
        'generated': datetime.now().isoformat(),
        'total_videos': len(videos),
        'outlier_count': len(outliers),
        'threshold': args.threshold,
        'topics': topics,
        'accounts': list(set(v.get('authorUsername', '') for v in videos if v.get('authorUsername'))),
        'outliers': outliers
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print(f"Outliers saved to: {args.output}")
    print(f"- {len(outliers)} outliers identified")
    if topics['hashtags']:
        print(f"- Top hashtag: #{topics['hashtags'][0][0]}")
    if topics['sounds']:
        print(f"- Top sound: {topics['sounds'][0][0]}")
    if topics['keywords']:
        print(f"- Top keyword: {topics['keywords'][0][0]}")


if __name__ == '__main__':
    main()
