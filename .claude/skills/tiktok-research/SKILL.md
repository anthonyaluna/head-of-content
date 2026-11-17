---
name: tiktok-research
description: |
  Research high-performing TikTok videos from tracked accounts using Apify's TikTok Scraper.
  Identifies outlier content, analyzes top 5 videos with AI, and generates reports with actionable hook formulas.

  Use when asked to:
  - Find trending TikTok content in a niche
  - Research what's performing on TikTok
  - Identify high-performing video patterns
  - Analyze competitors' TikTok content
  - Generate content ideas from TikTok trends
  - Run TikTok research
  - Find viral TikToks
  - Analyze hooks and content structure

  Triggers: "tiktok research", "tt research", "find trending tiktoks", "analyze tiktok accounts",
  "what's working on tiktok", "content research tiktok", "tiktok analysis", "tiktok trends"
---

# TikTok Research

Research high-performing TikTok videos, identify outliers, and analyze top video content for hooks and structure.

## Evidence-aware v2.1 policy

Read `.claude/lib/SCORING.md` and `.claude/lib/social_policy_2026.json` before interpreting results. The weights and targets are user-supplied policy, not official ranking coefficients. Use actual platform metrics with their units, denominator, window, and source. Missing private sends, saves, completion, dwell, or satisfaction remain null. An AI video inspection supplies creative observations, never measured viewer behavior. Retain every `_avs` coverage record even when no outlier can be established. Compare like-format, like-coverage cohorts only. Do not infer non-follower reach from plays/followers or public shares.

The shared `.claude/lib` directory must accompany these repository skills when distributed. The legacy root `.skill` archives are older snapshots and must not be used to install this v2.1 revision. Use the current source directories together.


## Prerequisites

- `APIFY_TOKEN` environment variable or in `.env`
- `GEMINI_API_KEY` environment variable or in `.env`
- `apify-client` and `google-genai` Python packages
- Accounts configured in `.claude/context/tiktok-accounts.md`

Verify setup:
```bash
python3 -c "
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from apify_client import ApifyClient
from google import genai
assert os.environ.get('APIFY_TOKEN'), 'APIFY_TOKEN not set'
assert os.environ.get('GEMINI_API_KEY'), 'GEMINI_API_KEY not set'
" && echo "Prerequisites OK"
```

## Workflow

### 1. Create Run Folder

```bash
RUN_FOLDER="tiktok-research/$(date +%Y-%m-%d_%H%M%S)" && mkdir -p "$RUN_FOLDER" && echo "$RUN_FOLDER"
```

### 2. Fetch Content

```bash
python3 .claude/skills/tiktok-research/scripts/fetch_tiktok.py \
  --days 30 \
  --limit 50 \
  --sorting latest \
  --output {RUN_FOLDER}/raw.json
```

Parameters:
- `--days`: Days back to search (default: 30)
- `--limit`: Max videos per account (default: 50)
- `--sorting`: "latest", "popular", or "oldest" (default: latest)
- `--usernames`: Override accounts file with specific usernames

### 3. Identify Outliers

```bash
python3 .claude/skills/tiktok-research/scripts/analyze_posts.py \
  --input {RUN_FOLDER}/raw.json \
  --output {RUN_FOLDER}/outliers.json \
  --threshold 2.0
```

Output JSON contains:
- `total_videos`: Number of videos analyzed
- `outlier_count`: Number of outliers found
- `topics`: Top hashtags, sounds, and keywords
- `accounts`: List of accounts analyzed
- `outliers`: Array of outlier videos with engagement metrics

### 4. Analyze Top Videos with AI

```bash
python3 .claude/skills/video-content-analyzer/scripts/analyze_videos.py \
  --input {RUN_FOLDER}/outliers.json \
  --output {RUN_FOLDER}/video-analysis.json \
  --platform tiktok \
  --max-videos 5
```

Extracts from each video:
- Hook technique and replicable formula
- Content structure and sections
- Retention techniques
- CTA strategy

See the `video-content-analyzer` skill for full output schema and hook/format types.

### 5. Generate Report

Read `{RUN_FOLDER}/outliers.json` and `{RUN_FOLDER}/video-analysis.json`, then generate `{RUN_FOLDER}/report.md`.

**Report Structure:**

```markdown
# TikTok Research Report

Generated: {date}

## Top Performing Hooks

Ranked by comparable observed policy contribution. Describe creative hypotheses, not guaranteed formulas.

### Hook 1: {technique} - @{username}
- **Opening**: "{opening_line}"
- **Why it works**: {attention_grab}
- **Replicable Formula**: {replicable_formula}
- **Engagement**: {diggCount} likes, {commentCount} comments, {playCount} views
- [Watch Video]({webVideoUrl})

[Repeat for each analyzed video]

## Content Structure Patterns

| Video | Format | Pacing | Key Retention Techniques |
|-------|--------|--------|--------------------------|
| @username | {format} | {pacing} | {techniques} |

## CTA Strategies

| Video | CTA Type | CTA Text | Placement |
|-------|----------|----------|-----------|
| @username | {type} | "{cta_text}" | {placement} |

## All Outliers

| Rank | Username | Likes | Comments | Shares | Views | AVS contribution / coverage |
|------|----------|-------|----------|--------|-------|-----------------|
[List all outliers with metrics and links]

## Trending Topics

### Top Hashtags
[From outliers.json topics.hashtags]

### Top Sounds
[From outliers.json topics.sounds]

### Top Keywords
[From outliers.json topics.keywords]

## Actionable Takeaways

[Synthesize patterns into 4-6 specific recommendations]

## Accounts Analyzed
[List accounts]
```

Focus on actionable insights. The "Top Performing Hooks" section with replicable formulas should be prominent.

## Quick Reference

Full pipeline:
```bash
RUN_FOLDER="tiktok-research/$(date +%Y-%m-%d_%H%M%S)" && mkdir -p "$RUN_FOLDER" && \
python3 .claude/skills/tiktok-research/scripts/fetch_tiktok.py -o "$RUN_FOLDER/raw.json" && \
python3 .claude/skills/tiktok-research/scripts/analyze_posts.py -i "$RUN_FOLDER/raw.json" -o "$RUN_FOLDER/outliers.json" && \
python3 .claude/skills/video-content-analyzer/scripts/analyze_videos.py -i "$RUN_FOLDER/outliers.json" -o "$RUN_FOLDER/video-analysis.json" -p tiktok
```

Then read both JSON files and generate the report.

## Evidence and outlier scoring

Use the exact v2026.11 signal weights in `.claude/lib/social_policy_2026.json`.
Report `_avs.score` only if complete, otherwise report `_avs.observed_contribution` as partial with coverage and missing signals. Outliers exceed the mean plus the chosen standard-deviation multiple within an identical-coverage/format cohort of at least three records. This descriptive statistic does not prove a causal content tactic. Do not call the weighted score an engagement rate or divide it by follower count.


## TikTok-Specific Fields

- `diggCount`: Likes/hearts
- `shareCount`: Shares
- `playCount`: Video views
- `commentCount`: Comments
- `collectCount`: Saves/bookmarks
- `authorFollowers`: Creator's follower count
- `musicName`: Sound used in video
- `musicOriginal`: Whether sound is original
