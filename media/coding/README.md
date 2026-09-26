# Story visuals — coding score × price frontier

Editorial charts for Arena Text **coding** score. Legacy files and some labels use “Elo,” though post-January 2024 ratings use Bradley–Terry estimation. **Frontier polylines only** — no scatter-cloud spaghetti.

## Deliverables

| File | Story beat |
|------|------------|
| `frontier_evolution.png` (+ `.svg`) | Many weekly frontiers overlaid, colored by date |
| `frontier_evolution.mp4` | **Every week** (coding panel frames); older curves stay as a muted color trail |
| `peak_capability.png` | Raw peak score (faint) + **running-max envelope** (bold ceiling) |
| `price_collapse.png` | Same-score-threshold cost; gaps ≤8 wks filled (dashed = imputed) |
| `migration.png` | **Hero:** early vs latest frontier, up-left migration |
| `storyboard.png` | One-pager: migration + peak ceiling + price collapse |

## Design notes (v2)

- **Typography:** Inter / Inter Display (bundled under `fonts/`); warm paper background `#F7F5F2`.
- **Color:** continuous time colormap (muted stone → indigo → vivid rose). Older frontiers sit quiet; latest is vivid and thicker.
- **Animation trail:** history **accumulates** — prior weekly curves remain on screen in muted time-colors; only the newest week is vivid.
- **Labels:** sparse callouts with leader lines + paper-backed text in empty margins (no polyline collisions; Opus 5 peak sits above the curve).
- **Peak chart:** raw weekly maximum score as ghost; bold line is the monotonic **running maximum** (“capability frontier ceiling”). Mid-2025 Arena wiggles annotated as relative rating noise.
- **Price collapse:** NaN weeks (no qualifying model) filled with LOCF / log-linear interp when the gap is ≤8 weeks; imputed segments drawn **dashed**.
- **Omitted models:** MiMo v2.6 Pro / Flash (Xiaomi) are rated but have no list price in our sources, so they are excluded from the price axis. We do **not** invent or merge scores.
- **Encoding:** log price (x), Text/coding score (y). Free ($0) models are explicit and floored at `$0.05` only for log display.
- **Retina:** PNGs at 220 dpi.

## Rebuild

```bash
python -m venv .venv && source .venv/bin/activate  # or your env
python scripts/viz/make_story_viz.py
python scripts/viz/make_story_viz.py --skip-anim   # static only
python scripts/viz/make_story_viz.py --every-n 3 --fps 10
```

Data inputs: `export/coding/01_*.csv`, `02_*.csv`, `03_*.csv`.
