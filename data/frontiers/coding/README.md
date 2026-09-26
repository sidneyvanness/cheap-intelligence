# Text/coding score × price frontiers

Primary analysis spine for this repo.

## Files

| File | Description |
|------|-------------|
| `arena_coding_elo_price_weekly_panel.csv` | Weekly join of Text/coding score × blended price + `on_frontier` |
| `same_coding_elo_cost_over_time.csv` | Min blended $/MTok to clear an earlier week’s peak score |
| `_summary.json` | Coverage, example frontiers, collapse ratios |
| `fixed_intelligence_cost.csv` | Cheapest model rated at least as high as a past board leader, week by week (head-to-head bar + frozen-bar cross-check) |
| `fixed_intelligence_summary.json` | Per-anchor start/latest price and fold decline |
| `arena_price_name_matches.csv` | Name-match audit |
| `arena_unmatched_models.csv` | Arena names without price match |

## Headline (from `_summary.json`)

- Weeks: **2024-04-01 → 2026-09-21** (118; no Arena snapshot was published in the week of 2026-09-14)
- Apr 2024 peak ~**1267** @ **$15** → Aug 31, 2026 same published score threshold @ **~$0.12** (~**126×**, promotional snapshot) → Sep 21, 2026 @ **$0.1275** (~**118×**, `gpt-oss-20b`, standard list prices)
- Latest frontier (week 2026-09-21): `claude-opus-5.5-high` ~1545 @ $8 → `muse-spark-1.3-max` ~1516 @ $2 → `gemini-3.8-flash-high` ~1512 @ $1.50 → `deepseek-v4.1-flash-max` ~1511 @ $0.525 → `glm-5.3-flash` ~1506 @ $0.2375 → `gpt-6-luna-max` ~1448 @ $0.20 → `qwen3.5-flash` ~1412 @ $0.175
- Weekly peak rose from ~1535 (`claude-opus-4-6-high`, $10) to ~1545 (`claude-opus-5.5-high`, $8, 573 votes) — higher and cheaper
- Fixed intelligence: o1-level coding (Jan 2025, $26.25) → **$0.175** (~**150×** in 20 months); see `fixed_intelligence_summary.json`

## Rebuild

```bash
python scripts/update_arena_snapshots.py   # optional: append new HF snapshots (needs pyarrow)
python scripts/build_coding_frontiers.py
python scripts/build_fixed_intelligence.py
python scripts/build_export.py
```

**Do not mix** Text/coding and WebDev scales. Legacy filenames use `elo`; post-January 2024 ratings use Bradley–Terry estimation.
