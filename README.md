# cheap-intelligence

**Coding intelligence got ~126× cheaper in 29 months.**

From April 2024 to August 2026, the Chatbot Arena *coding* score–price Pareto frontier marched up and left: peak quality rose, and the cost of clearing yesterday’s published score collapsed. The April 2024 coding peak (~**1267** at ~**$15**/MTok blended, GPT-4 Turbo `1106`) was cleared on August 31, 2026 by `glm-5.3-flash` at a promotional **$0.11875**/MTok — roughly **126×** lower list price for the old score threshold. At GLM-5.3 Flash's standard rate effective September 9, the live comparison is still about **63×**. This repo packages the weekly panels, methods, caveats, exports, and a chaptered movie of that migration.

“Cost of intelligence” is deliberately provocative shorthand, not a claim that Arena is an absolute intelligence meter. The exact factor depends on the benchmark slice, dates, price mix, match coverage, and pricing schedule. The claim is narrower: over 29 months, the list-price cost of exceeding one published human-preference score threshold fell by roughly two orders of magnitude.

## What a Pareto frontier means here

Each week we plot matched models in **(blended $/MTok, Arena Text/coding score)** space. A model is on the **Pareto frontier** if no other matched model that week is both **cheaper (or equal) and higher-scoring (or equal)** with at least one strict inequality — i.e. maximum published score for a given price, and minimum price for a given score. Dominated interior points are ignored in the story charts; only the frontier polyline matters.

**Blended price** = `(3 × input + 1 × output) / 4` USD per 1M tokens (3:1 input-heavy mix).

## Key finding (coding spine)

| Anchor | Published Text/coding score | Cheapest blended $/MTok clearing that score | Models (illustrative) |
|--------|-----------------|--------------------------------------|------------------------|
| **2024-04-01** | ~**1267** | **$15.00** | `gpt-4-1106-preview` |
| **2026-08-31 snapshot** | clears the old bar | **$0.11875** (~**126×**) | `glm-5.3-flash`, launch promotion |
| **2026-09-10 current watch** | clears the old bar | **$0.23750** (~**63×**) | `glm-5.3-flash`, standard rate |

Peak *ceiling* also rose: ~1267 → ~1535 weekly maximum score (`claude-opus-4-6-high`), with running-max envelope ~1553. See `data/frontiers/coding/_summary.json` and `media/coding/`.

> **Watch:** [`media/coding/frontier_evolution_chaptered.mp4`](media/coding/frontier_evolution_chaptered.mp4) — seven chapter freezes from the GPT-4-era stub to a near-frontier score at ~$0.12.

## Current frontier watch — September 10, 2026

These are not forced onto one axis. Text/coding and WebDev are separate Arena boards, and a newly released model without an independent rating remains unrated.

| Model | Independent capability signal | 3:1 blended list price | Status |
|-------|-------------------------------|------------------------|--------|
| **GLM-5.3 Flash** | Text/coding **1516.2** (Sep 2); WebDev **1604.5** (Sep 8) | **$0.2375** standard | Rated on both boards; launch promotion ended Sep 9 |
| **GPT-6 Astra Max** | WebDev **1796.2**, rank 1 (Sep 8) | **$20.00** | No Text/coding score in the latest published snapshot |
| **DeepSeek V4.1 Flash** | No independent Arena rating yet | **$0.525** peak / **$0.2625** off-peak | Released Sep 10; capability evidence is vendor-reported for now |

The auditable snapshot is [`data/current/current_model_watch.csv`](data/current/current_model_watch.csv). The normalized September 8 WebDev board is [`data/arena/webdev/arena_webdev_latest.csv`](data/arena/webdev/arena_webdev_latest.csv).

## Data sources

1. **LMArena / Chatbot Arena leaderboard** — Hugging Face [`lmarena-ai/leaderboard-dataset`](https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset)
   - Primary spine: subset `text`, category **`coding`**
   - Raw Text is used for longitudinal continuity: the available style-controlled coding series begins in September 2024 and would remove the April anchor
   - Optional: `text` / overall (weekly CSV included; full raw Parquet not shipped)
   - Secondary tip chart: Code Arena WebDev (`webdev` / `overall`) when a Text/coding score is missing
2. **Dated API prices**
   - **RoninForge AI Price Index** — https://roninforge.org/ai-price-index/ / [open data](https://roninforge.org/data/ai-price-index/) (**CC BY 4.0**)
   - **Model Price Watch** — https://modelpricewatch.com (supplement for models not in RoninForge)
3. **Blended price** = `(3*input + output)/4` as above
4. Optional secondary: Code Arena tip visuals for current models without a Text/coding score

Normalized CSVs live under `data/`. Huge raw JSON/Parquet dumps are **not** included; rebuild from upstream if you need them.

## Methods

- **Weekly Mondays.** Arena snapshots and prices are aligned to ISO week starts (Monday). Panel coverage for the coding × price join: **2024-04-01 → 2026-08-31** (116 weeks).
- **Name matching.** Arena display names ↔ price catalog IDs via normalization + a checked crosswalk (`data/model_name_crosswalk.csv`, `data/frontiers/arena_price_name_matches.csv`). No invented scores or prices — unmatched models are listed, not guessed.
- **Score terminology.** The source calls the published value an Arena rating/score. Post-January 2024 leaderboard ratings use Bradley–Terry estimation rather than classic Elo; legacy filenames and some rendered labels still say “Elo.”
- **Pareto.** Per week, `on_frontier` marks non-dominated points in published score ↑ / blended price ↓.
- **Same-score cost.** For each early anchor week’s maximum published score, track the cheapest later blended price among models that meet or exceed that threshold.
- **Free and promotional prices.** $0 rows remain visible in the frontier data and are floored at $0.05 only for log-axis display. The headline same-score calculation requires a positive paid price. Promotions are dated snapshots, not silently carried forward as current rates.
- **Chaptered movie.** Quiet weeks advance quickly; seven shape-shift weeks hold with callouts (GPT-4 → GPT-4o → o1-mini → Gemini 2.5 Pro → Opus 4.5/4.6 → Aug 2026 cheap tip). See `scripts/viz/make_chaptered_movie.py`.

## Media

| File | Description |
|------|-------------|
| `media/coding/frontier_evolution_chaptered.mp4` | Primary chaptered movie (~55s) |
| `media/coding/frontier_evolution_chaptered_last_frame.png` | End card still |
| `media/coding/frontier_evolution_chaptered_ch7_hold.png` | Chapter 7 hold (cheap tip) |
| `media/coding/migration.png` | Early vs latest frontier |
| `media/coding/price_collapse.png` | Same-score-threshold cost over time |
| `media/coding/storyboard.png` | One-pager |
| `media/coding/code_arena_tip.png` | Code Arena (WebDev) tip — includes Astra-scale board |

## Limitations (please read)

1. **Arena score is a relative human-preference ranking**, not a fixed absolute IQ score. Pairwise battles, estimation methods, sampling, and leaderboard composition change over time; small week-to-week dips are often noise, not capability loss. It is **not** a frozen exam and **≠ SWE-bench** (or other absolute coding benchmarks).
2. **Price coverage is sparse early** (especially 2023–early 2024). Open / self-hosted models **without list API prices are excluded** from the price axis.
3. **GPT-6 Astra and DeepSeek V4.1 Flash lack Text-`coding` scores** in the latest published snapshot. Astra is shown separately on the September 8 WebDev board. DeepSeek V4.1 Flash, released September 10, remains explicitly unrated until an independent Arena result appears.
4. Match rate is incomplete (~47% of coding Arena names matched to prices overall; lower in 2024). Results describe the **matched API-priced subset**.
5. List prices ≠ discounted enterprise rates; blend assumes a 3:1 input:output mix. Free tiers and promotions are real but unstable, so they are labeled explicitly rather than presented as ordinary durable prices.

## Reproduce

```bash
cd cheap-intelligence
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Rebuild coding frontiers from weekly CSVs already in data/
python scripts/build_coding_frontiers.py
python scripts/build_export.py

# Story statics + (optional) full animation; needs ffmpeg for mp4
python scripts/viz/make_story_viz.py --skip-anim
python scripts/viz/make_chaptered_movie.py
```

Pre-built tables and media are committed so you can inspect findings without re-running. FFmpeg is required only to regenerate MP4s.

## Roadmap

See [`ROADMAP.md`](ROADMAP.md): fixed-cost intelligence, declining-cost update series, size vs intelligence, richer illustrated pauses.

## Attribution & licenses

- **Code** (scripts, notebooks scaffolding): [MIT](LICENSE) © 2026 Sidney VanNess
- **Third-party data:** [`DATA_ATTRIBUTION.md`](DATA_ATTRIBUTION.md) — LMArena and RoninForge CC BY 4.0; Model Price Watch per upstream terms

## Layout

```
data/prices/          dated events + weekly blended prices
data/arena/           weekly Arena scores (coding + overall) + latest WebDev board
data/current/         dated cross-board current-model watch
data/frontiers/       Pareto panels + same-score-threshold cost series
data/export/coding/   xlsx + frontier_only CSVs for charts
scripts/              rebuild + viz
media/coding/         chaptered mp4 + key statics
```
