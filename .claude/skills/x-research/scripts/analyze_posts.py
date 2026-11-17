#!/usr/bin/env python3
"""
Identify outlier X/Twitter posts based on engagement metrics.
Outputs JSON with outliers and metadata for report generation.
"""

import json
import argparse
import statistics
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))
from avs import score_post, identify_policy_outliers
from collections import Counter
import re


def load_posts(input_path: str) -> list[dict]:
    """Load tweets from JSON file."""
    with open(input_path, 'r') as f:
        return json.load(f)


def calculate_engagement_score(post: dict):
    """Full internal policy score, or None when weighted evidence is missing."""
    return score_post(post, "x")["score"]


def calculate_engagement_rate(post: dict):
    """Legacy interface: no composite AVS can be represented as an engagement rate."""
    return None


def identify_outliers(posts: list[dict], threshold_multiplier: float = 2.0) -> list[dict]:
    return identify_policy_outliers(posts, "x", threshold_multiplier)


def extract_topics(tweets: list[dict]) -> dict:
    """
    Extract trending topics, hashtags, and keywords from tweets.
    """
    hashtags = Counter()
    mentions = Counter()
    keywords = Counter()

    # Common stop words to filter out
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
        'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how',
        'your', 'my', 'his', 'her', 'its', 'our', 'their', 'get', 'got',
        'like', 'dont', 'im', 'ive', 'youre', 'youve', 'weve', 'theyre',
        'theyve', 'hes', 'shes', 'thats', 'whats', 'heres', 'theres',
        'https', 'http', 'amp', 'rt', 'via'
    }

    for tweet in tweets:
        text = tweet.get('text', '')

        # Extract hashtags
        tags = re.findall(r'#(\w+)', text.lower())
        hashtags.update(tags)

        # Extract mentions
        ments = re.findall(r'@(\w+)', text.lower())
        mentions.update(ments)

        # Extract significant words (4+ chars, not URLs, not stop words)
        text_clean = re.sub(r'https?://\S+', '', text)
        text_clean = re.sub(r'[@#]\w+', '', text_clean)
        text_words = re.findall(r'\b[a-zA-Z]{4,}\b', text_clean.lower())
        filtered_words = [w for w in text_words if w not in stop_words]
        keywords.update(filtered_words)

    return {
        'hashtags': hashtags.most_common(20),
        'mentions': mentions.most_common(20),
        'keywords': keywords.most_common(30)
    }


def slim_outlier(tweet: dict) -> dict:
    """
    Extract only essential fields from an outlier tweet for lean output.
    """
    author = tweet.get('author', {})

    # Get media URLs if present
    media_urls = []
    if tweet.get('media'):
        media_urls = tweet['media'] if isinstance(tweet['media'], list) else [tweet['media']]
    elif tweet.get('extendedEntities', {}).get('media'):
        for m in tweet['extendedEntities']['media']:
            if m.get('type') == 'video':
                # Get highest quality video URL
                variants = m.get('video_info', {}).get('variants', [])
                mp4s = [v for v in variants if v.get('content_type') == 'video/mp4']
                if mp4s:
                    best = max(mp4s, key=lambda x: x.get('bitrate', 0))
                    media_urls.append(best.get('url'))
            elif m.get('media_url_https'):
                media_urls.append(m['media_url_https'])

    return {
        'url': tweet.get('url', ''),
        'text': tweet.get('text', ''),
        'created_at': tweet.get('createdAt', ''),
        'is_retweet': tweet.get('isRetweet', False),
        'is_quote': tweet.get('isQuote', False),
        'metrics': {
            'likes': tweet.get('likeCount', 0),
            'retweets': tweet.get('retweetCount', 0),
            'replies': tweet.get('replyCount', 0),
            'quotes': tweet.get('quoteCount', 0),
            'bookmarks': tweet.get('bookmarkCount', 0),
            'views': tweet.get('viewCount', 0),
        },
        'engagement_score': tweet.get('_engagement_score'),
        'avs': tweet.get('_avs'),
        'engagement_rate': tweet.get('_engagement_rate'),
        'author': {
            'username': author.get('userName', ''),
            'name': author.get('name', ''),
            'followers': author.get('followers', 0),
        },
        'media': media_urls,
    }


def analyze_content_patterns(outliers: list[dict]) -> dict:
    """
    Analyze content patterns in high-performing tweets.
    """
    patterns = {
        'has_media': 0,
        'has_link': 0,
        'has_thread': 0,
        'is_quote': 0,
        'question': 0,
        'list_format': 0,
        'short_tweet': 0,  # < 100 chars
        'medium_tweet': 0,  # 100-200 chars
        'long_tweet': 0,  # > 200 chars
    }

    for tweet in outliers:
        text = tweet.get('text', '')

        # Check for media
        if tweet.get('media') or tweet.get('extendedEntities'):
            patterns['has_media'] += 1

        # Check for links
        if 'http' in text:
            patterns['has_link'] += 1

        # Check for thread indicator
        if '\U0001f9f5' in text or 'thread' in text.lower() or '/1' in text:
            patterns['has_thread'] += 1

        # Check if quote tweet
        if tweet.get('isQuote'):
            patterns['is_quote'] += 1

        # Check for question
        if '?' in text:
            patterns['question'] += 1

        # Check for list format (numbered or bulleted)
        if re.search(r'^\d\.|\n\d\.|\n-|\n\u2022', text):
            patterns['list_format'] += 1

        # Tweet length
        clean_text = re.sub(r'https?://\S+', '', text)
        if len(clean_text) < 100:
            patterns['short_tweet'] += 1
        elif len(clean_text) < 200:
            patterns['medium_tweet'] += 1
        else:
            patterns['long_tweet'] += 1

    total = len(outliers) if outliers else 1
    percentages = {k: round(v / total * 100, 1) for k, v in patterns.items()}

    return {'counts': patterns, 'percentages': percentages}


def main():
    parser = argparse.ArgumentParser(description='Identify X/Twitter outliers')
    parser.add_argument('--input', '-i', required=True, help='Input JSON file')
    parser.add_argument('--output', '-o', required=True, help='Output JSON file')
    parser.add_argument('--threshold', '-t', type=float, default=2.0,
                        help='Outlier threshold multiplier (default: 2.0)')

    args = parser.parse_args()

    print(f"Loading tweets from: {args.input}")
    tweets = load_posts(args.input)
    print(f"Loaded {len(tweets)} tweets")

    print(f"Identifying outliers (threshold: {args.threshold}x std dev)...")
    outliers = identify_outliers(tweets, args.threshold)
    print(f"Found {len(outliers)} outlier tweets")

    print("Extracting topics...")
    topics = extract_topics(tweets)

    print("Analyzing content patterns...")
    patterns = analyze_content_patterns(outliers)

    # Build output with metadata (slim outliers to essential fields only)
    output = {
        'generated': datetime.now().isoformat(),
        'total_posts': len(tweets),
        'outlier_count': len(outliers),
        "evidence": [p.get("_avs") for p in tweets],
        'threshold': args.threshold,
        'topics': topics,
        'content_patterns': patterns,
        'accounts': list(set(
            t.get('author', {}).get('userName', '')
            for t in tweets if t.get('author', {}).get('userName')
        )),
        'outliers': [slim_outlier(t) for t in outliers]
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
