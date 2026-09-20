# Roadmap

Planned extensions beyond the coding intelligence–price spine shipped today.

## Fixed-cost intelligence

Hold a budget fixed (e.g. $1 / MTok blended) and track the best achievable Arena score over time — the dual of “same score threshold, cheaper.”

## Declining cost updates

Refresh the same-score-threshold cost series as new price events and Arena snapshots land. Automate weekly rebuild + a small public changelog. *Started:* `scripts/update_arena_snapshots.py` appends new Arena snapshots; price refresh is still manual.

## Size vs intelligence

Parameter count (and active params for MoE) vs Arena-score frontiers — how much “IQ per billion parameters” moved, and where the local/open frontier sits vs API.

## Richer chaptered movies

Longer illustrated pauses, dual-axis callouts, optional overall-Text track alongside coding, and WebDev tip overlays where Text/coding scores are missing (Astra, etc.).

## Better coverage

- Improve early-2024 price density
- Open-weight models without list API prices (self-host cost models)
- Absolute benchmarks (SWE-bench family) as a parallel quality axis — Arena remains preference-relative
