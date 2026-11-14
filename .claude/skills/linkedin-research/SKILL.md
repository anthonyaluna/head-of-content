---
name: linkedin-research
description: |
  Analyze LinkedIn posts, PDF document carousels, and Creator Analytics exports (.xlsx, .csv, JSON)
  using LinkedIn's 2026 360Brew Semantic Dwell & Topic Authority ranking matrix.
  Identifies high-AVS outliers, dwell multipliers, hook patterns, and ICP alignment.
---

# LinkedIn 360Brew Research & Outlier Analyzer

Analyze LinkedIn Creator exports (`.xlsx`, `.csv`), GDPR `Shares.csv`, or scraped LinkedIn JSON feeds using the **2026 LinkedIn 360Brew** ranking hierarchy:
1. **Dwell Time & "See More" Expansion (32%)** — 8–12 slide PDF Document Carousels (`1.34x`) and well-spaced practitioner narratives.
2. **Substantive Threaded Comments (28%)** — Multi-sentence practitioner dialogue (`15+` words) and author back-and-forth within 60 minutes.
3. **Semantic Topic Authority & First-Hand Proof (20%)** — Repeated depth in 2–3 core pillars; demotes generic AI clichés (`0.70x`).
4. **Saves & Reposts (13%)** — Bookmarking frameworks and operational checklists.
5. **External Link Penalty (`0.60x`)** — Outbound links in the post body suppress feed distribution; isolate links to the first comment.

## Usage

```bash
python3 .claude/skills/linkedin-research/scripts/analyze_posts.py \
  --input path/to/linkedin_export_or_raw.json \
  --output linkedin-research/$(date +%Y-%m-%d_%H%M%S)/outliers.json
```

Read `.agents/product-marketing.md` before generating final playbooks to ensure hooks and takeaways align with the target ICP and exclude anti-ICP clichés.
