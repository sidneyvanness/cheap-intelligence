#!/usr/bin/env python3
"""Fixed-intelligence cost charts + animation → media/coding/.

Reads data/frontiers/coding/fixed_intelligence_cost.csv (build_fixed_intelligence.py).

    python scripts/viz/make_fixed_intelligence.py            # statics + mp4 (needs ffmpeg)
    python scripts/viz/make_fixed_intelligence.py --skip-anim
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.animation import FFMpegWriter, FuncAnimation

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_story_viz as sv  # noqa: E402  (shared palette, fonts, title helpers)

ROOT = sv.ROOT
DATA = ROOT / "data" / "frontiers" / "coding"
OUT = sv.OUT

PRETTY = {
    "o1-2024-12-17": "o1",
    "o1-mini": "o1-mini",
    "o3-mini-high": "o3-mini (high)",
    "gpt-4.1-mini-2025-04-14": "GPT-4.1 mini",
    "gemini-2.5-flash-lite-preview-06-17-thinking": "Gemini 2.5 Flash-Lite",
    "gemini-2.0-flash-001": "Gemini 2.0 Flash",
    "mistral-small-2506": "Mistral Small 3.2",
    "mistral-medium-2508": "Mistral Medium 3.1",
    "mistral-large-3": "Mistral Large 3",
    "minimax-m2.1-preview": "MiniMax M2.1",
    "deepseek-v4-flash-thinking": "DeepSeek V4 Flash",
    "deepseek-v4-flash": "DeepSeek V4 Flash",
    "qwen3.5-flash": "Qwen3.5 Flash",
    "gpt-5-nano-high": "GPT-5 nano (high)",
    "gpt-6-luna-max": "GPT-6 Luna max",
    "o3-2025-04-16": "o3",
    "claude-3-7-sonnet-20250219": "Claude 3.7 Sonnet",
}

FOOTNOTE = (
    "Each week: cheapest paid API model rated at least as high as the anchor on that week's LMArena Text/coding board "
    "(matched, list-priced subset). Blended price = (3 × input + output) / 4, USD per 1M tokens.\n"
    "Arena score is a human-preference rating, not an absolute benchmark. Launch promotions are real but short-lived "
    "(GLM-5.3 Flash, Aug 31 2026). Sources: LMArena, RoninForge AI Price Index, Model Price Watch."
)


def pretty(name: str) -> str:
    return PRETTY.get(name) or sv.short_model(name, 26)


def usd(v: float) -> str:
    if v >= 1:
        return f"\\${v:.2f}"
    exact = f"{v:.5f}".rstrip("0")
    return "\\$" + (exact if len(exact) > 4 else f"{v:.2f}")


def load():
    df = pd.read_csv(DATA / "fixed_intelligence_cost.csv", parse_dates=["anchor_week", "week_start"])
    summary = json.loads((DATA / "fixed_intelligence_summary.json").read_text())
    return df, summary


def format_axes(ax, x0, x1, ymax):
    ax.set_yscale("log")
    ax.set_ylim(0.06, ymax)
    ticks = [t for t in [0.1, 0.25, 0.5, 1, 2.5, 5, 10, 25] if t < ymax]
    ax.set_yticks(ticks)
    ax.set_yticklabels([usd(t) if t < 1 else f"\\${t:g}" for t in ticks])
    ax.yaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_xlim(x0, x1)
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    ax.grid(axis="y", color=sv.GRID, lw=0.8)
    ax.tick_params(length=0)
    ax.spines["left"].set_visible(False)


def step_xy(g: pd.DataFrame):
    """Step-post line extended one week past the last observation."""
    x = list(g["week_start"]) + [g["week_start"].iloc[-1] + pd.Timedelta(days=7)]
    y = list(g["cheapest_price"]) + [g["cheapest_price"].iloc[-1]]
    return x, y


# Label offsets (points) for the primary anchor's record lows, tuned by eye.
HERO_OFFSETS = [(12, 4), (12, 10), (-10, -8), (10, 10), (-10, 36)]


def hero_frame(fig, ax, g, summ):
    months = round(summ["months_elapsed"])
    sv.add_title_block(
        fig,
        f"The price of o1-level coding fell {summ['fold_cheaper']:.0f}× in {months} months",
        "Cheapest API model rated at least as high as OpenAI o1 on each week's Arena Text/coding board  ·  "
        "blended USD per 1M tokens (log)",
    )
    format_axes(ax, g["week_start"].iloc[0] - pd.Timedelta(days=20), g["week_start"].iloc[-1] + pd.Timedelta(days=75), 60)
    ax.axhline(summ["anchor_price"], color=sv.RAW_PEAK, lw=1, ls=(0, (2, 3)), zorder=1)
    ax.text(
        g["week_start"].iloc[-1] + pd.Timedelta(days=70), summ["anchor_price"] * 1.12,
        f"o1 list price {usd(summ['anchor_price'])}", ha="right", va="bottom", fontsize=9, color=sv.MUTED,
    )
    sv.add_footnote(fig, FOOTNOTE, y=0.018)


def label_record(ax, row, offset, bold_price=True):
    ax.annotate(
        f"{usd(row['cheapest_price'])}\n{pretty(row['cheapest_model'])} · {row['week_start']:%b %Y}",
        (row["week_start"], row["cheapest_price"]),
        xytext=offset, textcoords="offset points", fontsize=9.5, color=sv.INK,
        ha="left" if offset[0] >= 0 else "right", va="bottom" if offset[1] >= 0 else "top", linespacing=1.35,
    )


def make_hero(df, summary):
    summ = next(a for a in summary["anchors"] if a["anchor_model"] == summary["primary_anchor"])
    g = df[df["anchor_model"] == summary["primary_anchor"]].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(12.5, 7.6))
    fig.subplots_adjust(left=0.07, right=0.97, top=0.82, bottom=0.17)
    hero_frame(fig, ax, g, summ)
    x, y = step_xy(g)
    ax.step(x, y, where="post", color=sv.ACCENT, lw=2.2, zorder=3, solid_joinstyle="round")
    rec = g[g["is_record_low"]].reset_index(drop=True)
    ax.scatter(rec["week_start"], rec["cheapest_price"], s=58, color=sv.ACCENT, edgecolor=sv.BG, lw=2, zorder=4)
    for i, row in rec.iterrows():
        label_record(ax, row, HERO_OFFSETS[i] if i < len(HERO_OFFSETS) else (10, 8))
    last = g.iloc[-1]
    ax.annotate(
        f"Now: {usd(last['cheapest_price'])}\n{pretty(last['cheapest_model'])}",
        (x[-1], last["cheapest_price"]), xytext=(8, 0), textcoords="offset points",
        fontsize=10.5, fontweight="semibold", color=sv.INK, va="center", linespacing=1.35,
    )
    png = OUT / "fixed_intelligence.png"
    fig.savefig(png, dpi=sv.DPI)
    plt.close(fig)
    return png


def make_anchors(df, summary):
    fig, axes = plt.subplots(2, 2, figsize=(12.5, 8.6), sharey=True)
    fig.subplots_adjust(left=0.07, right=0.97, top=0.77, bottom=0.13, hspace=0.66, wspace=0.08)
    sv.add_title_block(
        fig,
        "Same intelligence, four starting points: 13× to 150× cheaper",
        "Each panel takes one past leader of the Arena Text/coding board and tracks the cheapest model rated at least\n"
        "as high, week by week  ·  blended USD per 1M tokens (log)",
    )
    x0, x1 = df["week_start"].min() - pd.Timedelta(days=20), df["week_start"].max() + pd.Timedelta(days=30)
    for ax, a in zip(axes.flat, summary["anchors"]):
        g = df[df["anchor_model"] == a["anchor_model"]]
        format_axes(ax, x0, x1, 60)
        x, y = step_xy(g)
        ax.step(x, y, where="post", color=sv.ACCENT, lw=2, zorder=3)
        ax.scatter([g["week_start"].iloc[0]], [a["anchor_price"]], s=46, color=sv.ACCENT, edgecolor=sv.BG, lw=2, zorder=4)
        ax.set_title(
            f"{a['anchor_label']}  ·  {pd.Timestamp(a['anchor_week']):%b %Y}", loc="left", fontsize=12.5,
            fontweight="semibold", pad=24,
        )
        ax.text(
            0, 1.035,
            f"{usd(a['anchor_price'])} → {usd(a['latest_price'])} ({pretty(a['latest_model'])})  ·  "
            f"{a['fold_cheaper']:.0f}× in {a['months_elapsed']:.0f} months",
            transform=ax.transAxes, fontsize=9.5, color=sv.MUTED, va="bottom",
        )
    sv.add_footnote(fig, FOOTNOTE, y=0.015)
    png = OUT / "fixed_intelligence_anchors.png"
    fig.savefig(png, dpi=sv.DPI)
    plt.close(fig)
    return png


def make_animation(df, summary, fps=12, frames_per_week=2, hold_s=1.6, end_hold_s=4.0):
    summ = next(a for a in summary["anchors"] if a["anchor_model"] == summary["primary_anchor"])
    g = df[df["anchor_model"] == summary["primary_anchor"]].reset_index(drop=True)
    rec_idx = list(g.index[g["is_record_low"]])

    # Frame schedule: week index per frame, with holds on each record low and at the end.
    schedule = []
    for i in range(len(g)):
        schedule += [i] * (int(hold_s * fps) if i in rec_idx else frames_per_week)
    schedule += [len(g) - 1] * int(end_hold_s * fps)

    fig, ax = plt.subplots(figsize=(12.5, 7.6))
    fig.subplots_adjust(left=0.07, right=0.97, top=0.82, bottom=0.17)
    hero_frame(fig, ax, g, summ)
    (line,) = ax.step([], [], where="post", color=sv.ACCENT, lw=2.4, zorder=3)
    dots = ax.scatter([], [], s=58, color=sv.ACCENT, edgecolor=sv.BG, lw=2, zorder=4)
    tip = ax.scatter([], [], s=90, color=sv.ACCENT, edgecolor=sv.BG, lw=2.5, zorder=5)
    tip_text = ax.text(0, 0, "", fontsize=10.5, fontweight="semibold", color=sv.INK, va="center", linespacing=1.35)
    date_text = ax.text(0.985, 0.80, "", transform=ax.transAxes, ha="right", va="bottom", fontsize=13, color=sv.MUTED)
    fold_text = ax.text(0.985, 0.70, "", transform=ax.transAxes, ha="right", va="bottom", fontsize=24,
                        fontfamily=sv.DISPLAY_FONT, fontweight="semibold", color=sv.INK)
    labels: dict[int, object] = {}

    def update(f):
        i = schedule[f]
        cur = g.iloc[: i + 1]
        x, y = step_xy(cur)
        line.set_data(x, y)
        shown = [r for r in rec_idx if r <= i]
        dots.set_offsets(np.c_[mdates.date2num(g.loc[shown, "week_start"]), g.loc[shown, "cheapest_price"]])
        for k, r in enumerate(rec_idx):
            if r <= i and r not in labels:
                label_record(ax, g.loc[r], HERO_OFFSETS[k] if k < len(HERO_OFFSETS) else (10, 8))
                labels[r] = True
        row = g.iloc[i]
        tip.set_offsets([[mdates.date2num(x[-1]), row["cheapest_price"]]])
        tip_text.set_position((x[-1] + pd.Timedelta(days=9), row["cheapest_price"]))
        tip_text.set_text("" if i in rec_idx and i != len(g) - 1 else f"{usd(row['cheapest_price'])}\n{pretty(row['cheapest_model'])}")
        date_text.set_text(f"{row['week_start']:%b %Y}")
        fold = summ["anchor_price"] / row["cheapest_price"]
        fold_text.set_text(f"{fold:.0f}× cheaper than o1 at launch" if fold >= 1.5 else "Only o1 clears its own bar")
        return []

    anim = FuncAnimation(fig, update, frames=len(schedule), interval=1000 / fps, blit=False)
    mp4 = OUT / "fixed_intelligence.mp4"
    anim.save(str(mp4), writer=FFMpegWriter(fps=fps, bitrate=3600, metadata={"title": "Cost of o1-level coding over time"}), dpi=160)
    fig.savefig(OUT / "fixed_intelligence_last_frame.png", dpi=160)
    plt.close(fig)
    return mp4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-anim", action="store_true")
    ap.add_argument("--fps", type=int, default=12)
    args = ap.parse_args()
    sv.style_rc()
    df, summary = load()
    print(make_hero(df, summary))
    print(make_anchors(df, summary))
    if not args.skip_anim:
        print(make_animation(df, summary, fps=args.fps))


if __name__ == "__main__":
    main()
