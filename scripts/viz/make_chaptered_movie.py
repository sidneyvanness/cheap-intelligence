#!/usr/bin/env python3
"""Chaptered coding intelligence–price frontier movie with pause beats.

Outputs:
  media/coding/frontier_evolution_chaptered.mp4
  media/coding/frontier_evolution_chaptered_last_frame.png
  media/coding/frontier_evolution_chaptered_ch7_hold.png
  media/coding/CHAPTERED.md  (written alongside)

Usage:
  python -m venv .venv && source .venv/bin/activate  # or your env
  python media/coding/make_chaptered_movie.py
"""

from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from matplotlib import colors as mcolors
from matplotlib.animation import FFMpegWriter, FuncAnimation

ROOT = Path(__file__).resolve().parents[2]  # cheap-intelligence/
OUT = ROOT / "media" / "coding"
OUT.mkdir(parents=True, exist_ok=True)
FONT_DIR = Path(__file__).resolve().parent / "fonts"
PANEL_CSV = (
    ROOT / "data" / "frontiers" / "coding" / "arena_coding_elo_price_weekly_panel.csv"
)

PRICE_FLOOR = 0.05
DPI_ANIM = 160

BG = "#F7F5F2"
INK = "#1C1917"
MUTED = "#78716C"
GRID = "#E7E5E4"
ACCENT = "#E11D48"
ACCENT_SOFT = "#BE185D"
CMAP_COLORS = ["#A8A29E", "#94A3B8", "#64748B", "#6366F1", "#C026D3", "#E11D48"]

CURRENCY_FOOTNOTE = (
    "Arena Text/coding score (legacy files: Elo) × API prices through 2026-10-26. "
    "Free tiers at ≤$0.05. GLM-5.3 Flash Aug 31 = launch promo; "
    "Gemini 4 Argon = intro rate; Gemini 4 Carbon, MiMo v2.6: no list price."
)

# Pacing (target ~50–70s with longer shape-shock holds)
FPS = 12
QUIET_FRAMES = 3  # 0.25s per non-chapter week
END_CARD_FRAMES = 36  # 3.0s — room for end card without HUD fight

# (date, caption, highlight_mode, hold_seconds, price_ceiling|None)
# highlight_mode: "peak" | "cheapest_positive" | "max_elo_under_price"
CHAPTERS = [
    (
        "2024-04-01",
        "GPT-4 era coding frontier · score ~1267 @ $15/MTok",
        "peak",
        3.0,
        None,
    ),
    (
        "2024-05-13",
        "GPT-4o · higher score, lower price",
        "peak",
        3.0,
        None,
    ),
    (
        "2024-09-16",
        "o1-mini · frontier jump under $2/MTok",
        "peak",
        4.5,
        None,
    ),
    (
        "2025-06-23",
        "Gemini 2.5 Pro · score ~1492 @ ~$3.44",
        "peak",
        3.5,
        None,
    ),
    (
        "2025-11-24",
        "Claude Opus 4.5 thinking · new ceiling @ $10",
        "peak",
        3.0,
        None,
    ),
    (
        "2026-02-09",
        "Claude Opus 4.6 thinking · score ~1553",
        "peak",
        3.0,
        None,
    ),
    (
        "2026-08-31",
        "Near-frontier score at ~$0.12/MTok (launch promo) · peak still ~$10",
        "max_elo_under_price",
        4.5,
        0.25,
    ),
    (
        "2026-09-21",
        "Claude Opus 5.5 · new peak ~1545 at $8 — higher and cheaper",
        "peak",
        4.0,
        None,
    ),
    (
        "2026-10-26",
        "Gemini 4 Argon · ~1538 at $4, within 9 points of Opus 5.5 at half the price",
        "max_elo_under_price",
        5.0,
        4.0,
    ),
]

END_CARD_LINE = (
    "Same published Arena score threshold (~1267): ~$15 → ~$0.13 at standard list prices · about 118× cheaper"
)


def mpl_escape(s: str) -> str:
    """Escape $ so matplotlib does not treat captions as mathtext."""
    return s.replace("$", r"\$")


def register_fonts() -> tuple[str, str]:
    body, display = "DejaVu Sans", "DejaVu Sans"
    if FONT_DIR.exists():
        for ttf in sorted(FONT_DIR.glob("*.ttf")):
            try:
                fm.fontManager.addfont(str(ttf))
            except Exception:
                pass
        families = {f.name for f in fm.fontManager.ttflist}
        if "Inter" in families:
            body = "Inter"
        if "Inter Display" in families:
            display = "Inter Display"
        elif "Inter" in families:
            display = "Inter"
    return body, display


BODY_FONT, DISPLAY_FONT = register_fonts()


def style_rc():
    plt.rcParams.update(
        {
            "figure.facecolor": BG,
            "axes.facecolor": BG,
            "savefig.facecolor": BG,
            "text.color": INK,
            "axes.labelcolor": INK,
            "axes.edgecolor": "#D6D3D1",
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "axes.linewidth": 0.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "font.family": BODY_FONT,
            "font.size": 11,
            "axes.titlesize": 16,
            "axes.titleweight": "semibold",
            "axes.labelsize": 11,
            "xtick.labelsize": 9.5,
            "ytick.labelsize": 9.5,
            "figure.dpi": 120,
            "savefig.dpi": 220,
            "axes.grid": False,
            "axes.axisbelow": True,
        }
    )


def time_cmap():
    return mcolors.LinearSegmentedColormap.from_list("frontier_time", CMAP_COLORS)


def week_norm(weeks: pd.Series):
    t0 = weeks.min().toordinal()
    t1 = weeks.max().toordinal()
    if t1 == t0:
        return lambda w: 0.5
    return lambda w: (pd.Timestamp(w).toordinal() - t0) / (t1 - t0)


def frontier_xy(week_df: pd.DataFrame):
    s = week_df.sort_values(["price_plot", "elo"], ascending=[True, True])
    return s["price_plot"].to_numpy(), s["elo"].to_numpy(), s


def format_price_axis(ax):
    ax.set_xscale("log")
    ax.set_xlim(PRICE_FLOOR * 0.85, 55)
    ticks = [0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 25]
    ax.set_xticks(ticks)
    ax.set_xticklabels(
        [
            r"≤\$0.05",
            r"\$0.10",
            r"\$0.25",
            r"\$0.50",
            r"\$1",
            r"\$2.50",
            r"\$5",
            r"\$10",
            r"\$25",
        ]
    )
    ax.set_xlabel("Blended API price  ·  USD / 1M tokens  (log)", color=MUTED, labelpad=10)


def format_elo_axis(ax, ymin=1150, ymax=1570):
    ax.set_ylim(ymin, ymax)
    ax.set_ylabel("Arena Text/coding score", color=MUTED, labelpad=10)
    ax.yaxis.set_major_locator(mticker.MultipleLocator(50))
    ax.yaxis.set_minor_locator(mticker.MultipleLocator(25))


def load_frontier() -> pd.DataFrame:
    df = pd.read_csv(PANEL_CSV)
    df["week_start"] = pd.to_datetime(df["week_start"])
    df = df[df["on_frontier"] == True].copy()  # noqa: E712
    df["price_plot"] = df["blended_3_1_usd_per_mtok"].clip(lower=PRICE_FLOOR)
    return df


@dataclass(frozen=True)
class Chapter:
    week: pd.Timestamp
    caption: str
    index: int  # 1-based
    week_i: int  # index into weeks array
    highlight_mode: str
    hold_seconds: float
    price_ceiling: float | None
    hold_frames: int


@dataclass
class FrameSpec:
    kind: str  # "week" | "end"
    week_i: int
    hold: bool
    chapter: Chapter | None


def nearest_week(weeks: pd.DatetimeIndex, target: str) -> pd.Timestamp:
    ts = pd.Timestamp(target)
    return min(weeks, key=lambda w: abs((w - ts).days))


def build_chapters(weeks: pd.DatetimeIndex, fps: int) -> list[Chapter]:
    week_to_i = {w: i for i, w in enumerate(weeks)}
    out: list[Chapter] = []
    for n, (date_s, caption, mode, hold_s, ceiling) in enumerate(CHAPTERS, start=1):
        w = nearest_week(weeks, date_s)
        hold_frames = max(1, int(round(hold_s * fps)))
        out.append(
            Chapter(
                week=w,
                caption=caption,
                index=n,
                week_i=week_to_i[w],
                highlight_mode=mode,
                hold_seconds=hold_s,
                price_ceiling=ceiling,
                hold_frames=hold_frames,
            )
        )
    return out


def build_frame_schedule(n_weeks: int, chapters: list[Chapter]) -> list[FrameSpec]:
    chapter_by_week = {c.week_i: c for c in chapters}
    frames: list[FrameSpec] = []
    for i in range(n_weeks):
        ch = chapter_by_week.get(i)
        if ch is not None:
            for _ in range(ch.hold_frames):
                frames.append(FrameSpec(kind="week", week_i=i, hold=True, chapter=ch))
        else:
            for _ in range(QUIET_FRAMES):
                frames.append(FrameSpec(kind="week", week_i=i, hold=False, chapter=None))
    last_i = n_weeks - 1
    for _ in range(END_CARD_FRAMES):
        frames.append(FrameSpec(kind="end", week_i=last_i, hold=True, chapter=None))
    return frames


def short_model(name: str, n: int = 28) -> str:
    raw = str(name)
    pretty = {
        "claude-opus-4-6-high": "Claude Opus 4.6 high",
        "claude-opus-5.5-high": "Claude Opus 5.5 high",
        "gpt-6-luna-max": "GPT-6 Luna max",
        "gemini-4-argon-high": "Gemini 4 Argon high",
        "Claude Haiku 5.5 (High)": "Claude Haiku 5.5 high",
        "step-3.5-flash": "Step 3.5 Flash",
        "claude-opus-4-6-thinking": "Claude Opus 4.6 thinking",
        "claude-opus-4-5-20251101-thinking-32k": "Claude Opus 4.5 thinking",
        "gpt-4-1106-preview": "GPT-4 Turbo (1106)",
        "gpt-4o-2024-05-13": "GPT-4o",
        "gemini-2.5-pro": "Gemini 2.5 Pro",
        "o1-mini": "o1-mini",
        "glm-5.3-flash": "GLM-5.3 Flash",
        "glm-4.7-flash": "GLM-4.7 Flash",
    }
    if raw in pretty:
        s = pretty[raw]
    else:
        s = raw.replace("-2024-", "-").replace("-2025-", "-").replace("-2026-", "-")
        if s in pretty:
            s = pretty[s]
    if len(s) <= n:
        return s
    return s[: n - 1] + "…"


def format_price_label(price: float) -> str:
    if price < 0.01:
        return f"${price:.3f}"
    if price < 1:
        return f"${price:.2f}".rstrip("0").rstrip(".") if price >= 0.1 else f"${price:.3g}"
    if price < 10:
        return f"${price:.2g}" if price != int(price) else f"${int(price)}"
    return f"${price:.3g}"


def pick_highlight(
    week_df: pd.DataFrame, mode: str, price_ceiling: float | None
) -> tuple[pd.Series, pd.Series | None]:
    """Return (primary row, optional secondary contrast row)."""
    peak = week_df.loc[week_df["elo"].idxmax()]
    secondary = None

    if mode == "peak":
        return peak, None

    if mode == "cheapest_positive":
        pos = week_df[week_df["blended_3_1_usd_per_mtok"] > 0]
        if pos.empty:
            return peak, None
        row = pos.loc[pos["blended_3_1_usd_per_mtok"].idxmin()]
        return row, None

    if mode == "max_elo_under_price":
        ceiling = 0.25 if price_ceiling is None else float(price_ceiling)
        under = week_df[week_df["blended_3_1_usd_per_mtok"] <= ceiling]
        if under.empty:
            return peak, None
        primary = under.loc[under["elo"].idxmax()]
        # Contrast: peak if it is a different point (e.g. ~$10 ceiling)
        if primary.name != peak.name:
            secondary = peak
        return primary, secondary

    return peak, None


def annotation_offset(ax, x: float, y: float) -> tuple[float, float]:
    """Pick a text offset (points) that stays inside axes and off the polyline."""
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    # log-x: compare in log space
    x_mid = np.sqrt(xlim[0] * xlim[1])
    y_mid = 0.5 * (ylim[0] + ylim[1])

    # Prefer upper-left for right-side peaks, upper-right for cheap left points
    if x < x_mid:
        dx, dy = 28, 22
    else:
        dx, dy = -110, 18

    # If near top of plot, push label down
    if y > ylim[0] + 0.82 * (ylim[1] - ylim[0]):
        dy = -36 if dy > 0 else dy
        if x < x_mid:
            dx, dy = 32, -40
        else:
            dx, dy = -120, -38

    # If very high and left (cheap high-Elo), label above-right but clear of point
    if x < x_mid and y > ylim[0] + 0.75 * (ylim[1] - ylim[0]):
        dx, dy = 36, -8

    return dx, dy


def make_chaptered_movie(
    fps: int = FPS,
) -> tuple[Path, list[Chapter], list[FrameSpec], float, dict]:
    style_rc()
    frontier = load_frontier()
    weeks = pd.DatetimeIndex(sorted(frontier["week_start"].unique()))
    if len(weeks) < 10:
        raise ValueError(f"expected many weekly frames, got {len(weeks)}")

    chapters = build_chapters(weeks, fps=fps)
    schedule = build_frame_schedule(len(weeks), chapters)
    duration_s = len(schedule) / fps

    cmap = time_cmap()
    norm_fn = week_norm(pd.Series(weeks))

    cache: list[tuple[np.ndarray, np.ndarray, float]] = []
    peaks: list[pd.Series] = []
    week_dfs: list[pd.DataFrame] = []
    for w in weeks:
        wdf = frontier[frontier["week_start"] == w].copy()
        x, y, _ = frontier_xy(wdf)
        cache.append((x, y, norm_fn(w)))
        peaks.append(wdf.loc[wdf["elo"].idxmax()])
        week_dfs.append(wdf)

    # Precompute highlights per chapter
    chapter_highlights: dict[int, tuple[pd.Series, pd.Series | None]] = {}
    for ch in chapters:
        primary, secondary = pick_highlight(
            week_dfs[ch.week_i], ch.highlight_mode, ch.price_ceiling
        )
        chapter_highlights[ch.index] = (primary, secondary)

    fig, ax = plt.subplots(figsize=(12.5, 7.6))
    # HUD band above axes — same anti-overlap rule as make_story_viz
    fig.subplots_adjust(left=0.09, right=0.96, top=0.68, bottom=0.13)

    format_price_axis(ax)
    format_elo_axis(ax)
    for yv in range(1150, 1550, 50):
        ax.axhline(yv, color=GRID, lw=0.55, zorder=0)

    hist_lines = []
    for x, y, t in cache:
        color = cmap(t)
        if len(x) >= 2:
            (ln,) = ax.plot(
                x,
                y,
                color=color,
                lw=0.9 + 0.6 * t,
                alpha=0.0,
                solid_capstyle="round",
                zorder=2,
            )
        else:
            (ln,) = ax.plot(
                x,
                y,
                color=color,
                lw=0,
                alpha=0.0,
                marker="o",
                markersize=4,
                zorder=2,
            )
        hist_lines.append(ln)

    current_line = ax.plot(
        [], [], color=CMAP_COLORS[-1], lw=3.0, zorder=8, solid_capstyle="round"
    )[0]
    current_pts = ax.scatter(
        [], [], s=32, color=CMAP_COLORS[-1], zorder=9, edgecolors="white", linewidths=0.7
    )

    # Primary pointer: large ring + filled core
    ring = ax.scatter(
        [],
        [],
        s=420,
        facecolors="none",
        edgecolors=ACCENT,
        linewidths=2.4,
        zorder=20,
        alpha=0.0,
    )
    core = ax.scatter(
        [],
        [],
        s=72,
        facecolors=ACCENT,
        edgecolors="white",
        linewidths=1.2,
        zorder=21,
        alpha=0.0,
    )
    # Optional secondary (faint) contrast marker — e.g. $10 peak on ch7
    ring2 = ax.scatter(
        [],
        [],
        s=280,
        facecolors="none",
        edgecolors=MUTED,
        linewidths=1.6,
        zorder=18,
        alpha=0.0,
    )
    core2 = ax.scatter(
        [],
        [],
        s=40,
        facecolors=MUTED,
        edgecolors="white",
        linewidths=0.8,
        zorder=19,
        alpha=0.0,
    )

    callout_ann = [None]  # mutable holder for Annotation
    callout2_ann = [None]

    fig.text(
        0.09,
        0.93,
        "The coding intelligence–price frontier",
        fontsize=14,
        fontfamily=DISPLAY_FONT,
        fontweight="semibold",
        color=INK,
    )
    fig.text(
        0.09,
        0.895,
        "Chaptered trail · pause at key shifts · older curves muted",
        fontsize=10,
        color=MUTED,
    )

    date_text = fig.text(
        0.09,
        0.84,
        "",
        fontsize=18,
        fontfamily=DISPLAY_FONT,
        fontweight="semibold",
        color=INK,
        va="top",
        bbox=dict(boxstyle="round,pad=0.25", fc=BG, ec="none", alpha=0.98),
    )
    caption_text = fig.text(
        0.09,
        0.785,
        "",
        fontsize=11.5,
        fontfamily=BODY_FONT,
        color=INK,
        va="top",
        bbox=dict(boxstyle="round,pad=0.28", fc=BG, ec="#D6D3D1", alpha=0.98),
    )
    chapter_badge = fig.text(
        0.96,
        0.93,
        "",
        fontsize=11,
        fontfamily=BODY_FONT,
        color=MUTED,
        ha="right",
        va="top",
        bbox=dict(boxstyle="round,pad=0.22", fc=BG, ec="none", alpha=0.98),
    )
    # End card: full-width panel in header band (0.78–0.90), centered — no date HUD
    end_card = fig.text(
        0.525,
        0.835,
        "",
        fontsize=13.5,
        fontfamily=DISPLAY_FONT,
        fontweight="semibold",
        color=INK,
        ha="center",
        va="center",
        bbox=dict(
            boxstyle="round,pad=0.55",
            fc="#FFFFFF",
            ec="#D6D3D1",
            alpha=0.98,
            mutation_aspect=0.4,
        ),
        wrap=True,
        linespacing=1.35,
    )
    fig.text(
        0.09,
        0.035,
        CURRENCY_FOOTNOTE,
        fontsize=7,
        color=MUTED,
        fontfamily=BODY_FONT,
    )

    def clear_pointers():
        ring.set_alpha(0.0)
        core.set_alpha(0.0)
        ring.set_offsets(np.empty((0, 2)))
        core.set_offsets(np.empty((0, 2)))
        ring2.set_alpha(0.0)
        core2.set_alpha(0.0)
        ring2.set_offsets(np.empty((0, 2)))
        core2.set_offsets(np.empty((0, 2)))
        if callout_ann[0] is not None:
            callout_ann[0].set_visible(False)
        if callout2_ann[0] is not None:
            callout2_ann[0].set_visible(False)

    def show_pointer(row: pd.Series, secondary: pd.Series | None):
        x = float(row["price_plot"])
        y = float(row["elo"])
        price = float(row["blended_3_1_usd_per_mtok"])
        label = (
            f"{short_model(row['model_name_arena'], 26)}\n"
            f"Score {row['elo']:.0f}  ·  {mpl_escape(format_price_label(price))}/MTok"
        )

        ring.set_offsets([[x, y]])
        core.set_offsets([[x, y]])
        ring.set_alpha(0.95)
        core.set_alpha(1.0)

        dx, dy = annotation_offset(ax, x, y)

        if callout_ann[0] is not None:
            callout_ann[0].remove()
            callout_ann[0] = None

        callout_ann[0] = ax.annotate(
            label,
            xy=(x, y),
            xytext=(dx, dy),
            textcoords="offset points",
            fontsize=10,
            fontfamily=BODY_FONT,
            fontweight="semibold",
            color=INK,
            ha="left" if dx >= 0 else "right",
            va="center",
            zorder=22,
            bbox=dict(
                boxstyle="round,pad=0.35",
                fc="#FFFFFF",
                ec=ACCENT,
                lw=1.1,
                alpha=0.96,
            ),
            arrowprops=dict(
                arrowstyle="-|>",
                color=ACCENT,
                lw=1.4,
                connectionstyle="arc3,rad=0.12",
                shrinkA=0,
                shrinkB=10,
            ),
        )

        if secondary is not None:
            x2 = float(secondary["price_plot"])
            y2 = float(secondary["elo"])
            p2 = float(secondary["blended_3_1_usd_per_mtok"])
            ring2.set_offsets([[x2, y2]])
            core2.set_offsets([[x2, y2]])
            ring2.set_alpha(0.55)
            core2.set_alpha(0.55)

            if callout2_ann[0] is not None:
                callout2_ann[0].remove()
                callout2_ann[0] = None

            label2 = (
                f"peak · {short_model(secondary['model_name_arena'], 22)}\n"
                f"Score {secondary['elo']:.0f}  ·  {mpl_escape(format_price_label(p2))}"
            )
            # Place secondary label opposite side / lower
            dx2, dy2 = -100, -42
            callout2_ann[0] = ax.annotate(
                label2,
                xy=(x2, y2),
                xytext=(dx2, dy2),
                textcoords="offset points",
                fontsize=8.5,
                fontfamily=BODY_FONT,
                color=MUTED,
                ha="right",
                va="top",
                zorder=17,
                alpha=0.85,
                bbox=dict(
                    boxstyle="round,pad=0.28",
                    fc=BG,
                    ec="#D6D3D1",
                    lw=0.8,
                    alpha=0.92,
                ),
                arrowprops=dict(
                    arrowstyle="-",
                    color=MUTED,
                    lw=0.9,
                    alpha=0.7,
                    connectionstyle="arc3,rad=-0.08",
                    shrinkB=8,
                ),
            )
        else:
            ring2.set_alpha(0.0)
            core2.set_alpha(0.0)
            ring2.set_offsets(np.empty((0, 2)))
            core2.set_offsets(np.empty((0, 2)))
            if callout2_ann[0] is not None:
                callout2_ann[0].set_visible(False)

    def paint_trail(i: int, hold: bool):
        """Reveal weeks 0..i; during holds, dim older trails more so current pops."""
        for j in range(i + 1):
            x, y, t = cache[j]
            color = cmap(t)
            age_frac = (i - j) / max(i, 1) if i > 0 else 0.0
            base = 0.12 + 0.40 * t
            if hold:
                # Extra mute on older curves during chapter freezes
                alpha = base * (0.22 + 0.55 * (1.0 - 0.92 * age_frac))
                max_a = 0.38
            else:
                alpha = base * (0.35 + 0.65 * (1.0 - 0.85 * age_frac))
                max_a = 0.55
            if j < i:
                hist_lines[j].set_alpha(min(max_a, max(0.06, alpha)))
                hist_lines[j].set_color(color)
                hist_lines[j].set_linewidth(0.75 + 0.65 * t)
                hist_lines[j].set_zorder(2 + t)
            else:
                hist_lines[j].set_alpha(0.0)

        x, y, t = cache[i]
        color = cmap(t)
        if len(x) >= 2:
            current_line.set_data(x, y)
            current_line.set_color(color)
            current_line.set_linewidth(3.35 if hold else 3.0)
            current_pts.set_offsets(np.column_stack([x, y]))
            current_pts.set_facecolor(color)
            current_pts.set_sizes([38 if hold else 32] * len(x))
        elif len(x) == 1:
            current_line.set_data([], [])
            current_pts.set_offsets(np.column_stack([x, y]))
            current_pts.set_facecolor(color)
        else:
            current_line.set_data([], [])
            current_pts.set_offsets(np.empty((0, 2)))

    def init():
        current_line.set_data([], [])
        current_pts.set_offsets(np.empty((0, 2)))
        for ln in hist_lines:
            ln.set_alpha(0.0)
        date_text.set_text("")
        caption_text.set_text("")
        chapter_badge.set_text("")
        end_card.set_text("")
        clear_pointers()
        return [current_line, current_pts]

    def update(frame_i: int):
        spec = schedule[frame_i]
        i = spec.week_i
        paint_trail(i, hold=spec.hold or spec.kind == "end")

        w = weeks[i]
        peak = peaks[i]

        if spec.kind == "end":
            # Hide date/caption HUD entirely — end card owns the header band
            date_text.set_text("")
            caption_text.set_text("")
            chapter_badge.set_text("")
            end_card.set_text(mpl_escape(END_CARD_LINE))
            clear_pointers()
        elif spec.hold and spec.chapter is not None:
            ch = spec.chapter
            date_text.set_text(w.strftime("%b %-d, %Y"))
            caption_text.set_text(mpl_escape(ch.caption))
            chapter_badge.set_text(f"{ch.index}/{len(chapters)}")
            end_card.set_text("")
            primary, secondary = chapter_highlights[ch.index]
            show_pointer(primary, secondary)
        else:
            date_text.set_text(w.strftime("%b %Y"))
            caption_text.set_text(
                f"Peak  {short_model(peak['model_name_arena'])}"
                f"   ·   score {peak['elo']:.0f}"
                f"   ·   \\${peak['blended_3_1_usd_per_mtok']:.3g}/MTok"
            )
            chapter_badge.set_text("")
            end_card.set_text("")
            clear_pointers()

        return [current_line, current_pts]

    # Capture mid-hold still for chapter 7 before animation save
    ch7 = next(c for c in chapters if c.index == 7)
    ch7_frame_i = next(
        i for i, s in enumerate(schedule) if s.chapter is not None and s.chapter.index == 7
    )
    # Mid-hold frame index
    mid_ch7 = ch7_frame_i + ch7.hold_frames // 2

    anim = FuncAnimation(
        fig,
        update,
        frames=len(schedule),
        init_func=init,
        interval=1000 / fps,
        blit=False,
    )

    mp4 = OUT / "frontier_evolution_chaptered.mp4"
    writer = FFMpegWriter(
        fps=fps,
        bitrate=3800,
        metadata={"title": "Coding intelligence–price frontier (chaptered)"},
    )

    # Render ch7 hold still by running update once
    init()
    update(mid_ch7)
    ch7_png = OUT / "frontier_evolution_chaptered_ch7_hold.png"
    fig.savefig(str(ch7_png), dpi=DPI_ANIM)
    print(f"  ch7 mid-hold still → {ch7_png}")

    # Reset then save animation
    init()
    anim.save(str(mp4), writer=writer, dpi=DPI_ANIM)
    plt.close(fig)

    extras = {
        "ch7_png": ch7_png,
        "chapter_highlights": chapter_highlights,
        "mid_ch7_frame": mid_ch7,
    }
    return mp4, chapters, schedule, duration_s, extras


def extract_last_frame(mp4: Path) -> Path:
    png = OUT / "frontier_evolution_chaptered_last_frame.png"
    # -sseof seeks from end; grab one frame (true end-card frame)
    cmd = [
        "ffmpeg",
        "-y",
        "-sseof",
        "-0.15",
        "-i",
        str(mp4),
        "-frames:v",
        "1",
        "-q:v",
        "2",
        str(png),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return png


def write_chaptered_md(
    chapters: list[Chapter],
    schedule: list[FrameSpec],
    duration_s: float,
    fps: int,
    mp4: Path,
    png: Path,
    ch7_png: Path,
    chapter_highlights: dict,
):
    chapter_times: list[tuple[Chapter, float]] = []
    seen = set()
    for fi, spec in enumerate(schedule):
        if spec.chapter is not None and spec.chapter.index not in seen:
            seen.add(spec.chapter.index)
            chapter_times.append((spec.chapter, fi / fps))

    n_quiet = sum(1 for s in schedule if s.kind == "week" and not s.hold)
    n_hold = sum(1 for s in schedule if s.kind == "week" and s.hold)
    n_end = sum(1 for s in schedule if s.kind == "end")

    hold_desc = ", ".join(
        f"ch{c.index}={c.hold_seconds:.1f}s" for c in chapters
    )

    lines = [
        "# Chaptered frontier evolution movie",
        "",
        "Coding-only intelligence–price frontier with freezes at key shifts.",
        "",
        f"- **Primary:** `{mp4.name}`",
        f"- **Last frame:** `{png.name}` (end card; date HUD cleared)",
        f"- **Ch7 hold still:** `{ch7_png.name}`",
        f"- **Duration:** {duration_s:.2f}s @ {fps} fps ({len(schedule)} frames)",
        f"- **Pacing:** quiet weeks {QUIET_FRAMES}/{fps}s each "
        f"({n_quiet} frames); chapter holds variable ({hold_desc}; "
        f"{n_hold} frames across {len(chapters)} beats); "
        f"end card {END_CARD_FRAMES}/{fps}s ({n_end} frames)",
        f"- **Original (kept):** `frontier_evolution.mp4` (~12s rush)",
        "",
        "## Beats (chapter timestamps)",
        "",
    ]
    for ch, t0 in chapter_times:
        primary, secondary = chapter_highlights[ch.index]
        p_price = float(primary["blended_3_1_usd_per_mtok"])
        ptr = (
            f"pointer → {short_model(primary['model_name_arena'])} "
            f"score {primary['elo']:.0f} @ {format_price_label(p_price)}/MTok"
        )
        if secondary is not None:
            s_price = float(secondary["blended_3_1_usd_per_mtok"])
            ptr += (
                f"; faint peak → {short_model(secondary['model_name_arena'])} "
                f"@ {format_price_label(s_price)}"
            )
        lines.append(
            f"{ch.index}. **{t0:05.1f}s** ({ch.hold_seconds:.1f}s hold) — "
            f"`{ch.week.date()}` — {ch.caption}"
        )
        lines.append(f"   - highlight `{ch.highlight_mode}`"
                     + (f" ≤${ch.price_ceiling:g}" if ch.price_ceiling is not None else "")
                     + f": {ptr}")
    end_start = next(i for i, s in enumerate(schedule) if s.kind == "end") / fps
    lines += [
        "",
        f"**End card** from {end_start:05.1f}s — {END_CARD_LINE}",
        "",
        "## Design notes",
        "",
        "- Frontier-only polylines, log price axis, time-colored trail",
        "- During holds: older curves dimmed further; large ring + leader-line "
        "callout on the highlighted frontier point (model · score · price)",
        "- Quiet weeks: pointer hidden; peak summary in caption HUD only",
        "- End frames: `date_text` / `caption_text` cleared; centered end-card "
        "panel in header band (≈0.78–0.90) — no overlap with Aug 2026 HUD",
        "- Optional badge `n/N` during chapter freezes",
        "",
        "## Re-run",
        "",
        "```bash",
        "python -m venv .venv && source .venv/bin/activate  # or your env",
        "python media/coding/make_chaptered_movie.py",
        "```",
        "",
    ]
    (OUT / "CHAPTERED.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fps", type=int, default=FPS)
    args = ap.parse_args()

    print("Building chaptered frontier movie…")
    mp4, chapters, schedule, duration_s, extras = make_chaptered_movie(fps=args.fps)
    print(f"  wrote {mp4}  ({duration_s:.2f}s, {len(schedule)} frames @ {args.fps} fps)")
    for ch in chapters:
        primary, secondary = extras["chapter_highlights"][ch.index]
        print(
            f"  chapter {ch.index}/{len(chapters)}  {ch.week.date()}  hold={ch.hold_seconds:.1f}s  "
            f"mode={ch.highlight_mode}  → {short_model(primary['model_name_arena'])} "
            f"score {primary['elo']:.0f} @ ${primary['blended_3_1_usd_per_mtok']:.3g}"
        )

    png = extract_last_frame(mp4)
    print(f"  last frame → {png}")

    write_chaptered_md(
        chapters,
        schedule,
        duration_s,
        args.fps,
        mp4,
        png,
        extras["ch7_png"],
        extras["chapter_highlights"],
    )
    print(f"  note → {OUT / 'CHAPTERED.md'}")

    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(mp4),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    actual = float(probe.stdout.strip())
    print(f"  ffprobe duration: {actual:.2f}s")


if __name__ == "__main__":
    main()
