# Research evidence and internal policy scoring

`social_policy_2026.json` stores the user's v2026.11 weights and targets. They are configurable editorial assumptions, not official weights. The empirical calibration in Coastline Agent OS PR2829 is a separate evidence source. This repository does not contain its private raw exports and must not claim to have reproduced its backtest.

`avs.py` computes signal-weight contributions only. Format multipliers, content bonuses, and penalties are recorded in the configuration for explicit editorial use, not applied to missing or inferred evidence by public-post analyzers. No guarantee of reach or format superiority is implied.

## Input and output

Supply platform (`instagram`, `facebook`, `linkedin`, `tiktok`, `x`, `youtube`), format, and an optional `signals` object. Instagram surface is `connected` or `unconnected` (default). YouTube requires explicit `shorts` or `longform`, never an inferred format from views.

All signals are unit-interval normalized values. For nontrivial signals such as dwell, watch time, reply depth, satisfaction, and tri-modal quality, preserve the normalization definition and actual evidence source alongside the record. A seconds value cannot be silently interpreted as a rate. Public action counts can supply count/exposure ratios only with a valid positive denominator. Instagram/Facebook use reach, LinkedIn impressions, TikTok/X/YouTube views. Unknown and malformed metrics remain null. Zero is valid evidence.

`score` is 0–100 only when all weighted signals and the entire weight allocation are available. `observed_contribution` is the unrescaled sum of available contributions, explicitly partial. `coverage`, `missing`, `sources`, and `unassigned_weight` accompany it. The supplied long-form YouTube weights total 0.90, so its full score is withheld rather than silently assigning the remaining 0.10.

Instagram public shares do not establish DM sends; video plays/followers do not establish non-follower reach. LinkedIn total comments do not establish >12-word substantive comments, and clicks do not establish dwell. YouTube likes/comments do not establish viewer satisfaction. A single post is not an outlier. Records without a known format are ineligible for outlier comparison. Partial-score outliers compare at least three records with the same available signals, profile, exposure denominator, and format. They are descriptive candidates, not causal findings.

YouTube provider zScore remains a separate discovery ordering when owned analytics are unavailable. The output includes the unavailable AVS evidence rather than calling provider discovery a satisfaction score.

## Editorial targets

Use the exact target table in the JSON. Durations and formats are operating preferences, not documented ranking exclusions. Standard targets are IG 68% 3s hold /65% completion/2.5% sends per reach/3% saves per reach; FB65%/58%; TikTok72%/70%; Shorts76% viewed /82% completion. Trial graduation differs intentionally: 24h non-follower hold62% and sends/reach1.5%. Missing trial measurements mean Pending.

## Primary-source limitations

- [Meta Trial Reels](https://about.fb.com/news/2024/12/trial-reels-try-content-non-followers-first-see-what-perfoms-best/) describes metrics after approximately 24h and optional automated sharing based on views within 72h. It does not document this policy's graduation thresholds.
- [LinkedIn engineering clarification](https://www.linkedin.com/posts/timjurka_updates-to-the-linkedin-feed-focusing-on-activity-7449929754679545857-HyFG) says the 360Brew test was shut down. The requested name is retained as a historical/internal label, not a claim about the current deployed ranker or a 69% authority weight.
- [Google Search updates](https://developers.google.com/search/updates) records retirement of FAQ rich results. Valid FAQPage JSON-LD is not a rich-result promise.

## Calibration provenance

Require source platform/account, export timestamp, data window, metric definitions, deduplication identity, paid/trial/collaboration status when known, and missing-field coverage. Keep empirical, synthetic, and policy-derived data separate. Never load packaged `historical_intelligence_report.json` or `calibrated_weights.json` as personal evidence without establishing provenance. The previously packaged 235-post synthetic benchmark is test data, not Anthony's platform history.

Use an explicitly selected engine and an isolated per-run database for calibration. Publish a provenance receipt with input file SHA-256 hashes and the exact engine CLI used. This receipt establishes inputs, not the correctness of an external engine's analysis. No private exports or generated analytics belong in Git.
