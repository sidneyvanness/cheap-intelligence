#!/usr/bin/env python3
"""Arena Text *coding* score × blended API prices — weekly Pareto frontiers.

Reuses name-matching from ../build_frontiers.py (and existing
arena_price_name_matches.csv where the Arena name already matched).
Does NOT invent or merge ratings for models without a published Text/coding score.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"
OUT = DATA / "frontiers" / "coding"
OUT.mkdir(parents=True, exist_ok=True)

# Import overall frontier helpers (same scripts/ directory)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_frontiers as bf  # noqa: E402

ARENA_PATH = DATA / "arena" / "coding" / "arena_coding_elo_snapshots_weekly.csv"
PRICES_PATH = DATA / "prices" / "weekly_blended_prices.csv"
XWALK_PATH = DATA / "model_name_crosswalk.csv"
SIZES_PATH = DATA / "model_sizes.csv"
EXISTING_MATCHES = DATA / "frontiers" / "arena_price_name_matches.csv"
TODAY = date.today().isoformat()


def main():
    arena = pd.read_csv(ARENA_PATH)
    prices = pd.read_csv(PRICES_PATH)
    xwalk = pd.read_csv(XWALK_PATH)
    sizes = pd.read_csv(SIZES_PATH)

    arena["snapshot_date"] = pd.to_datetime(arena["snapshot_date"])
    prices["week_start"] = pd.to_datetime(prices["week_start"])

    by_id, id_index, can_index, core_index = bf.build_price_lookups(prices)

    # Prefer existing overall matches for shared Arena names; re-resolve misses
    existing = pd.read_csv(EXISTING_MATCHES) if EXISTING_MATCHES.exists() else pd.DataFrame()
    existing_map = {}
    if len(existing):
        for _, r in existing.iterrows():
            existing_map[r["model_name_arena"]] = r.to_dict()

    arena_models = sorted(arena["model_name"].unique())
    match_rows, unmatched = [], []
    reused = 0
    for name in arena_models:
        if name in existing_map:
            # verify price model_id still resolves
            mid = existing_map[name]["model_id_price"]
            rec = bf.resolve_model_id(mid, by_id, id_index, core_index)
            if rec is not None:
                m = {
                    "model_name_arena": name,
                    "model_id_price": rec["model_id"],
                    "provider": rec["provider"],
                    "model_name_canonical": rec["model_name_canonical"],
                    "match_method": existing_map[name].get("match_method", "reused_overall"),
                    "match_confidence": float(existing_map[name].get("match_confidence", 0.9)),
                    "normalized_arena": existing_map[name].get(
                        "normalized_arena", bf.normalize_name(name)
                    ),
                    "matched_key": existing_map[name].get(
                        "matched_key", bf.normalize_name(mid)
                    ),
                }
                # stamp reuse
                if not str(m["match_method"]).startswith("reused_"):
                    m["match_method"] = f"reused_overall:{m['match_method']}"
                match_rows.append(m)
                reused += 1
                continue
        m = bf.pick_match(name, by_id, id_index, can_index, core_index)
        if m:
            match_rows.append(m)
        else:
            unmatched.append(name)

    matches = pd.DataFrame(match_rows)
    freq = arena.groupby("model_name").size().rename("n_snapshots")
    unmatched_freq = (
        pd.DataFrame({"model_name_arena": unmatched})
        .merge(freq, left_on="model_name_arena", right_index=True, how="left")
        .sort_values("n_snapshots", ascending=False)
    )
    print(
        f"Matched {len(matches)} / {len(arena_models)} "
        f"({100 * len(matches) / len(arena_models):.1f}%); reused_overall={reused}"
    )
    print("Top unmatched:")
    print(unmatched_freq.head(20).to_string(index=False))

    matches_out = matches[
        [
            "model_name_arena",
            "model_id_price",
            "provider",
            "model_name_canonical",
            "match_method",
            "match_confidence",
            "normalized_arena",
            "matched_key",
        ]
    ].copy()
    matches_out.to_csv(OUT / "arena_price_name_matches.csv", index=False)
    unmatched_freq.to_csv(OUT / "arena_unmatched_models.csv", index=False)

    arena = arena.copy()
    arena["week_start"] = arena["snapshot_date"].map(bf.monday_on_or_before)
    arena = arena.sort_values(["week_start", "snapshot_date"])
    arena = arena.groupby(["week_start", "model_name"], as_index=False).last()

    panel = arena.merge(
        matches_out[["model_name_arena", "model_id_price", "match_confidence"]],
        left_on="model_name",
        right_on="model_name_arena",
        how="inner",
    )

    pr = prices.rename(columns={"model_id": "model_id_price"})[
        [
            "week_start",
            "model_id_price",
            "provider",
            "input_usd_per_mtok",
            "output_usd_per_mtok",
            "blended_3_1_usd_per_mtok",
        ]
    ].copy()
    pr["prov_rank"] = pr["provider"].map(bf.provider_rank)
    pr = pr.sort_values(["week_start", "model_id_price", "prov_rank"]).drop_duplicates(
        ["week_start", "model_id_price"], keep="first"
    )

    panel = panel.merge(pr, on=["week_start", "model_id_price"], how="inner")

    size_df = bf.match_sizes(panel["model_name_arena"].unique().tolist(), sizes, xwalk)
    panel = panel.merge(size_df, on="model_name_arena", how="left")

    panel = panel[
        [
            "week_start",
            "model_name_arena",
            "model_id_price",
            "provider",
            "elo",
            "blended_3_1_usd_per_mtok",
            "input_usd_per_mtok",
            "output_usd_per_mtok",
            "params_b",
            "open_weights",
            "match_confidence",
        ]
    ].copy()
    panel = panel.dropna(subset=["elo", "blended_3_1_usd_per_mtok"])
    panel = panel.sort_values(["week_start", "elo"], ascending=[True, False]).reset_index(
        drop=True
    )

    on_flags = np.zeros(len(panel), dtype=bool)
    for week, g in panel.groupby("week_start", sort=True):
        idx = g.index.to_numpy()
        on = bf.is_pareto(
            g["elo"].to_numpy(float), g["blended_3_1_usd_per_mtok"].to_numpy(float)
        )
        on_flags[idx] = on
    panel["on_frontier"] = on_flags

    panel_write = panel.copy()
    panel_write["week_start"] = panel_write["week_start"].dt.strftime("%Y-%m-%d")
    panel_write.to_csv(OUT / "arena_coding_elo_price_weekly_panel.csv", index=False)

    # Same-Elo cost anchors (coding starts ~2024-04)
    weeks_sorted = sorted(panel["week_start"].unique())
    models_per_week = panel.groupby("week_start").size()
    first_ge5 = models_per_week[models_per_week >= 5].index.min()
    target_anchors = [
        first_ge5,
        pd.Timestamp("2024-04-08"),
        pd.Timestamp("2024-07-01"),
        pd.Timestamp("2025-01-01"),
        pd.Timestamp("2025-07-01"),
        pd.Timestamp("2026-01-01"),
    ]
    anchors = []
    for t in target_anchors:
        if pd.isna(t):
            continue
        cand = [w for w in weeks_sorted if w <= t]
        if not cand:
            cand = [w for w in weeks_sorted if w >= t][:1]
        if not cand:
            continue
        w = cand[-1]
        fr = panel[(panel["week_start"] == w) & (panel["on_frontier"])]
        if fr.empty:
            for w2 in weeks_sorted:
                if w2 < w:
                    continue
                fr = panel[(panel["week_start"] == w2) & (panel["on_frontier"])]
                if not fr.empty:
                    w = w2
                    break
        if fr.empty:
            continue
        if w not in anchors:
            anchors.append(w)

    same_rows = []
    for t0 in anchors:
        fr0 = panel[(panel["week_start"] == t0) & (panel["on_frontier"])]
        fr0_pos = fr0[fr0["blended_3_1_usd_per_mtok"] > 0]
        q_star = float((fr0_pos if len(fr0_pos) else fr0)["elo"].max())
        for t in weeks_sorted:
            if t < t0:
                continue
            g = panel[panel["week_start"] == t]
            qual = g[(g["elo"] >= q_star) & (g["blended_3_1_usd_per_mtok"] > 0)]
            if qual.empty:
                same_rows.append(
                    {
                        "anchor_week": t0.strftime("%Y-%m-%d"),
                        "anchor_max_elo": q_star,
                        "week_start": t.strftime("%Y-%m-%d"),
                        "min_blended_price_for_anchor_elo": np.nan,
                        "achieving_model": None,
                        "n_models_qualifying": 0,
                    }
                )
            else:
                i = qual["blended_3_1_usd_per_mtok"].idxmin()
                row = qual.loc[i]
                same_rows.append(
                    {
                        "anchor_week": t0.strftime("%Y-%m-%d"),
                        "anchor_max_elo": q_star,
                        "week_start": t.strftime("%Y-%m-%d"),
                        "min_blended_price_for_anchor_elo": float(
                            row["blended_3_1_usd_per_mtok"]
                        ),
                        "achieving_model": row["model_name_arena"],
                        "n_models_qualifying": int(len(qual)),
                    }
                )
    same_df = pd.DataFrame(same_rows)
    same_df.to_csv(OUT / "same_coding_elo_cost_over_time.csv", index=False)

    panel2 = panel.copy()
    panel2["year"] = panel2["week_start"].dt.year
    arena_y = arena.copy()
    arena_y["year"] = arena_y["week_start"].dt.year
    match_rate_by_year = {}
    for y, g in arena_y.groupby("year"):
        models_y = set(g["model_name"].unique())
        matched_y = models_y & set(matches_out["model_name_arena"])
        match_rate_by_year[str(int(y))] = {
            "arena_models": len(models_y),
            "matched_models": len(matched_y),
            "match_rate": round(len(matched_y) / len(models_y), 4) if models_y else 0,
            "panel_rows": int((panel2["year"] == y).sum()),
            "panel_unique_models": int(
                panel2.loc[panel2["year"] == y, "model_name_arena"].nunique()
            ),
        }

    mpw = panel2.groupby("week_start").size()
    early_week = panel2["week_start"].min()
    late_week = panel2["week_start"].max()
    early_f = panel2[(panel2["week_start"] == early_week) & (panel2["on_frontier"])].sort_values(
        "elo", ascending=False
    )
    late_f = panel2[(panel2["week_start"] == late_week) & (panel2["on_frontier"])].sort_values(
        "elo", ascending=False
    )

    def frontier_examples(df):
        return [
            {
                "model": r["model_name_arena"],
                "elo": round(float(r["elo"]), 2),
                "blended": float(r["blended_3_1_usd_per_mtok"]),
                "provider": r["provider"],
            }
            for _, r in df.head(10).iterrows()
        ]

    decline = {}
    for aw, g in same_df.groupby("anchor_week"):
        g2 = g.dropna(subset=["min_blended_price_for_anchor_elo"]).sort_values("week_start")
        if len(g2) < 2:
            decline[aw] = {"has_series": False}
            continue
        first_p = float(g2.iloc[0]["min_blended_price_for_anchor_elo"])
        last_p = float(g2.iloc[-1]["min_blended_price_for_anchor_elo"])
        decline[aw] = {
            "has_series": True,
            "anchor_max_elo": float(g2.iloc[0]["anchor_max_elo"]),
            "start_price": first_p,
            "end_price": last_p,
            "start_week": g2.iloc[0]["week_start"],
            "end_week": g2.iloc[-1]["week_start"],
            "declined": bool(last_p < first_p),
            "pct_change": round(100 * (last_p - first_p) / first_p, 2) if first_p else None,
            "collapse_ratio": round(first_p / last_p, 2) if last_p else None,
        }

    mpw_by_year = {
        str(int(y)): {
            "median": float(s.median()),
            "mean": round(float(s.mean()), 2),
            "min": int(s.min()),
            "max": int(s.max()),
            "weeks": int(len(s)),
        }
        for y, s in mpw.groupby(mpw.index.year)
    }

    summary = {
        "generated": TODAY,
        "category": "coding",
        "arena_models_total": int(len(arena_models)),
        "matched_models": int(len(matches)),
        "match_rate": round(len(matches) / len(arena_models), 4),
        "reused_overall_matches": int(reused),
        "unmatched_models": int(len(unmatched)),
        "panel_rows": int(len(panel2)),
        "weeks_covered": int(panel2["week_start"].nunique()),
        "week_start_min": early_week.strftime("%Y-%m-%d"),
        "week_start_max": late_week.strftime("%Y-%m-%d"),
        "median_models_per_week": float(mpw.median()),
        "mean_models_per_week": round(float(mpw.mean()), 2),
        "models_per_week_by_year": mpw_by_year,
        "frontier_rows": int(panel2["on_frontier"].sum()),
        "median_frontier_models_per_week": float(
            panel2[panel2["on_frontier"]].groupby("week_start").size().median()
        ),
        "match_rate_by_year": match_rate_by_year,
        "example_frontier_early_week": early_week.strftime("%Y-%m-%d"),
        "example_frontier_early": frontier_examples(early_f),
        "example_frontier_latest_week": late_week.strftime("%Y-%m-%d"),
        "example_frontier_latest": frontier_examples(late_f),
        "same_elo_cost_decline": decline,
        "anchors": [a.strftime("%Y-%m-%d") for a in anchors],
        "top_unmatched": unmatched_freq.head(25).to_dict(orient="records"),
        "zero_price_panel_rows": int((panel2["blended_3_1_usd_per_mtok"] <= 0).sum()),
        "astra_note": (
            "GPT-6 Astra Max joins this coding spine from the 2026-09-11 snapshot (week 2026-09-07); "
            "DeepSeek V4.1 Flash Max, Claude Opus 5.5, GPT-6 Sol/Luna and Grok 4.7 from 2026-09-25 "
            "(week 2026-09-21); Gemini 4 Argon, Claude Sonnet/Haiku 5.5, GPT-6.1 Sol, Muse Wonder and "
            "Step 3.5 Flash/Step 5 Preview from weeks 2026-09-28 to 2026-10-26. Gemini 4 Carbon and MiMo v2.6 "
            "have no list price in our sources. Do not invent or merge scores."
        ),
        "note_span": (
            "Coding category on Arena Text begins 2024-04-03; panel weeks are Mondays "
            "with both a Text/coding score and blended API price."
        ),
    }
    with open(OUT / "_summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)

    lines = []
    lines.append("# Arena Text/coding score × blended price weekly frontiers\n")
    lines.append(
        f"Built **{TODAY}** from Arena Text **coding** weekly scores + Monday blended API prices. "
        "Legacy filenames retain `elo`; post-January 2024 ratings use Bradley–Terry estimation.\n"
    )
    lines.append("Parallel to the overall Text Elo spine in `data/frontiers/`.\n")
    lines.append("## Outputs\n")
    lines.append("| File | Description |")
    lines.append("|------|-------------|")
    lines.append("| `arena_price_name_matches.csv` | Coding Arena ↔ price matches |")
    lines.append("| `arena_unmatched_models.csv` | Unmatched coding Arena models |")
    lines.append(
        "| `arena_coding_elo_price_weekly_panel.csv` | Weekly panel + `on_frontier` |"
    )
    lines.append(
        "| `same_coding_elo_cost_over_time.csv` | Min blended $ to hit anchor peak coding Elo |"
    )
    lines.append("| `_summary.json` | Coverage / examples / collapse ratios |")
    lines.append("| `build_coding_frontiers.py` | Reproducible builder |\n")
    lines.append("## Name matching\n")
    lines.append(
        "Reuses `data/frontiers/arena_price_name_matches.csv` where Arena names overlap "
        f"(**{reused}** reused), then falls back to `build_frontiers.pick_match` for the rest.\n"
    )
    lines.append(
        f"**Overall:** {summary['matched_models']}/{summary['arena_models_total']} coding Arena models "
        f"({100 * summary['match_rate']:.1f}%).\n"
    )
    lines.append("### Match rates by year\n")
    lines.append("| Year | Arena models | Matched | Rate | Panel rows | Median models/week |")
    lines.append("|------|-------------|---------|------|------------|--------------------|")
    for y in sorted(match_rate_by_year.keys()):
        m = match_rate_by_year[y]
        mp = mpw_by_year.get(y, {})
        lines.append(
            f"| {y} | {m['arena_models']} | {m['matched_models']} | {100 * m['match_rate']:.1f}% | "
            f"{m['panel_rows']} | {mp.get('median', '—')} |"
        )
    lines.append("\n## Pareto\n")
    lines.append(
        "Per week: maximum Text/coding score, minimum 3:1 blended $/MTok (same domination rule as overall).\n"
    )
    lines.append("## Coverage\n")
    lines.append(
        f"- Panel weeks: **{summary['week_start_min']} → {summary['week_start_max']}** "
        f"({summary['weeks_covered']} weeks)\n"
        f"- Panel rows: **{summary['panel_rows']}**\n"
        f"- Median models/week: **{summary['median_models_per_week']}**\n"
        f"- Median frontier size/week: **{summary['median_frontier_models_per_week']}**\n"
    )
    lines.append(f"- {summary['note_span']}\n")
    lines.append(f"- **{summary['astra_note']}**\n")
    lines.append("## Same-score-threshold cost (coding)\n")
    lines.append(
        "Anchors: " + ", ".join(a.strftime("%Y-%m-%d") for a in anchors) + ".\n"
    )
    for aw, d in decline.items():
        if not d.get("has_series"):
            lines.append(f"- Anchor {aw}: insufficient series")
            continue
        ratio = d.get("collapse_ratio")
        arrow = "YES (decline)" if d["declined"] else "NO (up/flat)"
        lines.append(
            f"- Anchor {aw} (Q*={d['anchor_max_elo']:.1f}): "
            f"{d['start_price']:.4f} → {d['end_price']:.4f} $/MTok "
            f"({d['pct_change']}%, ~{ratio}×) — **{arrow}**"
        )
    lines.append("\n## Example frontier models\n")
    lines.append(f"### Early week ({summary['example_frontier_early_week']})\n")
    for e in summary["example_frontier_early"]:
        lines.append(f"- {e['model']}: score {e['elo']}, ${e['blended']}/MTok ({e['provider']})")
    lines.append(f"\n### Latest week ({summary['example_frontier_latest_week']})\n")
    for e in summary["example_frontier_latest"]:
        lines.append(f"- {e['model']}: score {e['elo']}, ${e['blended']}/MTok ({e['provider']})")
    lines.append("")
    # The shipped README is hand-curated; only scaffold one if it is missing.
    if not (OUT / "README.md").exists():
        (OUT / "README.md").write_text("\n".join(lines))

    print(
        json.dumps(
            {
                "match_rate": summary["match_rate"],
                "weeks_covered": summary["weeks_covered"],
                "span": [summary["week_start_min"], summary["week_start_max"]],
                "panel_rows": summary["panel_rows"],
                "frontier_rows": summary["frontier_rows"],
                "decline": {
                    k: (v.get("declined"), v.get("pct_change"), v.get("collapse_ratio"))
                    for k, v in decline.items()
                },
            },
            indent=2,
        )
    )
    print("Early:", summary["example_frontier_early"][:5])
    print("Latest:", summary["example_frontier_latest"][:5])


if __name__ == "__main__":
    main()
