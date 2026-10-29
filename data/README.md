# Data schema index

Normalized tables only — no multi-hundred-MB raw Parquet/JSON dumps.

| Path | Role |
|------|------|
| `prices/price_events.csv` | Dated input/output (etc.) price windows |
| `prices/weekly_blended_prices.csv` | Monday panel + 3:1 blend |
| `arena/coding/arena_coding_elo_snapshots_weekly.csv` | Arena Text **coding** Elo, ~weekly |
| `arena/arena_elo_snapshots_weekly.csv` | Arena Text **overall** Elo, ~weekly (~4.4M) |
| `arena/webdev/arena_webdev_latest.csv` | October 28, 2026 WebDev overall board (separate scale) |
| `current/current_model_watch.csv` | Dated current prices + Arena-rating status for the models at or near the frontier (October 28, 2026) |
| `frontiers/coding/arena_coding_elo_price_weekly_panel.csv` | Joined panel + `on_frontier` |
| `frontiers/coding/same_coding_elo_cost_over_time.csv` | Cost of earlier peak Elo later |
| `frontiers/coding/_summary.json` | Machine-readable key stats |
| `frontiers/overall/` | Smaller overall exports (frontier_only + story metrics) |
| `export/coding/` | Chart-ready CSVs + xlsx |
| `model_name_crosswalk.csv` | Arena ↔ catalog name helpers |
| `arena/display_name_map.csv` | Arena display name → legacy slug (Text boards switched on 2026-10-20) |
| `model_sizes.csv` | Optional size metadata for future size-vs-IQ work |

## Upstream raw sources (not shipped)

- HF dataset: [`lmarena-ai/leaderboard-dataset`](https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset) (Parquet splits)
- RoninForge series JSON: https://roninforge.org/data/ai-price-index/
- Model Price Watch JSON APIs

Rebuild coding spine: `python scripts/build_coding_frontiers.py` then `python scripts/build_export.py`.
