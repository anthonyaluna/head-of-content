---
name: content-qa-gate
description: Evaluate Coastline authority drafts against the brand ICP, local AEO, legal-topic disclaimer, and three-seat editorial policy. Use for prepublication review, Trial Reel evidence checks, and five-asset operational story bundles.
---

# Content QA and atomization

Read `.agents/product-marketing.md` for the complete v2.1 policy and `.claude/lib/SCORING.md` for evidence limits. Use the canonical Coastline engine, explicitly selected with `--canonical-root` or `COASTLINE_AGENT_OS_ROOT`. Do not silently discover the old Social Intelligence Engine or load synthetic calibration.

```bash
python .claude/skills/content-qa-gate/scripts/run_qa_gate.py qa \
  --input draft-and-evidence.json --canonical-root /path/to/coastline-codex-agent-os
python .claude/skills/content-qa-gate/scripts/run_qa_gate.py atomize \
  --input verified-story.json --canonical-root /path/to/coastline-codex-agent-os
```

Pass source-supported `content`, `platform`, `format_name`, optional editorial `algo_score`, `editor_evidence`, `distribution_evidence`, `trial_metrics`, `authority_post`, `local_post`, and `entities` using the canonical CLI's schema. Inspect its help and schema if an input is rejected. Do not manufacture video runtime, slide count, seat approval, future response compliance, or audience retention. Unknown evidence stays Pending.

Apply strategist >=72, ICP >=75, and the supplied composite thresholds. A high composite never overrides hard brand flags or an unreviewed required seat. Trial graduation requires actual matching-window non-follower hold and sends/reach. Public shares are not DM sends. Availability and measurement must be verified separately from account eligibility.

For atomization, provide one operational story and one supported metric or lesson. Produce the requested LinkedIn post, seven-slide carousel, canonical webpage, owner audit, and five practitioner prompts. Missing claims remain unresolved in every derivative. Review the returned assets for length, source accuracy, originality, and audience fit. Valid Article/FAQPage JSON-LD does not promise indexing or FAQ rich results. No command authorizes publication or sends messages.
