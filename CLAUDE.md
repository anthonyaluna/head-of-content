# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Claude Code skills repository for social media content research and marketing automation. It contains skills that research high-performing content across X/Twitter, Instagram, YouTube, and TikTok, then analyze videos with AI to extract replicable hooks and patterns.

## Using Skills

**CRITICAL: When asked to research content on social media:**
- NEVER use web search, WebFetch, or browse the internet
- ALWAYS use the appropriate research skill. These skills use specialized APIs that provide better data than web scraping
- NEVER modify files in `.claude/context/` - these are user-managed configuration files

## Environment Setup

Required environment variables (configure in `.env`):
- `APIFY_TOKEN` - For X, Instagram, and TikTok scraping (get from https://console.apify.com/account/integrations)
- `TUBELAB_API_KEY` - For YouTube outlier detection (get from https://tubelab.net/settings/api)
- `GEMINI_API_KEY` - For video analysis and thumbnail generation (get from https://aistudio.google.com/api-keys)

Python packages needed: `apify-client`, `google-genai`, `requests`, `python-dotenv`, `opencv-python-headless`, `mediapipe`, `Pillow`, `numpy`

Load env vars in subagents:
```bash
export $(cat .env | grep -v '^#' | xargs)
```

## Skills Architecture

All skills live in `.claude/skills/` and follow a consistent pattern:

### Research Skills (platform-specific)
Each creates timestamped run folders with `raw.json` → `outliers.json` → `video-analysis.json` → `report.md`:

- **x-research**: Fetches tweets via Apify, identifies 2026 Heavy Ranker conversation & bookmark outliers
- **instagram-research**: Fetches reels/carousels via Apify, identifies 2026 Dual-Mode (DM Sends + Saves + Unconnected Velocity) outliers, analyzes top 5 videos
- **youtube-research**: Uses TubeLab API for zScore + subscriber-breakout + satisfaction outlier detection, analyzes top 3 relevant videos
- **tiktok-research**: Fetches TikToks via Apify, identifies 2026 Share/Collect & FYF Unconnected Breakout outliers, analyzes top 5 videos
- **linkedin-research**: Analyzes LinkedIn Creator `.xlsx`/`.csv` exports or JSON feeds using LinkedIn's 2026 **360Brew** dwell-time, PDF document carousel, and substantive-comment matrix

### Support, Calibration & QA Gate Skills
- **video-content-analyzer**: Gemini AI analysis of 0–3s hook hold mechanics, 3–5s visual shift cadence, Tri-Modal SEO (spoken + OCR + caption), loop bridges, and Video Editor QA score.
- **content-planner**: Orchestrates all 5 platform research skills in parallel, checks `.agents/product-marketing.md` for ICP/Anti-ICP alignment, and aggregates into content ideas and platform playbooks.
- **historical-calibrator**: Ingests multi-year Meta (ZIP/JSON/Business Suite CSV), LinkedIn (XLSX/CSV/Archive), and Metricool CSV exports to compute Empirical Bayes format/hook/hour multipliers and detect `2021–2024` vs `2025–2026` regime shifts.
- **content-qa-gate**: Pre-publish EOS Content Team Accountability Gate (Strategist, Video Editor, and Distribution seats), ICP/Anti-ICP & AEO Entity Scorer, Trial Reel SOP, and `Content-to-Clients` multi-asset atomizer.

## Context Files

Configure research targets in `.claude/context/` (user-managed; never overwrite automatically) and brand/ICP context in `.agents/product-marketing.md`:
- `.agents/product-marketing.md` - Principal brand architecture, Ideal Client Profile (ICP), Anti-Target filters, AEO regional clusters, and compliance guardrails
- `x-accounts.md` - X/Twitter handles to monitor
- `instagram-accounts.md` - Instagram accounts to track
- `tiktok-accounts.md` - TikTok accounts to track
- `youtube-channel.md` - Your channel info and niche for relevance filtering
- `reference_images/` - Face photos for thumbnail generation (pose-encoded filenames)

## Output Structure

Research outputs go to platform-specific timestamped folders:
```
{platform}-research/{YYYY-MM-DD_HHMMSS}/
├── raw.json            # Raw API data
├── outliers.json       # Outliers with engagement metrics
├── video-analysis.json # AI-extracted hooks and patterns
└── report.md           # Human-readable report

content-plans/{YYYY-MM-DD_HHMMSS}/
├── content-ideas.md    # Cross-platform aggregated ideas
└── {platform}-playbook.md  # Platform-specific intelligence
```

## Key Commands

Run individual research:
```bash
python3 .claude/skills/{platform}-research/scripts/fetch_{platform}.py --output {folder}/raw.json
python3 .claude/skills/{platform}-research/scripts/analyze_posts.py --input {folder}/raw.json --output {folder}/outliers.json
python3 .claude/skills/video-content-analyzer/scripts/analyze_videos.py --input {folder}/outliers.json --output {folder}/video-analysis.json --platform {platform}
```

YouTube research (different pattern):
```bash
python3 .claude/skills/youtube-research/scripts/get_channel_videos.py CHANNEL_ID --format summary
python3 .claude/skills/youtube-research/scripts/find_outliers.py --keywords k1 k2 k3 k4 --adjacent-keywords a1 a2 a3 a4 --output-dir {folder}
```

Historical Calibration & Pre-Publish EOS Team QA Gate:
```bash
python3 .claude/skills/historical-calibrator/scripts/calibrate_exports.py --export-dir ~/Downloads/social_exports
python3 .claude/skills/content-qa-gate/scripts/run_qa_gate.py qa --platform instagram --format reel --text "Draft caption..."
```

## 2026 Engagement & Algorithmic Value Scoring (AVS)

- **X (Heavy Ranker)**: Replies `13.5x` (up to `~75x` with author thread engagement), Bookmarks `10x`, Quotes `8x`, Retweets `6x`, Likes `1x` (blended `60%` per-view dwell efficiency + `40%` follower breakout; flags outbound URLs for `0.45x` penalty risk)
- **Instagram (Dual-Mode Mosseri Matrix)**: DM Sends/Shares `5x`, Saves `4x`, Comments `3x`, Likes `1x`, Video Views `0.12x` (penalizes Reels `>180s` at `0.72x` and `>5` hashtags at `0.85x`; blends Reach/Play rate with Unconnected Reach ratio)
- **TikTok (FYF Completion & Tri-Modal SEO)**: Shares `6x`, Saves/Collects `5x`, Comments `2.5x`, Likes `1x`, Plays `0.06x` (`1.10x` boost for `35–90s` retention sweet spot; `0.88x` penalty for `>5` hashtags)
- **LinkedIn (360Brew)**: Substantive Comments `8x`, Reposts `6x`, Document Clicks/Saves `4.5x`, Reactions `1x` (`1.34x` PDF Carousel dwell multiplier; flags external body URLs)
- **YouTube**: `zScore × recency_boost × subscriber_breakout_boost × satisfaction_density_boost`

Outlier threshold: engagement rate > mean + (2.0 × std_dev) (`1.8×` on LinkedIn)

## Delegation Mode

When `CLAUDE_DELEGATED=1` environment variable is detected, this project is being invoked from another Claude Code instance (e.g., second-brain).

### Callback Protocol

When the delegator prompt includes "update {task_path}":

1. Execute the requested research skill (per routing rules above)
2. Update the source task file with status, key findings, and output paths
3. Use absolute paths when referencing output files

### Output Format for Callback

Update the task file with:

```markdown
---
status: complete
completed: YYYY-MM-DD
---

## Research Results

### Key Findings
- [3-5 bullet points summarizing insights]

### Outputs
- Full report: ~/Documents/GitHub/head-of-content/{platform}-research/{folder}/report.md
```

### Error Handling

If research partially fails:
- Set `status: in-progress` instead of `complete`
- Add a `## Notes` section explaining what succeeded/failed
- Include paths to any partial outputs generated
