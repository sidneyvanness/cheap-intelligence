#!/usr/bin/env python3
"""Append new LMArena snapshots to the shipped weekly CSVs.

Reads the Hugging Face `lmarena-ai/leaderboard-dataset` Parquet dumps and:
  - appends Text `coding` / `overall` snapshots newer than the last shipped date
  - rewrites the WebDev `overall` board with the latest published snapshot

Existing rows are never rewritten. Run from repo root:

    python scripts/update_arena_snapshots.py            # download from HF
    python scripts/update_arena_snapshots.py --text text.parquet --webdev webdev.parquet
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
HF_URL = "https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset"
PARQUET_URL = HF_URL + "/resolve/main/{subset}/full-00000-of-00001.parquet"

TEXT_TARGETS = {
    "coding": ROOT / "data" / "arena" / "coding" / "arena_coding_elo_snapshots_weekly.csv",
    "overall": ROOT / "data" / "arena" / "arena_elo_snapshots_weekly.csv",
}
WEBDEV_PATH = ROOT / "data" / "arena" / "webdev" / "arena_webdev_latest.csv"
# Text boards switched from slugs to display names on 2026-10-20; map back so
# per-model series, aliases and anchors stay continuous.
DISPLAY_MAP_PATH = ROOT / "data" / "arena" / "display_name_map.csv"


def append_text(text: pd.DataFrame, category: str, path: Path) -> None:
    shipped = pd.read_csv(path)
    last = shipped["snapshot_date"].max()
    new = text[(text["category"] == category) & (text["leaderboard_publish_date"] > last)]
    if new.empty:
        print(f"{category}: no snapshots after {last}")
        return
    names = pd.read_csv(DISPLAY_MAP_PATH)
    new = new.assign(
        model_name=new["model_name"].replace(dict(zip(names["display_name"], names["legacy_slug"])))
    )
    unknown = sorted(set(new["model_name"]) - set(shipped["model_name"]))
    if unknown:
        print(f"{category}: names not seen before (new models or missing map rows): {unknown}")
    new = new.sort_values(
        ["leaderboard_publish_date", "rank", "rating"], ascending=[True, True, False]
    )
    add = pd.DataFrame(
        {
            "snapshot_date": new["leaderboard_publish_date"],
            "model_name": new["model_name"],
            "elo": new["rating"],
            "votes": new["vote_count"].astype(float),
            "rank": new["rank"].astype(float),
            "source": f"{HF_URL} (subset=text, category={category}, split=full)",
        }
    )
    # Append in place: re-serializing shipped rows perturbs float last digits.
    add[list(shipped.columns)].to_csv(path, mode="a", header=False, index=False)
    dates = ", ".join(sorted(add["snapshot_date"].unique()))
    print(f"{category}: appended {len(add)} rows ({dates})")


def refresh_webdev(webdev: pd.DataFrame) -> None:
    # Some publish dates only carry side categories (e.g. image_to_webdev).
    overall = webdev[webdev["category"] == "overall"]
    latest = overall["leaderboard_publish_date"].max()
    shipped = pd.read_csv(WEBDEV_PATH)["leaderboard_publish_date"].max()
    if latest <= shipped:
        print(f"webdev: no overall board after {shipped}")
        return
    board = overall[overall["leaderboard_publish_date"] == latest].sort_values("rank")
    board.to_csv(WEBDEV_PATH, index=False, float_format="%.6f")
    print(f"webdev: wrote {len(board)} rows ({latest})")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--text", help="local text Parquet (default: download from HF)")
    ap.add_argument("--webdev", help="local webdev Parquet (default: download from HF)")
    args = ap.parse_args()

    text = pd.read_parquet(args.text or PARQUET_URL.format(subset="text"))
    for category, path in TEXT_TARGETS.items():
        append_text(text, category, path)
    refresh_webdev(pd.read_parquet(args.webdev or PARQUET_URL.format(subset="webdev")))


if __name__ == "__main__":
    main()
