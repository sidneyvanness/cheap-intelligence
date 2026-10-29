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

- Weeks: **2024-04-01 → 2026-10-26** (123; no Arena snapshot was published in the week of 2026-09-14)
- Apr 2024 peak ~**1267** @ **$15** → Aug 31, 2026 same published score threshold @ **~$0.12** (~**126×**, promotional snapshot) → Oct 26, 2026 @ **$0.1275** (~**118×**, `gpt-oss-20b`, standard list prices)
- Latest frontier (week 2026-10-26): `claude-opus-5.5-high` ~1547 @ $8 → `gemini-4-argon-high` ~1538 @ $4 (introductory) → `muse-spark-1.3-max` ~1509 @ $2 → `gemini-3.8-flash-high` ~1509 @ $1.50 → `glm-5.3-flash` ~1509 @ $0.2375 → `Claude Haiku 5.5 (High)` ~1454 @ $0.20 → `step-3.5-flash` ~1436 @ $0.15 → `glm-4.7-flash` ~1383 @ $0 (free)
- Near-peak price halved: Gemini 4 Argon sits 9 points below Opus 5.5 at half the price. Gemini 4 Carbon (~1569, #1) has no list price yet and is not in the panel
- Fixed intelligence: o1-level coding (Jan 2025, $26.25) → **$0.15** (~**175×** in 21 months, `step-3.5-flash`); see `fixed_intelligence_summary.json`

## Rebuild

```bash
python scripts/update_arena_snapshots.py   # optional: append new HF snapshots (needs pyarrow)
python scripts/build_coding_frontiers.py
python scripts/build_fixed_intelligence.py
python scripts/build_export.py
```

**Do not mix** Text/coding and WebDev scales. Legacy filenames use `elo`; post-January 2024 ratings use Bradley–Terry estimation.
