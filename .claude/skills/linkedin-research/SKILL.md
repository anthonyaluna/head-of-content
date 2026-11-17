---
name: linkedin-research
description: Analyze LinkedIn JSON, CSV, and XLSX exports for descriptive outliers using Coastline's explicit v2026.11 research weights. Use for practitioner-content research with coverage-aware results, never fabricated dwell or substantive-comment metrics.
---

# LinkedIn research

Read `.agents/product-marketing.md` and `.claude/lib/SCORING.md`. The requested 360Brew label is historical/internal, not an assertion about LinkedIn's current deployed ranker. Do not claim a 69% topic-authority weight.

Internal weights: dwell .34, substantive comments .26, saves/sends .18, author reply depth .10, profile actions .08, likes .04. Counts alone do not establish dwell, >12-word comments, reply depth, or private sends.

```bash
python .claude/skills/linkedin-research/scripts/analyze_posts.py \
  --input path/to/creator-export.xlsx --output linkedin-research/run/outliers.json
```

Review each record's `evidence` and `_avs` object. A complete score requires all weighted normalized signals. Partial contributions remain unrescaled and compare only within matching signal-coverage and format groups of at least three posts. Missing impressions cannot be replaced by followers or an invented denominator. JSON, CSV, and XLSX export adapters retain unknown values.

For drafting, use the user policy's 150–240-word atomized post, a concise two-line hook, operator evidence, and a substantive closing question only when useful. Internal format multipliers and link preferences are planning rules, not proven reach lifts. Keep external links in the proposed first comment without claiming an official fixed penalty.
