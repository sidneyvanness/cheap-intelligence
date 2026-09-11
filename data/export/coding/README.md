# Coding export pack

Chart-ready tables for the Text/coding score × price story. Legacy filenames retain `elo`; post-January 2024 ratings use Bradley–Terry estimation.

| File | Use |
|------|-----|
| `01_arena_coding_elo_price_frontier_only.csv` | Frontier polylines |
| `02_weekly_frontier_story_metrics.csv` | Weekly peak / tip metrics |
| `03_same_coding_elo_cost_over_time.csv` | Price-collapse series |
| `00_*_full.csv` | Full matched panel |
| `pareto_coding_frontier_story_data.xlsx` | Workbook |

Rebuild: `python scripts/build_export.py`
