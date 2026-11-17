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

- **x-research**: Fetches tweets via Apify and compares available policy signals within matched evidence cohorts
- **instagram-research**: Fetches reels/carousels via Apify and compares connected or unconnected policy evidence; unavailable private sends and retention stay missing
- **youtube-research**: Uses TubeLab provider zScore for discovery, with separate coverage-aware owned-analytics scoring, analyzes top 3 relevant videos
- **tiktok-research**: Fetches TikToks via Apify, preserves verified format metadata, and compares available signals without inferring completion or rewatch
- **linkedin-research**: Analyzes LinkedIn Creator `.xlsx`/`.csv` exports or JSON feeds using the user-supplied v2026.11 policy with explicit missing-signal coverage

### Support, Calibration & QA Gate Skills
- **video-content-analyzer**: Gemini AI analysis of 0–3s hook hold mechanics, 3–5s visual shift cadence, Tri-Modal SEO (spoken + OCR + caption), loop bridges, and Video Editor QA score.
- **content-planner**: Orchestrates all 5 platform research skills in parallel, checks `.agents/product-marketing.md` for ICP/Anti-ICP alignment, and aggregates into content ideas and platform playbooks.
- **historical-calibrator**: Stages selected CSV/XLS/XLSX exports, records input hashes, verifies ingest coverage, and runs the explicitly selected canonical engine in an isolated database. ZIP/JSON require canonical harvesting first. Output needs provenance and coverage review before use.
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
python3 .claude/skills/historical-calibrator/scripts/calibrate_exports.py --export-dir ~/Downloads/social_exports --run-dir ~/calibration-new-run --canonical-root /path/to/coastline-codex-agent-os
python3 .claude/skills/content-qa-gate/scripts/run_qa_gate.py qa --input draft.json --canonical-root /path/to/coastline-codex-agent-os
```

## v2026.11 internal policy and evidence

Read `.claude/lib/SCORING.md` and `.claude/lib/social_policy_2026.json`. The JSON records exact user-supplied signal weights, format multipliers, targets, and penalties. These are operating assumptions, not official platform coefficients or the private empirical backtest.

Research scripts use coverage-aware signal contributions. Missing retention, sends, saves, dwell, or satisfaction remain null; no follower-count substitute for reach and no likes-as-watch-time proxy. Full AVS is withheld when incomplete. YouTube provider zScore is separate discovery evidence. LinkedIn 360Brew is a legacy internal label, not the current deployed ranker.

Canonical QA / atomization requires an explicit reviewed Coastline checkout:
```bash
python .claude/skills/content-qa-gate/scripts/run_qa_gate.py qa --input draft.json --canonical-root /path/to/coastline-codex-agent-os
python .claude/skills/historical-calibrator/scripts/calibrate_exports.py --export-dir /path/to/exports --run-dir /path/to/new-run --canonical-root /path/to/coastline-codex-agent-os
```

Do not use a packaged synthetic historical report as Anthony's data. No auto-publication follows from a numeric score. `.claude/context/*` stays user-owned and untouched.

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
