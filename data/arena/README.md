# Arena rating snapshots (weekly)

## Coding (primary)

`coding/arena_coding_elo_snapshots_weekly.csv` — from HF [`lmarena-ai/leaderboard-dataset`](https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset), subset `text`, category **`coding`**.

Span in source dump: **2024-04-03 → 2026-10-28** (weekly thin). This is a **coding-category** human-preference rating — not interchangeable with overall Text or WebDev ratings. Post-January 2024 ratings use Bradley–Terry estimation; `elo` survives in legacy filenames and labels.

The raw Text series stays primary because the available style-controlled coding history begins **2024-09-15**, after the April 2024 anchor. That makes style control useful for later cross-checks, but unsuitable for this full longitudinal window.

## Overall (optional)

`arena_elo_snapshots_weekly.csv` (~4.4 MB) — Text **overall** category, weekly thin. Full raw Parquet lives on Hugging Face; we ship the weekly CSV only.

## WebDev (current tip)

`webdev/arena_webdev_latest.csv` — normalized `overall` rows from the **2026-10-28** WebDev leaderboard, in LMArena's display names. This is a separate board and scale; it includes GPT-6 Astra Max but must not be spliced onto the Text/coding time series.

## Note on missing models

GPT-6 Astra Max gained a Text/coding rating on **2026-09-11**; DeepSeek V4.1 Flash (`deepseek-v4.1-flash-max`), Claude Opus 5.5, GPT-6 Sol/Luna, Grok 4.7 and MiMo v2.6 on **2026-09-25**. Gemini 4 Argon, Claude Sonnet 5.5, GPT-6.1 Sol and Muse Wonder followed between **2026-09-30** and **2026-10-15**, and Claude Haiku 5.5 and Gemini 4 Carbon by **2026-10-28**. MiMo v2.6 and Gemini 4 Carbon are rated but have no list price in our sources, so they stay off the price axis. DeepSeek V4.1 Flash 1017 has a WebDev rating but no Text/coding rating yet. Do not invent scores.

## Display names (from 2026-10-20)

LMArena's Text boards switched from slugs to display names on **2026-10-20** (the 2026-10-15 board was partly switched). `display_name_map.csv` maps each display name back to its legacy slug: exact matches on version-preserving name tokens, plus hand-checked pairs (`method = manual`). `scripts/update_arena_snapshots.py` applies it on append and prints any name it has not seen before, so a new model and a missing map row both show up at ingest. Models first published under a display name (Claude Haiku 5.5, Gemini 4 Carbon, Step 5 Preview, Beam 1.0) keep it. See `data/current/current_model_watch.csv` for explicit rated/unrated status.
