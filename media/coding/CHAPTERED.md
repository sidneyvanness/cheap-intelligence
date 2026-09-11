# Chaptered frontier evolution movie

Coding-only intelligence–price frontier with freezes at key shifts.

- **Primary:** `frontier_evolution_chaptered.mp4`
- **Last frame:** `frontier_evolution_chaptered_last_frame.png` (end card; date HUD cleared)
- **Ch7 hold still:** `frontier_evolution_chaptered_ch7_hold.png`
- **Duration:** 55.25s @ 12 fps (663 frames)
- **Pacing:** quiet weeks 3/12s each (327 frames); chapter holds variable (ch1=3.0s, ch2=3.0s, ch3=4.5s, ch4=3.5s, ch5=3.0s, ch6=3.0s, ch7=5.0s; 300 frames across 7 beats); end card 36/12s (36 frames)
- **Original (kept):** `frontier_evolution.mp4` (~12s rush)

## Beats (chapter timestamps)

1. **000.0s** (3.0s hold) — `2024-04-01` — GPT-4 era coding frontier · score ~1267 @ $15/MTok
   - highlight `peak`: pointer → GPT-4 Turbo (1106) score 1267 @ $15/MTok
2. **004.2s** (3.0s hold) — `2024-05-13` — GPT-4o · higher score, lower price
   - highlight `peak`: pointer → GPT-4o score 1310 @ $7.5/MTok
3. **011.5s** (4.5s hold) — `2024-09-16` — o1-mini · frontier jump under $2/MTok
   - highlight `peak`: pointer → o1-mini score 1370 @ $1.9/MTok
4. **024.5s** (3.5s hold) — `2025-06-23` — Gemini 2.5 Pro · score ~1492 @ ~$3.44
   - highlight `peak`: pointer → Gemini 2.5 Pro score 1492 @ $3.4/MTok
5. **032.2s** (3.0s hold) — `2025-11-24` — Claude Opus 4.5 thinking · new ceiling @ $10
   - highlight `peak`: pointer → Claude Opus 4.5 thinking score 1515 @ $10/MTok
6. **037.2s** (3.0s hold) — `2026-02-09` — Claude Opus 4.6 thinking · score ~1553
   - highlight `peak`: pointer → Claude Opus 4.6 thinking score 1553 @ $10/MTok
7. **047.2s** (5.0s hold) — `2026-08-31` — Near-frontier score at ~$0.12/MTok · peak still ~$10
   - highlight `max_elo_under_price` ≤$0.25: pointer → GLM-5.3 Flash score 1516 @ $0.12/MTok; faint peak → Claude Opus 4.6 high @ $10

**End card** from 052.2s — Same published Arena score threshold (~1267): ~$15 → ~$0.12 · about 126× cheaper

## Design notes

- Frontier-only polylines, log price axis, time-colored trail
- During holds: older curves dimmed further; large ring + leader-line callout on the highlighted frontier point (model · score · price)
- Quiet weeks: pointer hidden; peak summary in caption HUD only
- End frames: `date_text` / `caption_text` cleared; centered end-card panel in header band (≈0.78–0.90) — no overlap with Aug 2026 HUD
- Optional badge `n/7` during chapter freezes

## Re-run

```bash
python -m venv .venv && source .venv/bin/activate  # or your env
python media/coding/make_chaptered_movie.py
```
