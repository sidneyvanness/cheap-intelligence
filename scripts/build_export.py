#!/usr/bin/env python3
"""Slim export pack for the Arena Text/coding score × price story."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
FRONT = REPO / "data" / "frontiers" / "coding"
OUT = REPO / "data" / "export" / "coding"
OUT.mkdir(parents=True, exist_ok=True)
TODAY = date.today().isoformat()


def sheet_with_meta(writer, df: pd.DataFrame, name: str):
    # Match overall export workbook style: title + shape + blank + header + data
    start = 3
    df.to_excel(writer, sheet_name=name, index=False, startrow=start)
    ws = writer.sheets[name]
    ws.cell(1, 1, name)
    ws.cell(2, 1, f"rows={len(df)} cols={len(df.columns)}")


def main():
    panel = pd.read_csv(FRONT / "arena_coding_elo_price_weekly_panel.csv")
    same = pd.read_csv(FRONT / "same_coding_elo_cost_over_time.csv")
    summary = json.loads((FRONT / "_summary.json").read_text())

    frontier = panel[panel["on_frontier"]].copy()
    frontier_only = frontier[
        ["week_start", "model_name_arena", "provider", "elo", "blended_3_1_usd_per_mtok"]
    ].sort_values(["week_start", "elo"], ascending=[True, False])

    metrics_rows = []
    for week, g in frontier.groupby("week_start", sort=True):
        peak_i = g["elo"].idxmax()
        peak = g.loc[peak_i]
        metrics_rows.append(
            {
                "week_start": week,
                "frontier_n": int(len(g)),
                "max_elo": float(g["elo"].max()),
                "min_blended_price": float(g["blended_3_1_usd_per_mtok"].min()),
                "peak_model": peak["model_name_arena"],
                "peak_elo": float(peak["elo"]),
                "peak_model_price": float(peak["blended_3_1_usd_per_mtok"]),
            }
        )
    metrics = pd.DataFrame(metrics_rows)

    # Write CSVs
    f0 = OUT / "00_arena_coding_elo_price_weekly_panel_full.csv"
    f1 = OUT / "01_arena_coding_elo_price_frontier_only.csv"
    f2 = OUT / "02_weekly_frontier_story_metrics.csv"
    f3 = OUT / "03_same_coding_elo_cost_over_time.csv"
    panel.to_csv(f0, index=False)
    frontier_only.to_csv(f1, index=False)
    metrics.to_csv(f2, index=False)
    same.to_csv(f3, index=False)

    xlsx = OUT / "pareto_coding_frontier_story_data.xlsx"
    with pd.ExcelWriter(xlsx, engine="openpyxl") as writer:
        sheet_with_meta(writer, frontier_only, "frontier_only")
        sheet_with_meta(writer, metrics, "weekly_story_metrics")
        sheet_with_meta(writer, same, "same_elo_cost")
        notes = pd.DataFrame(
            {
                "note": [
                    f"Pareto coding frontier export — {TODAY}",
                    "",
                    "Primary story: Arena Text/coding score vs blended $/MTok over time",
                    "NOT overall Text or WebDev — coding category only",
                    f"Panel weeks: {summary['week_start_min']} → {summary['week_start_max']} ({summary['weeks_covered']} weeks)",
                    f"Match rate: {summary['matched_models']}/{summary['arena_models_total']} ({100*summary['match_rate']:.1f}%)",
                    "GPT-6 Astra Max rated on Text/coding from week 2026-09-07; DeepSeek V4.1 Flash is rated on WebDev only",
                    "Viz: frontier polylines by week; label peak + cheap anchors; LOCF/dash ≤8wk gaps on price collapse",
                ]
            }
        )
        notes.to_excel(writer, sheet_name="NOTES", index=False, header=False)

    readme = f"""# Coding Pareto frontier export pack ({TODAY})

Story-ready tables for Arena Text **coding** score × blended API price (parallel to root `export/`). Legacy filenames retain `elo`; post-January 2024 ratings use Bradley–Terry estimation.

## Start here
1. `01_arena_coding_elo_price_frontier_only.csv` — Pareto frontier points by week
2. `02_weekly_frontier_story_metrics.csv` — weekly maximum score / cheap tip / peak model
3. `03_same_coding_elo_cost_over_time.csv` — later cost to clear an earlier week's peak score
4. `00_*_full.csv` — full matched panel with `on_frontier`
5. `pareto_coding_frontier_story_data.xlsx` — workbook (frontier_only / metrics / same_elo_cost / NOTES)

## Axes
- Quality: Chatbot Arena Text **coding** category score (not overall Text or WebDev)
- Price: blended USD / 1M tokens = (3×input + output)/4

## Coverage
- Weeks: **{summary['week_start_min']} → {summary['week_start_max']}** ({summary['weeks_covered']} weeks)
- Match rate: **{summary['matched_models']}/{summary['arena_models_total']}** ({100*summary['match_rate']:.1f}%)
- Frontier rows: **{summary['frontier_rows']}**

## Caveats
- GPT-6 Astra Max has a Text/coding score from the 2026-09-11 snapshot (week 2026-09-07)
- DeepSeek V4.1 Flash is rated on WebDev only; no Text/coding score is invented
"""
    # The shipped README is hand-curated; only scaffold one if it is missing.
    if not (OUT / "README.md").exists():
        (OUT / "README.md").write_text(readme)
    print(
        json.dumps(
            {
                "frontier_rows": len(frontier_only),
                "weeks": len(metrics),
                "same_rows": len(same),
                "files": [p.name for p in (f0, f1, f2, f3, xlsx)],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
