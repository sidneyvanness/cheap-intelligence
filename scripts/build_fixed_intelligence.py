#!/usr/bin/env python3
"""Cost of a fixed amount of coding intelligence over time.

Pick an anchor: the top API-priced model on the Arena Text/coding board in some
past week. Then, for every later week, find the cheapest paid model rated at
least as high as the anchor — even if that takes a newer model.

Two bars are computed:
  head_to_head (primary)  the anchor's score on *that week's* board. Arena
                          ratings drift as the pool changes, so comparing within
                          one snapshot is the like-for-like test; the anchor
                          always clears its own bar while it is still sold.
  frozen (cross-check)    the anchor's score in the anchor week, held constant
                          (same rule as same_coding_elo_cost_over_time.csv).

Run from repo root after build_coding_frontiers.py:
    python scripts/build_fixed_intelligence.py
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import build_frontiers as bf  # noqa: E402

ARENA_PATH = REPO / "data" / "arena" / "coding" / "arena_coding_elo_snapshots_weekly.csv"
PANEL_PATH = REPO / "data" / "frontiers" / "coding" / "arena_coding_elo_price_weekly_panel.csv"
OUT = REPO / "data" / "frontiers" / "coding"

# Each model that took over as the top API-priced model on the coding board,
# ~18–24 months before the 2026-09-07 panel end. (o1-preview and
# gpt-4.5-preview also led the board in this window but have no dated list
# price in our sources, so they cannot anchor a price series.)
ANCHORS = [
    ("2024-09-16", "o1-mini", "o1-mini"),
    ("2025-01-13", "o1-2024-12-17", "o1"),
    ("2025-02-24", "claude-3-7-sonnet-20250219", "Claude 3.7 Sonnet"),
    ("2025-03-31", "chatgpt-4o-latest-20250326", "ChatGPT-4o (Mar 2025)"),
]
PRIMARY_ANCHOR = "o1-2024-12-17"


def cheapest(paid_week: pd.DataFrame, bar: float) -> tuple[float, str | None, int]:
    qual = paid_week[paid_week["elo"] >= bar]
    if qual.empty:
        return np.nan, None, 0
    row = qual.loc[qual["blended_3_1_usd_per_mtok"].idxmin()]
    return float(row["blended_3_1_usd_per_mtok"]), row["model_name_arena"], len(qual)


def main() -> None:
    panel = pd.read_csv(PANEL_PATH)
    paid = panel[panel["blended_3_1_usd_per_mtok"] > 0]
    weeks = sorted(panel["week_start"].unique())

    arena = pd.read_csv(ARENA_PATH)
    arena["snapshot_date"] = pd.to_datetime(arena["snapshot_date"])
    arena["week_start"] = arena["snapshot_date"].map(bf.monday_on_or_before).dt.strftime("%Y-%m-%d")
    arena = arena.sort_values("snapshot_date").groupby(["week_start", "model_name"], as_index=False).last()

    rows, summary = [], []
    for anchor_week, anchor_model, anchor_label in ANCHORS:
        a0 = panel[(panel["week_start"] == anchor_week) & (panel["model_name_arena"] == anchor_model)]
        if a0.empty:
            raise SystemExit(f"anchor not in panel: {anchor_week} {anchor_model}")
        score0 = float(a0["elo"].iloc[0])
        price0 = float(a0["blended_3_1_usd_per_mtok"].iloc[0])
        on_board = arena[arena["model_name"] == anchor_model].set_index("week_start")["elo"]

        bar, low = score0, np.inf
        for w in weeks:
            if w < anchor_week:
                continue
            bar = float(on_board.get(w, bar))  # carry last score if off the board
            g = paid[paid["week_start"] == w]
            price, model, n = cheapest(g, bar)
            f_price, f_model, _ = cheapest(g, score0)
            record = bool(price < low)
            low = min(low, price) if not np.isnan(price) else low
            rows.append(
                {
                    "anchor_week": anchor_week,
                    "anchor_model": anchor_model,
                    "anchor_label": anchor_label,
                    "anchor_score": score0,
                    "anchor_price": price0,
                    "week_start": w,
                    "anchor_score_this_week": bar,
                    "cheapest_price": price,
                    "cheapest_model": model,
                    "n_models_qualifying": n,
                    "is_record_low": record,
                    "frozen_bar_cheapest_price": f_price,
                    "frozen_bar_cheapest_model": f_model,
                }
            )
        last = rows[-1]
        months = (pd.Timestamp(last["week_start"]) - pd.Timestamp(anchor_week)).days / 30.44
        summary.append(
            {
                "anchor_week": anchor_week,
                "anchor_model": anchor_model,
                "anchor_label": anchor_label,
                "anchor_score": round(score0, 1),
                "anchor_price": price0,
                "latest_week": last["week_start"],
                "months_elapsed": round(months, 1),
                "latest_price": last["cheapest_price"],
                "latest_model": last["cheapest_model"],
                "fold_cheaper": round(price0 / last["cheapest_price"], 1),
                "frozen_bar_latest_price": last["frozen_bar_cheapest_price"],
                "frozen_bar_fold_cheaper": round(price0 / last["frozen_bar_cheapest_price"], 1),
                "annualized_decline_factor": round((price0 / last["cheapest_price"]) ** (12 / months), 1),
            }
        )

    pd.DataFrame(rows).to_csv(OUT / "fixed_intelligence_cost.csv", index=False)
    with open(OUT / "fixed_intelligence_summary.json", "w") as f:
        json.dump(
            {
                "generated": date.today().isoformat(),
                "primary_anchor": PRIMARY_ANCHOR,
                "method": "head_to_head bar (anchor's score on each week's board); frozen bar as cross-check",
                "anchors": summary,
            },
            f,
            indent=2,
        )
    print(pd.DataFrame(summary).to_string(index=False))


if __name__ == "__main__":
    main()
