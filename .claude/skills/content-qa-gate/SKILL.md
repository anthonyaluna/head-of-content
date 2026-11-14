---
name: content-qa-gate
description: |
  Pre-publish EOS Content Team Accountability Gate, Brand ICP/Anti-ICP Filter,
  SoCal Answer Engine Optimization (AEO) Entity Scorer, Video Editor Beat-Sheet QA,
  Trial Reel testing SOP, and Content-to-Clients multi-asset atomizer.
---

# EOS Content Team QA Gate & Brand/AEO Scorer

Solves content execution accountability across three seats before any post, Reel, carousel, or vacancy announcement is published:

1. **Strategist / Copy Seat:**
   - Pre-publish 2026 Algorithm Score >= 72/100 and ICP Fit Score >= 75/100.
   - Zero Anti-ICP flags (filters out duplex/fourplex/cheap-fee language) and zero LinkedIn cliché phrases.
   - Statutory Compliance Check: enforces legal-counsel disclaimer whenever referencing `AB 1482`, `AB 130`, `SB 79`, `SB 707`, CEQA, rent caps, or disclosures.
   - Narrative Coherence Check: bridges community/civic stories directly to fiduciary asset stewardship (*The Reinvestment Test* / *The Protective Perimeter*).
2. **Video Editor Seat:**
   - 0–3s visual & verbal pattern interrupt (beats the Viewed-vs-Swiped-Away gate).
   - Visual shift / B-roll / dynamic zoom reset every 3–5 seconds.
   - Burned-in high-contrast captions + Tri-Modal keyword alignment (spoken + OCR + caption).
   - Zero third-party watermarks + seamless ending-to-opening loop bridge.
3. **Distribution / Community Seat:**
   - Stage new Instagram video hooks as **Trial Reels** to non-followers first; graduate to main followers grid when 24h 3s hold >= 62% and Sends/Reach >= 1.5%.
   - Isolate outbound links to the first comment on LinkedIn, X, and Facebook.
   - Execute 2-hour *Comment-to-Rank* reply SLA and log weekly inbound DM attribution.

## Commands

```bash
# Audit a draft post, Reel script, or hyper-local AEO vacancy post
python3 .claude/skills/content-qa-gate/scripts/run_qa_gate.py qa \
  --platform instagram --format reel --duration 28 \
  --text "Your draft caption or video script..."

# Atomize 1 operational story + metric into LinkedIn + 7-slide IG Carousel + Canonical AEO Webpage + Lead Magnet
python3 .claude/skills/content-qa-gate/scripts/run_qa_gate.py atomize \
  --topic "Deferred Maintenance & Vendor Standards" \
  --story "Field audit example..." \
  --lesson "Same-day triage cut emergency vendor spend by 31%"
```
