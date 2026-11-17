---
name: youtube-research
description: |
  Research high-performing YouTube videos in a niche using TubeLab's outlier detection API.
  Identifies outlier videos, analyzes top 3 relevant videos with AI, and generates reports with actionable hook formulas.

  Use when asked to:
  - Find trending videos in a YouTube niche
  - Research competitor content
  - Discover viral video patterns
  - Generate content ideas based on what's working
  - Run YouTube research
  - Find outlier videos
  - Analyze hooks and content structure

  Triggers: "youtube research", "find outlier videos", "research YouTube trends",
  "what videos are performing well", "find content ideas for my channel", "youtube trends"
---

# YouTube Research

Research high-performing YouTube outlier videos, analyze top content with AI, and generate actionable reports.

## Evidence-aware v2.1 policy

Read `.claude/lib/SCORING.md` and `.claude/lib/social_policy_2026.json` before interpreting results. The weights and targets are user-supplied policy, not official ranking coefficients. Use actual platform metrics with their units, denominator, window, and source. Missing private sends, saves, completion, dwell, or satisfaction remain null. An AI video inspection supplies creative observations, never measured viewer behavior. Retain every `_avs` coverage record even when no outlier can be established. Compare like-format, like-coverage cohorts only. Do not infer non-follower reach from plays/followers or public shares.

The shared `.claude/lib` directory must accompany these repository skills when distributed. The legacy root `.skill` archives are older snapshots and must not be used to install this v2.1 revision. Use the current source directories together.


## Prerequisites

- `TUBELAB_API_KEY` environment variable. Get key from https://tubelab.net/settings/api
- `GEMINI_API_KEY` environment variable (for video analysis)
- `google-genai` and `requests` Python packages

## Workflow

### Step 1: Create Run Folder

```bash
mkdir -p youtube-research/$(date +%Y-%m-%d_%H%M%S)
```

### Step 2: Get Channel ID

Read `.claude/context/youtube-channel.md` to get the channel ID.

### Step 3: Fetch Channel Videos

```bash
python scripts/get_channel_videos.py CHANNEL_ID --format summary
```

This returns JSON with the channel's video titles and view counts.

### Step 4: Analyze Channel

Analyze the channel data to extract:
- **keywords**: 4 search terms for the channel's direct niche
- **adjacent-keywords**: 4 search terms for topics the same audience watches
- **audience**: 2-3 profiles with objections, transformations, stakes
- **formulas**: Reusable title templates

See `references/channel-analysis-schema.md` for the full schema and example output.

### Step 5: Search for Outliers

Run the outlier search with both keyword sets:

```bash
python .claude/skills/youtube-research/scripts/find_outliers.py \
  --keywords "keyword1" "keyword2" "keyword3" "keyword4" \
  --adjacent-keywords "adjacent1" "adjacent2" "adjacent3" "adjacent4" \
  --output-dir youtube-research/{run-folder} \
  --top 5
```

This runs two searches:
- **Direct niche**: keywords with 5K+ views threshold
- **Adjacent audience**: adjacent-keywords with 10K+ views threshold

Output files:
- `outliers.json` - All outliers normalized for video analysis
- `report.md` - Basic markdown report
- `thumbnails/*.jpg` - Video thumbnails
- `transcripts/*.txt` - Video transcripts

### Step 6: Filter Relevant Videos for Analysis

Read `outliers.json` and the user's niche from `.claude/context/youtube-channel.md`.

**CRITICAL**: Select MAX 3 videos that are most relevant to the user's niche. Filter by:
1. **Title relevance**: Title contains keywords related to user's niche/topics
2. **Transcript relevance**: If transcript exists, check it mentions relevant topics
3. **Direct niche priority**: Prefer videos from direct keyword search over adjacent

Skip videos that are clearly outside the user's content style (e.g., entertainment/vlogs when user does tutorials).

Write the filtered videos to `{RUN_FOLDER}/filtered-outliers.json`:
```json
{
  "outliers": [/* max 3 relevant videos */],
  "filter_reason": "Selected based on relevance to [user's niche]"
}
```

### Step 7: Analyze Top Videos with AI

```bash
python3 .claude/skills/video-content-analyzer/scripts/analyze_videos.py \
  --input {RUN_FOLDER}/filtered-outliers.json \
  --output {RUN_FOLDER}/video-analysis.json \
  --platform youtube \
  --max-videos 3
```

Extracts from each video:
- Hook technique and replicable formula
- Content structure and sections
- Retention techniques
- CTA strategy

See the `video-content-analyzer` skill for full output schema and hook/format types.

### Step 8: Generate Final Report

Read `{RUN_FOLDER}/outliers.json` and `{RUN_FOLDER}/video-analysis.json`, then generate `{RUN_FOLDER}/report.md`.

**Report Structure:**

```markdown
# YouTube Research Report

Generated: {date}

## Top Performing Hooks

Ranked by engagement. Use these formulas for your content.

### Hook 1: {technique} - {channelTitle}
- **Video**: "{title}"
- **Opening**: "{opening_line}"
- **Why it works**: {attention_grab}
- **Replicable Formula**: {replicable_formula}
- **Views**: {viewCount} | **zScore**: {zScore}
- [Watch Video]({url})

[Repeat for each analyzed video]

## Content Structure Patterns

| Video | Format | Pacing | Key Retention Techniques |
|-------|--------|--------|--------------------------|
| {title} | {format} | {pacing} | {techniques} |

## CTA Strategies

| Video | CTA Type | CTA Text | Placement |
|-------|----------|----------|-----------|
| {title} | {type} | "{cta_text}" | {placement} |

## All Outliers

### Direct Niche
| Rank | Channel | Title | Views | zScore |
|------|---------|-------|-------|--------|
[List direct niche outliers]

### Adjacent Audience
| Rank | Channel | Title | Views | zScore |
|------|---------|-------|-------|--------|
[List adjacent outliers]

## Actionable Takeaways

[Synthesize patterns into 4-6 specific recommendations based on video analysis]
```

Focus on actionable insights. The "Top Performing Hooks" section with replicable formulas should be prominent.

## Quick Reference

Full pipeline:
```bash
RUN_FOLDER="youtube-research/$(date +%Y-%m-%d_%H%M%S)" && mkdir -p "$RUN_FOLDER" && \
python .claude/skills/youtube-research/scripts/find_outliers.py \
  --keywords "k1" "k2" "k3" "k4" \
  --adjacent-keywords "a1" "a2" "a3" "a4" \
  --output-dir "$RUN_FOLDER" --top 5
```

Then filter outliers for niche relevance (max 3), run video analysis, and generate the report.

## Script Reference

### get_channel_videos.py

```
python .claude/skills/youtube-research/scripts/get_channel_videos.py CHANNEL_ID [--format json|summary]
```

| Arg | Description |
|-----|-------------|
| `CHANNEL_ID` | YouTube channel ID (24 chars) |
| `--format` | `json` (full data) or `summary` (for analysis) |

### find_outliers.py

```
python .claude/skills/youtube-research/scripts/find_outliers.py --keywords K1 K2 K3 K4 --adjacent-keywords A1 A2 A3 A4 --output-dir DIR [options]
```

| Arg | Description |
|-----|-------------|
| `--keywords` | Direct niche keywords (4 recommended) |
| `--adjacent-keywords` | Adjacent topic keywords (4 recommended) |
| `--output-dir` | Output directory (required) |
| `--top` | Videos per category (default: 5) |
| `--days` | Days back to search (default: 30) |
| `--json` | Also save raw JSON data |

Output: `outliers.json`, `report.md`, `thumbnails/`, `transcripts/`

## Discovery and policy evidence

Provider `zScore` orders discovery candidates. Owned audience signals use the separate v2026.11 policy in `.claude/lib/social_policy_2026.json`. Do not infer satisfaction from likes/comments, subscriber counts, or recency. Report missing format and missing analytics explicitly; provider zScore is not a 0–100 algorithm score.
