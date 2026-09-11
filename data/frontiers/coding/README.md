# Text/coding score × price frontiers

Primary analysis spine for this repo.

## Files

| File | Description |
|------|-------------|
| `arena_coding_elo_price_weekly_panel.csv` | Weekly join of Text/coding score × blended price + `on_frontier` |
| `same_coding_elo_cost_over_time.csv` | Min blended $/MTok to clear an earlier week’s peak score |
| `_summary.json` | Coverage, example frontiers, collapse ratios |
| `arena_price_name_matches.csv` | Name-match audit |
| `arena_unmatched_models.csv` | Arena names without price match |

## Headline (from `_summary.json`)

- Weeks: **2024-04-01 → 2026-08-31** (116)
- Apr 2024 peak ~**1267** @ **$15** → Aug 2026 same published score threshold @ **~$0.12** (~**126×**, promotional snapshot)
- Latest historical frontier includes `glm-5.3-flash` (~1516 @ ~$0.12) with premium peak still ~$10; its September 9 standard blended rate is $0.2375

## Rebuild

```bash
python scripts/build_coding_frontiers.py
python scripts/build_export.py
```

**Do not mix** Text/coding and WebDev scales. Legacy filenames use `elo`; post-January 2024 ratings use Bradley–Terry estimation.
