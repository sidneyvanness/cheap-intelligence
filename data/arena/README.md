# Arena rating snapshots (weekly)

## Coding (primary)

`coding/arena_coding_elo_snapshots_weekly.csv` — from HF [`lmarena-ai/leaderboard-dataset`](https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset), subset `text`, category **`coding`**.

Span in source dump: **2024-04-03 → 2026-09-02** (weekly thin). This is a **coding-category** human-preference rating — not interchangeable with overall Text or WebDev ratings. Post-January 2024 ratings use Bradley–Terry estimation; `elo` survives in legacy filenames and labels.

The raw Text series stays primary because the available style-controlled coding history begins **2024-09-15**, after the April 2024 anchor. That makes style control useful for later cross-checks, but unsuitable for this full longitudinal window.

## Overall (optional)

`arena_elo_snapshots_weekly.csv` (~4.4 MB) — Text **overall** category, weekly thin. Full raw Parquet lives on Hugging Face; we ship the weekly CSV only.

## WebDev (current tip)

`webdev/arena_webdev_latest.csv` — normalized `overall` rows from the **2026-09-08** WebDev leaderboard. This is a separate board and scale; it includes GPT-6 Astra Max but must not be spliced onto the Text/coding time series.

## Note on missing models

GPT-6 Astra Max has **no Text/coding rating** in the latest dump; DeepSeek V4.1 Flash has no independent Arena rating on either included board as of **2026-09-10**. Do not invent scores. See `data/current/current_model_watch.csv` for explicit rated/unrated status.
