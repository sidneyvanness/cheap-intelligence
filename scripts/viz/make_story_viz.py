#!/usr/bin/env python3
"""Editorial Pareto-frontier story visuals — Arena Text *coding* score spine.

Outputs under media/coding/:
  frontier_evolution.png/.svg/.mp4   — weekly + accumulating color trail
  peak_capability.png                — raw peak + running-max envelope
  price_collapse.png                 — LOCF/interp across short gaps (dashed)
  migration.png                      — hero early→late up-left shift
  storyboard.png                     — multi-panel including migration
  README.md / INTERPRETATION.md

Usage:
  python -m venv .venv && source .venv/bin/activate  # or your env
  python scripts/viz/make_story_viz.py
  python scripts/viz/make_story_viz.py --skip-anim
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from matplotlib import colors as mcolors
from matplotlib.animation import FFMpegWriter, FuncAnimation
from matplotlib.patches import FancyArrowPatch

ROOT = Path(__file__).resolve().parents[2]  # cheap-intelligence/
EXPORT = ROOT / "data" / "export" / "coding"
OUT = ROOT / "media" / "coding"
OUT.mkdir(parents=True, exist_ok=True)
FONT_DIR = Path(__file__).resolve().parent / "fonts"

PRICE_FLOOR = 0.05  # log-axis floor for $0 models
DPI = 220
GAP_FILL_MAX_WEEKS = 8

# Warm editorial paper palette
BG = "#F7F5F2"
INK = "#1C1917"
MUTED = "#78716C"
GRID = "#E7E5E4"
ACCENT = "#0F766E"  # deep teal
PEAK_LINE = "#0F766E"
ENVELOPE = "#0F766E"
RAW_PEAK = "#A8A29E"
# Time colormap: older muted slate → mid indigo → latest vivid coral/rose
CMAP_COLORS = ["#A8A29E", "#94A3B8", "#64748B", "#6366F1", "#C026D3", "#E11D48"]
EARLY_CURVE = "#78716C"
LATE_CURVE = "#E11D48"

CURRENCY_FOOTNOTE = (
    "Arena Text/coding score (legacy files: Elo) × API prices through 2026-10-26. "
    "Free tiers shown at ≤$0.05; paid headline excludes them. "
    "Gemini 4 Carbon and MiMo v2.6 have no list price and are excluded."
)


def register_fonts() -> tuple[str, str]:
    """Register Inter / Inter Display; fall back to DejaVu."""
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
            "legend.fontsize": 9,
            "figure.dpi": 120,
            "savefig.dpi": DPI,
            "axes.grid": False,
            "axes.axisbelow": True,
        }
    )


def load_data():
    frontier = pd.read_csv(EXPORT / "01_arena_coding_elo_price_frontier_only.csv")
    frontier["week_start"] = pd.to_datetime(frontier["week_start"])
    frontier["price_plot"] = frontier["blended_3_1_usd_per_mtok"].clip(lower=PRICE_FLOOR)

    metrics = pd.read_csv(EXPORT / "02_weekly_frontier_story_metrics.csv")
    metrics["week_start"] = pd.to_datetime(metrics["week_start"])
    metrics = metrics.sort_values("week_start").reset_index(drop=True)
    metrics["running_max_elo"] = metrics["max_elo"].cummax()

    same = pd.read_csv(EXPORT / "03_same_coding_elo_cost_over_time.csv")
    same["week_start"] = pd.to_datetime(same["week_start"])
    same["anchor_week"] = pd.to_datetime(same["anchor_week"])
    same["price_plot"] = same["min_blended_price_for_anchor_elo"].clip(lower=PRICE_FLOOR)

    return frontier, metrics, same


def short_model(name: str, n: int = 20) -> str:
    s = str(name).replace("-2024-", "-").replace("-2025-", "-").replace("-2026-", "-")
    # friendlier display names for callouts
    pretty = {
        "claude-opus-5-high": "Claude Opus 5 high",
        "claude-opus-4-6-high": "Claude Opus 4.6 high",
        "claude-opus-5.5-high": "Claude Opus 5.5 high",
        "gpt-6-luna-max": "GPT-6 Luna max",
        "gemini-4-argon-high": "Gemini 4 Argon high",
        "Claude Haiku 5.5 (High)": "Claude Haiku 5.5 high",
        "step-3.5-flash": "Step 3.5 Flash",
        "deepseek-v4.1-flash-max": "DeepSeek V4.1 Flash max",
        "claude-3-sonnet-20240229": "Claude 3 Sonnet",
        "claude-3-haiku-20240307": "Claude 3 Haiku",
        "gpt-4-1106-preview": "GPT-4 Turbo (1106)",
        "gemini-2.5-pro": "Gemini 2.5 Pro",
        "gemini-3.7-flash-high": "Gemini 3.7 Flash high",
        "glm-5.3-flash": "GLM-5.3 Flash",
        "glm-4.7-flash": "GLM-4.7 Flash",
        "gpt-4-0314": "GPT-4 (0314)",
        "gpt-4o-2024-05-13": "GPT-4o",
        "chatgpt-4o-latest-20250326": "ChatGPT-4o latest",
    }
    if s in pretty:
        s = pretty[s]
    if len(s) <= n:
        return s
    return s[: n - 1] + "…"


def time_cmap():
    return mcolors.LinearSegmentedColormap.from_list("frontier_time", CMAP_COLORS)


def week_norm(weeks: pd.Series):
    t0 = weeks.min().toordinal()
    t1 = weeks.max().toordinal()
    if t1 == t0:
        return lambda w: 0.5
    return lambda w: (pd.Timestamp(w).toordinal() - t0) / (t1 - t0)


def frontier_xy(week_df: pd.DataFrame):
    """Ascending price polyline (cheap → expensive / often rising Elo)."""
    s = week_df.sort_values(["price_plot", "elo"], ascending=[True, True])
    return s["price_plot"].to_numpy(), s["elo"].to_numpy(), s


def sample_weeks(weeks: pd.DatetimeIndex, every_n: int = 4) -> list[pd.Timestamp]:
    weeks = pd.DatetimeIndex(sorted(weeks.unique()))
    sampled = list(weeks[::every_n])
    if weeks[0] not in sampled:
        sampled.insert(0, weeks[0])
    if weeks[-1] not in sampled:
        sampled.append(weeks[-1])
    return sampled


def format_price_axis(ax):
    ax.set_xscale("log")
    ax.set_xlim(PRICE_FLOOR * 0.85, 55)
    ticks = [0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 25]
    ax.set_xticks(ticks)
    ax.set_xticklabels(
        [r"≤\$0.05", r"\$0.10", r"\$0.25", r"\$0.50", r"\$1", r"\$2.50", r"\$5", r"\$10", r"\$25"]
    )
    ax.set_xlabel("Blended API price  ·  USD / 1M tokens  (log)", color=MUTED, labelpad=10)


def format_elo_axis(ax, ymin=1150, ymax=1560):
    ax.set_ylim(ymin, ymax)
    ax.set_ylabel("Arena Text/coding score", color=MUTED, labelpad=10)
    ax.yaxis.set_major_locator(mticker.MultipleLocator(50))
    ax.yaxis.set_minor_locator(mticker.MultipleLocator(25))


def add_title_block(fig, title: str, subtitle: str, y: float = 0.96):
    fig.text(
        0.06,
        y,
        title,
        fontsize=20,
        fontfamily=DISPLAY_FONT,
        fontweight="semibold",
        color=INK,
        va="top",
    )
    fig.text(
        0.06,
        y - 0.045,
        subtitle,
        fontsize=10.5,
        fontfamily=BODY_FONT,
        color=MUTED,
        va="top",
    )


def add_footnote(fig, text: str, y: float = 0.02):
    fig.text(
        0.06,
        y,
        text,
        fontsize=7.5,
        color=MUTED,
        fontfamily=BODY_FONT,
        va="bottom",
        wrap=True,
    )


def fill_price_gaps(sub: pd.DataFrame, max_gap_weeks: int = GAP_FILL_MAX_WEEKS) -> pd.DataFrame:
    """LOCF + linear interpolate across NaN runs of length ≤ max_gap_weeks.

    Returns a copy with columns:
      price_filled, is_imputed (True where original was NaN and we filled).
    Longer gaps are left NaN (line breaks).
    """
    out = sub.sort_values("week_start").copy().reset_index(drop=True)
    raw = out["min_blended_price_for_anchor_elo"].astype(float).to_numpy().copy()
    filled = raw.copy()
    imputed = np.zeros(len(raw), dtype=bool)

    n = len(raw)
    i = 0
    while i < n:
        if not np.isnan(raw[i]):
            i += 1
            continue
        # start of NaN run
        j = i
        while j < n and np.isnan(raw[j]):
            j += 1
        run_len = j - i
        # left value
        left = raw[i - 1] if i > 0 else np.nan
        right = raw[j] if j < n else np.nan
        if run_len <= max_gap_weeks and not np.isnan(left):
            if not np.isnan(right) and run_len >= 1:
                # linear interpolate in log-price space (more natural for collapse)
                left_log = np.log(max(left, PRICE_FLOOR))
                right_log = np.log(max(right, PRICE_FLOOR))
                for k, idx in enumerate(range(i, j)):
                    t = (k + 1) / (run_len + 1)
                    filled[idx] = np.exp(left_log + t * (right_log - left_log))
                    imputed[idx] = True
            else:
                # LOCF only (no right observation yet / trailing)
                for idx in range(i, j):
                    filled[idx] = left
                    imputed[idx] = True
        i = j

    out["price_filled"] = filled
    out["price_plot_filled"] = np.clip(filled, PRICE_FLOOR, None)
    out["is_imputed"] = imputed
    return out


def draw_price_series(ax, sub: pd.DataFrame, color: str, lw: float = 2.3, zorder: int = 3):
    """Draw continuous series with solid=observed, dashed=imputed segments."""
    filled = fill_price_gaps(sub)
    xs = filled["week_start"].to_numpy()
    ys = filled["price_plot_filled"].to_numpy()
    imp = filled["is_imputed"].to_numpy()
    obs = ~np.isnan(filled["min_blended_price_for_anchor_elo"].to_numpy(dtype=float))

    # Walk contiguous drawable points; style by whether segment touches imputed
    # A segment between i and i+1 is imputed if either endpoint is imputed
    # (and both have filled values).
    drawable = ~np.isnan(ys)
    i = 0
    n = len(filled)
    while i < n - 1:
        if not drawable[i]:
            i += 1
            continue
        # extend run of drawable
        j = i
        while j < n - 1 and drawable[j + 1]:
            j += 1
        # draw each edge in the run with appropriate style
        for k in range(i, j):
            is_imp_seg = bool(imp[k] or imp[k + 1])
            ax.plot(
                xs[k : k + 2],
                ys[k : k + 2],
                color=color,
                lw=lw * (0.85 if is_imp_seg else 1.0),
                ls="--" if is_imp_seg else "-",
                solid_capstyle="round",
                dash_capstyle="round",
                alpha=0.72 if is_imp_seg else 1.0,
                zorder=zorder,
            )
        i = j + 1

    # markers only on observed endpoints of the series
    obs_idx = np.where(obs & drawable)[0]
    if len(obs_idx):
        first, last = obs_idx[0], obs_idx[-1]
        ax.scatter(
            [xs[first]],
            [ys[first]],
            s=42,
            facecolors="white",
            edgecolors=color,
            linewidths=2,
            zorder=zorder + 2,
        )
        ax.scatter(
            [xs[last]],
            [ys[last]],
            s=42,
            color=color,
            zorder=zorder + 2,
            edgecolors="white",
            linewidths=0.8,
        )
    return filled


# ─────────────────────────────────────────────────────────────
# 1. Frontier evolution (static overlay)
# ─────────────────────────────────────────────────────────────
def make_frontier_evolution(frontier: pd.DataFrame, every_n: int = 3):
    weeks_all = pd.DatetimeIndex(sorted(frontier["week_start"].unique()))
    sampled = sample_weeks(weeks_all, every_n=every_n)
    cmap = time_cmap()
    norm_fn = week_norm(pd.Series(weeks_all))
    norm = mcolors.Normalize(
        vmin=mdates.date2num(weeks_all[0]), vmax=mdates.date2num(weeks_all[-1])
    )

    fig, ax = plt.subplots(figsize=(13.5, 8.4))
    fig.subplots_adjust(left=0.08, right=0.88, top=0.80, bottom=0.14)

    for y in range(1150, 1550, 50):
        ax.axhline(y, color=GRID, lw=0.6, zorder=0)

    for w in sampled:
        wdf = frontier[frontier["week_start"] == w]
        if wdf.empty:
            continue
        x, y, _ = frontier_xy(wdf)
        if len(x) < 1:
            continue
        t = norm_fn(w)
        color = cmap(t)
        lw = 1.0 + 1.8 * t
        alpha = 0.22 + 0.68 * t
        if len(x) == 1:
            ax.scatter(
                [x[0]],
                [y[0]],
                s=18 + 30 * t,
                color=color,
                alpha=alpha,
                zorder=2 + t,
                edgecolors="none",
            )
        else:
            ax.plot(x, y, color=color, lw=lw, alpha=alpha, solid_capstyle="round", zorder=2 + t)
            ax.scatter(
                x,
                y,
                s=7 + 12 * t,
                color=color,
                alpha=min(1, alpha + 0.12),
                zorder=3 + t,
                edgecolors="none",
            )

    # Smart callouts: place labels in empty margin above/beside, never on the polyline
    # Peak sits top-right of curve — push label UP into top margin with leader line.
    # Cheap sits bottom-left — push LEFT/DOWN into empty region.
    # Sparse era callouts. Latest peak uses axes-fraction placement in the empty
    # top-right margin so the label never sits on the polyline.
    callout_specs = [
        # target, peak_mode, peak_xytext_or_axes, cheap_xytext, include_cheap, peak_ha, cheap_ha
        # peak_mode: "offset" | "axes"
        ("2024-04-01", "offset", (18, 22), (14, -28), True, "left", "left"),
        ("2025-07-07", "offset", (-18, 30), (14, -34), True, "right", "left"),
        ("2026-08-31", "axes", (0.98, 0.22), (18, -40), True, "right", "left"),
    ]
    for target, peak_mode, peak_pos, cheap_off, include_cheap, peak_ha, cheap_ha in callout_specs:
        tw = pd.Timestamp(target)
        nearest = min(weeks_all, key=lambda w: abs((w - tw).days))
        wdf = frontier[frontier["week_start"] == nearest]
        if wdf.empty:
            continue
        peak = wdf.loc[wdf["elo"].idxmax()]
        cheap = wdf.loc[wdf["price_plot"].idxmin()]
        t = norm_fn(nearest)
        color = cmap(t)

        ax.scatter(
            [peak["price_plot"]],
            [peak["elo"]],
            s=55,
            facecolors="white",
            edgecolors=color,
            linewidths=2,
            zorder=10,
        )
        label = (
            f"{short_model(peak['model_name_arena'], 22)}\n"
            f"Score {peak['elo']:.0f} · \\${peak['blended_3_1_usd_per_mtok']:.2g}"
        )
        if peak_mode == "axes":
            # Leader from empty top-right margin down to the peak point
            ax.annotate(
                label,
                xy=(peak["price_plot"], peak["elo"]),
                xytext=peak_pos,
                xycoords='data',
                textcoords='axes fraction',
                fontsize=8.5,
                fontfamily=BODY_FONT,
                color=INK,
                ha=peak_ha,
                va="top",
                arrowprops=dict(
                    arrowstyle="-",
                    color=color,
                    lw=0.95,
                    shrinkA=2,
                    shrinkB=6,
                    connectionstyle="arc3,rad=-0.12",
                ),
                bbox=dict(boxstyle="round,pad=0.3", fc=BG, ec="#D6D3D1", lw=0.5, alpha=0.96),
                zorder=12,
            )
        else:
            ax.annotate(
                label,
                xy=(peak["price_plot"], peak["elo"]),
                xytext=peak_pos,
                textcoords="offset points",
                fontsize=8.5,
                fontfamily=BODY_FONT,
                color=INK,
                ha=peak_ha,
                va="bottom",
                arrowprops=dict(
                    arrowstyle="-",
                    color=color,
                    lw=0.9,
                    shrinkA=0,
                    shrinkB=5,
                    connectionstyle="arc3,rad=0.08",
                ),
                bbox=dict(boxstyle="round,pad=0.25", fc=BG, ec="none", alpha=0.92),
                zorder=11,
            )

        if include_cheap and cheap["model_name_arena"] != peak["model_name_arena"]:
            ax.scatter(
                [cheap["price_plot"]],
                [cheap["elo"]],
                s=40,
                facecolors="white",
                edgecolors=color,
                linewidths=1.5,
                zorder=10,
            )
            clabel = (
                f"{short_model(cheap['model_name_arena'], 16)}\n"
                f"\\${max(cheap['blended_3_1_usd_per_mtok'], 0):.3g}"
            )
            ax.annotate(
                clabel,
                xy=(cheap["price_plot"], cheap["elo"]),
                xytext=cheap_off,
                textcoords="offset points",
                fontsize=8,
                fontfamily=BODY_FONT,
                color=MUTED,
                ha=cheap_ha,
                va="top",
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.7, shrinkA=0, shrinkB=4),
                bbox=dict(boxstyle="round,pad=0.2", fc=BG, ec="none", alpha=0.9),
                zorder=11,
            )

    format_price_axis(ax)
    format_elo_axis(ax, ymax=1570)
    ax.spines["left"].set_color("#D6D3D1")
    ax.spines["bottom"].set_color("#D6D3D1")

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cax = fig.add_axes([0.90, 0.20, 0.018, 0.52])
    cb = fig.colorbar(sm, cax=cax)
    cb.set_ticks(
        [
            mdates.date2num(pd.Timestamp("2024-01-01")),
            mdates.date2num(pd.Timestamp("2025-01-01")),
            mdates.date2num(pd.Timestamp("2026-01-01")),
            mdates.date2num(weeks_all[-1]),
        ]
    )
    cb.set_ticklabels(["2024", "2025", "2026", weeks_all[-1].strftime("%b %Y")])
    cb.ax.tick_params(labelsize=8.5, colors=MUTED, length=3)
    cb.outline.set_visible(False)
    cax.set_title("Week", fontsize=8, color=MUTED, pad=8, fontfamily=BODY_FONT)

    add_title_block(
        fig,
        "The coding intelligence–price frontier, 2024–2026",
        "Pareto curves only · older weeks muted · latest vivid  ·  Arena Text/coding score vs blended $/MTok",
    )
    add_footnote(fig, CURRENCY_FOOTNOTE + r"  ·  free (\$0) floored at \$0.05 on log axis")

    png = OUT / "frontier_evolution.png"
    svg = OUT / "frontier_evolution.svg"
    fig.savefig(png, dpi=DPI, bbox_inches="tight", pad_inches=0.35)
    fig.savefig(svg, format="svg", bbox_inches="tight", pad_inches=0.35)
    plt.close(fig)
    return png


# ─────────────────────────────────────────────────────────────
# 2. Animation — EVERY week, accumulating muted trail
# ─────────────────────────────────────────────────────────────
def make_frontier_animation(frontier: pd.DataFrame, fps: int = 10):
    """Weekly frames. Older frontiers stay on screen in muted time-colors;
    newest week is vivid & thick so migration accumulates visually."""
    weeks = pd.DatetimeIndex(sorted(frontier["week_start"].unique()))
    if len(weeks) < 10:
        raise ValueError(f"expected many weekly frames, got {len(weeks)}")
    cmap = time_cmap()
    norm_fn = week_norm(pd.Series(weeks))

    # Precompute polylines
    cache: list[tuple[np.ndarray, np.ndarray, float]] = []
    for w in weeks:
        wdf = frontier[frontier["week_start"] == w]
        x, y, _ = frontier_xy(wdf)
        cache.append((x, y, norm_fn(w)))

    fig, ax = plt.subplots(figsize=(12.5, 7.6))
    # Keep axes below the HUD band so high-Elo/cheap curves never run under date text
    fig.subplots_adjust(left=0.09, right=0.96, top=0.68, bottom=0.13)

    format_price_axis(ax)
    format_elo_axis(ax, ymax=1570)
    for y in range(1150, 1550, 50):
        ax.axhline(y, color=GRID, lw=0.55, zorder=0)

    # One Line2D per week (history); we just toggle visibility / restyle current
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

    current_line = ax.plot([], [], color=CMAP_COLORS[-1], lw=3.0, zorder=8, solid_capstyle="round")[0]
    current_pts = ax.scatter(
        [], [], s=32, color=CMAP_COLORS[-1], zorder=9, edgecolors="white", linewidths=0.7
    )

    # Title + HUD live entirely ABOVE the axes (top=0.68). Left-of-plot overlays
    # collide with the latest high-Elo / low-price frontier trail.
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
        "Every week · older curves stay as a color trail · newest vivid",
        fontsize=10,
        color=MUTED,
    )
    date_text = fig.text(
        0.09,
        0.84,
        "",
        fontsize=20,
        fontfamily=DISPLAY_FONT,
        fontweight="semibold",
        color=INK,
        va="top",
        bbox=dict(boxstyle="round,pad=0.25", fc=BG, ec="none", alpha=0.98),
    )
    peak_text = fig.text(
        0.09,
        0.785,
        "",
        fontsize=11,
        fontfamily=BODY_FONT,
        color=MUTED,
        va="top",
        bbox=dict(boxstyle="round,pad=0.22", fc=BG, ec="none", alpha=0.98),
    )
    fig.text(
        0.09,
        0.035,
        CURRENCY_FOOTNOTE,
        fontsize=7,
        color=MUTED,
        fontfamily=BODY_FONT,
    )

    def init():
        current_line.set_data([], [])
        current_pts.set_offsets(np.empty((0, 2)))
        for ln in hist_lines:
            ln.set_alpha(0.0)
        return [current_line, current_pts]

    def update(i: int):
        # Reveal weeks 0..i as muted trail; week i is also drawn vivid on top
        for j in range(i + 1):
            x, y, t = cache[j]
            color = cmap(t)
            # Age relative to current frame: older → more muted
            age_frac = (i - j) / max(i, 1) if i > 0 else 0.0
            # Base alpha from time colormap position, then damp by age
            base = 0.12 + 0.40 * t
            alpha = base * (0.35 + 0.65 * (1.0 - 0.85 * age_frac))
            # Keep very old trails visible but quiet
            if j < i:
                hist_lines[j].set_alpha(min(0.55, max(0.08, alpha)))
                hist_lines[j].set_color(color)
                hist_lines[j].set_linewidth(0.8 + 0.7 * t)
                hist_lines[j].set_zorder(2 + t)
            else:
                # current week in history layer also faint under vivid overlay
                hist_lines[j].set_alpha(0.0)

        x, y, t = cache[i]
        color = cmap(t)
        if len(x) >= 2:
            current_line.set_data(x, y)
            current_line.set_color(color)
            current_pts.set_offsets(np.column_stack([x, y]))
            current_pts.set_facecolor(color)
        elif len(x) == 1:
            current_line.set_data([], [])
            current_pts.set_offsets(np.column_stack([x, y]))
            current_pts.set_facecolor(color)
        else:
            current_line.set_data([], [])
            current_pts.set_offsets(np.empty((0, 2)))

        w = weeks[i]
        wdf = frontier[frontier["week_start"] == w]
        peak = wdf.loc[wdf["elo"].idxmax()]
        date_text.set_text(w.strftime("%b %Y"))
        peak_text.set_text(
            f"Peak  {short_model(peak['model_name_arena'], 28)}"
            f"   ·   score {peak['elo']:.0f}"
            f"   ·   \\${peak['blended_3_1_usd_per_mtok']:.3g}/MTok"
        )
        return [current_line, current_pts]

    anim = FuncAnimation(
        fig, update, frames=len(weeks), init_func=init, interval=1000 / fps, blit=False
    )

    mp4 = OUT / "frontier_evolution.mp4"
    writer = FFMpegWriter(
        fps=fps,
        bitrate=3600,
        metadata={"title": "Intelligence–price frontier (weekly trail)"},
    )
    anim.save(str(mp4), writer=writer, dpi=160)
    plt.close(fig)
    return mp4


# ─────────────────────────────────────────────────────────────
# 3. Peak capability — raw ghost + running-max envelope
# ─────────────────────────────────────────────────────────────
def make_peak_capability(metrics: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(12.5, 6.6))
    fig.subplots_adjust(left=0.09, right=0.96, top=0.76, bottom=0.16)

    x = metrics["week_start"]
    y_raw = metrics["max_elo"]
    y_env = metrics["running_max_elo"]

    for yv in range(1150, 1550, 50):
        ax.axhline(yv, color=GRID, lw=0.55, zorder=0)

    # Soft fill under envelope
    ax.fill_between(x, 1150, y_env, color=ENVELOPE, alpha=0.07, zorder=1)

    # Raw peak Elo — faint ghost (shows Arena relative wiggles)
    ax.plot(
        x,
        y_raw,
        color=RAW_PEAK,
        lw=1.35,
        alpha=0.55,
        solid_capstyle="round",
        zorder=2,
        label="Weekly peak score (raw)",
    )

    # Running maximum — bold capability ceiling (monotonic)
    ax.plot(
        x,
        y_env,
        color=ENVELOPE,
        lw=2.6,
        solid_capstyle="round",
        zorder=4,
        label="Capability frontier ceiling  (running max)",
    )

    # Annotate mid-2025 Gemini plateau / relative dip
    gemini = metrics[(metrics["week_start"] >= "2025-06-20") & (metrics["week_start"] <= "2025-09-30")]
    if len(gemini):
        g_row = gemini.loc[gemini["max_elo"].idxmax()]
        ax.annotate(
            "Arena ratings are relative —\nsmall dips ≠ capability loss",
            xy=(g_row["week_start"], g_row["max_elo"]),
            xytext=(28, -48),
            textcoords="offset points",
            fontsize=8.2,
            color=MUTED,
            fontfamily=BODY_FONT,
            ha="left",
            va="top",
            arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8, shrinkB=4),
            bbox=dict(boxstyle="round,pad=0.35", fc=BG, ec="#D6D3D1", lw=0.6, alpha=0.95),
            zorder=7,
        )

    # Regime markers on the envelope
    highlights = [
        ("2024-04-01", "GPT-4 Turbo era"),
        ("2024-07-01", "GPT-4o"),
        ("2024-12-30", "o1"),
        ("2025-06-23", "Gemini 2.5"),
        ("2026-08-31", "Opus 4.6"),
    ]
    for d, label in highlights:
        tw = pd.Timestamp(d)
        idx = (metrics["week_start"] - tw).abs().idxmin()
        row = metrics.loc[idx]
        ax.scatter(
            [row["week_start"]],
            [row["running_max_elo"]],
            s=48,
            facecolors="white",
            edgecolors=ENVELOPE,
            linewidths=2,
            zorder=5,
        )
        ax.annotate(
            f"{label}\n{row['running_max_elo']:.0f}",
            xy=(row["week_start"], row["running_max_elo"]),
            xytext=(0, 14),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8.5,
            color=INK,
            fontfamily=BODY_FONT,
            zorder=6,
        )

    ax.set_ylim(1150, 1580)
    ax.set_xlim(x.min() - pd.Timedelta(days=14), x.max() + pd.Timedelta(days=21))
    ax.yaxis.set_major_locator(mticker.MultipleLocator(50))
    ax.set_ylabel("Max frontier score", color=MUTED, labelpad=10)
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.xaxis.set_minor_locator(mdates.MonthLocator())
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color("#D6D3D1")

    d_elo = y_env.iloc[-1] - y_raw.iloc[0]
    ax.text(
        0.98,
        0.10,
        f"+{d_elo:.0f} point ceiling from first week → latest",
        transform=ax.transAxes,
        ha="right",
        fontsize=10,
        color=ACCENT,
        fontfamily=BODY_FONT,
        fontweight="medium",
    )

    leg = ax.legend(loc="lower right", frameon=False, fontsize=8.5, bbox_to_anchor=(0.98, 0.18))
    for t in leg.get_texts():
        t.set_color(MUTED)

    add_title_block(
        fig,
        "Peak capability keeps rising",
        "Bold line = running maximum of weekly peak score (observed ceiling)  ·  faint = raw weekly peak",
        y=0.94,
    )
    add_footnote(
        fig,
        "Note: Arena score is relative (leaderboard drift). Mid-2025 wiggles around Gemini 2.5 Pro "
        "are rating noise, not true capability loss.  ·  " + CURRENCY_FOOTNOTE,
        y=0.018,
    )

    png = OUT / "peak_capability.png"
    fig.savefig(png, dpi=DPI, bbox_inches="tight", pad_inches=0.35)
    plt.close(fig)
    return png


# ─────────────────────────────────────────────────────────────
# 4. Price collapse — continuous with LOCF/dash for gaps
# ─────────────────────────────────────────────────────────────
def make_price_collapse(same: pd.DataFrame):
    prefer = [
        pd.Timestamp("2024-04-01"),
        pd.Timestamp("2024-04-08"),
        pd.Timestamp("2024-07-01"),
        pd.Timestamp("2024-12-30"),
    ]
    available = sorted(same["anchor_week"].unique())
    anchors = []
    for p in prefer:
        nearest = min(available, key=lambda a: abs((a - p).days))
        if nearest not in anchors:
            anchors.append(nearest)
    anchors = anchors[:4]

    palette = ["#0EA5E9", "#6366F1", "#D946EF", "#F43F5E"]

    fig, ax = plt.subplots(figsize=(12.5, 7.0))
    fig.subplots_adjust(left=0.10, right=0.78, top=0.76, bottom=0.16)

    for yv in [0.1, 0.25, 0.5, 1, 2.5, 5, 10, 25]:
        ax.axhline(yv, color=GRID, lw=0.55, zorder=0)

    collapse_notes = []
    for i, aw in enumerate(anchors):
        sub = same[same["anchor_week"] == aw].sort_values("week_start")
        elo = sub["anchor_max_elo"].iloc[0]
        color = palette[i]
        filled = draw_price_series(ax, sub, color=color, lw=2.3, zorder=3)

        # collapse factor from first observed → last observed
        obs = filled[~filled["min_blended_price_for_anchor_elo"].isna()]
        start_p = float(obs["min_blended_price_for_anchor_elo"].iloc[0])
        end_p = float(obs["min_blended_price_for_anchor_elo"].iloc[-1])
        factor = start_p / end_p if end_p > 0 else float("inf")
        collapse_notes.append((aw, elo, start_p, end_p, factor, color, obs))

        ax.plot([], [], color=color, lw=2.2, label=f"Score ≥ {elo:.0f}  (peak of {aw.strftime('%b %Y')})")

    # Callout box — collapse factors live here (avoids end-of-curve label pileup)
    lines = ["Orders-of-magnitude collapse:"]
    for aw, elo, p0, p1, fac, color, _ in collapse_notes:
        if fac >= 40:
            lines.append(f"  Score ≥{elo:.0f}:  \\${p0:.3g} → \\${p1:.3g}   (~{fac:.0f}×)")
        else:
            drop = 100 * (1 - p1 / p0) if p0 > 0 else 0
            lines.append(f"  Score ≥{elo:.0f}:  \\${p0:.3g} → \\${p1:.3g}   (−{drop:.0f}%)")
    ax.text(
        0.03,
        0.05,
        "\n".join(lines),
        transform=ax.transAxes,
        fontsize=8.0,
        color=INK,
        fontfamily=BODY_FONT,
        va="bottom",
        ha="left",
        bbox=dict(boxstyle="round,pad=0.45", fc="#FFFFFF", ec="#D6D3D1", lw=0.7, alpha=0.92),
        zorder=8,
    )

    ax.set_yscale("log")
    ax.set_ylim(PRICE_FLOOR * 0.9, 50)
    ax.set_ylabel(r"Cheapest blended \$/MTok clearing that score  (log)", color=MUTED, labelpad=10)
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: f"\\${v:g}" if v >= 0.1 else f"\\${v:.2f}")
    )
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color("#D6D3D1")

    leg = ax.legend(
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        frameon=False,
        fontsize=9,
        title="Quality anchor",
        title_fontsize=9,
    )
    leg.get_title().set_color(MUTED)

    # dashed = imputed legend hint
    ax.plot([], [], color=MUTED, lw=1.4, ls="--", alpha=0.7, label="_imputed")
    fig.text(
        0.80,
        0.42,
        "Solid = observed\nDashed = filled gap\n(≤8 weeks, LOCF/interp)",
        fontsize=7.5,
        color=MUTED,
        fontfamily=BODY_FONT,
        va="top",
    )

    add_title_block(
        fig,
        "Price collapse at a fixed score threshold",
        "Cost to clear an earlier week’s peak published score — falling dollars  (log scale)",
        y=0.94,
    )
    add_footnote(
        fig,
        CURRENCY_FOOTNOTE
        + r"  ·  \$0 floored at \$0.05  ·  dashed segments = gaps with no qualifying model (filled ≤8 wks)",
        y=0.018,
    )

    png = OUT / "price_collapse.png"
    fig.savefig(png, dpi=DPI, bbox_inches="tight", pad_inches=0.35)
    plt.close(fig)
    return png


# ─────────────────────────────────────────────────────────────
# 5. Migration hero — bottom-right → top-left
# ─────────────────────────────────────────────────────────────
def make_migration(frontier: pd.DataFrame):
    weeks_all = pd.DatetimeIndex(sorted(frontier["week_start"].unique()))
    cmap = time_cmap()
    norm_fn = week_norm(pd.Series(weeks_all))

    early_w = weeks_all[0]
    late_w = weeks_all[-1]

    fig, ax = plt.subplots(figsize=(13.5, 8.2))
    fig.subplots_adjust(left=0.08, right=0.96, top=0.80, bottom=0.14)

    for y in range(1150, 1550, 50):
        ax.axhline(y, color=GRID, lw=0.55, zorder=0)

    # Ghost monthly trails (every ~4 weeks), same colormap — soft history
    ghosts = sample_weeks(weeks_all, every_n=4)
    for w in ghosts:
        if w in (early_w, late_w):
            continue
        wdf = frontier[frontier["week_start"] == w]
        x, y, _ = frontier_xy(wdf)
        if len(x) < 2:
            continue
        t = norm_fn(w)
        ax.plot(
            x,
            y,
            color=cmap(t),
            lw=1.0 + 0.8 * t,
            alpha=0.14 + 0.22 * t,
            solid_capstyle="round",
            zorder=1 + t,
        )

    # Early frontier — bold muted
    edf = frontier[frontier["week_start"] == early_w]
    ex, ey, _ = frontier_xy(edf)
    ax.plot(
        ex,
        ey,
        color=EARLY_CURVE,
        lw=3.2,
        solid_capstyle="round",
        zorder=5,
        label=f"Early  ·  {early_w.strftime('%b %Y')}",
        alpha=0.9,
    )
    ax.scatter(ex, ey, s=55, facecolors="white", edgecolors=EARLY_CURVE, linewidths=2.0, zorder=6)

    # Latest frontier — vivid rose
    ldf = frontier[frontier["week_start"] == late_w]
    lx, ly, _ = frontier_xy(ldf)
    ax.plot(
        lx,
        ly,
        color=LATE_CURVE,
        lw=3.4,
        solid_capstyle="round",
        zorder=7,
        label=f"Latest  ·  {late_w.strftime('%b %Y')}",
    )
    ax.scatter(lx, ly, s=60, facecolors="white", edgecolors=LATE_CURVE, linewidths=2.2, zorder=8)

    # Centroids for motion arrow (geometric mean price × mean Elo)
    def centroid(x, y):
        return (float(np.exp(np.mean(np.log(np.clip(x, PRICE_FLOOR, None))))), float(np.mean(y)))

    c0 = centroid(ex, ey) if len(ex) else (20.0, 1125.0)
    c1 = centroid(lx, ly) if len(lx) else (1.0, 1450.0)

    arrow = FancyArrowPatch(
        c0,
        c1,
        transform=ax.transData,
        arrowstyle="-|>",
        mutation_scale=22,
        lw=2.4,
        color="#BE123C",
        alpha=0.85,
        connectionstyle="arc3,rad=-0.18",
        zorder=9,
    )
    ax.add_patch(arrow)

    # Mid-arrow caption
    mid = (
        np.exp(0.45 * np.log(c0[0]) + 0.55 * np.log(c1[0])),
        0.45 * c0[1] + 0.55 * c1[1],
    )
    ax.text(
        mid[0],
        mid[1] + 28,
        "migration\nup & left",
        fontsize=11,
        fontfamily=DISPLAY_FONT,
        fontweight="semibold",
        color="#BE123C",
        ha="center",
        va="bottom",
        zorder=10,
    )

    # Peak / cheap labels for early & late — placed in empty margins
    e_peak = edf.loc[edf["elo"].idxmax()]
    l_peak = ldf.loc[ldf["elo"].idxmax()]
    l_cheap = ldf.loc[ldf["price_plot"].idxmin()]

    ax.annotate(
        f"{short_model(e_peak['model_name_arena'], 18)}\n"
        f"Score {e_peak['elo']:.0f} · \\${e_peak['blended_3_1_usd_per_mtok']:.2g}",
        xy=(e_peak["price_plot"], e_peak["elo"]),
        xytext=(22, -36),
        textcoords="offset points",
        fontsize=8.5,
        color=EARLY_CURVE,
        ha="left",
        va="top",
        arrowprops=dict(arrowstyle="-", color=EARLY_CURVE, lw=0.8),
        bbox=dict(boxstyle="round,pad=0.25", fc=BG, ec="none", alpha=0.92),
        zorder=11,
    )
    # Latest peak — empty top-right margin (never on the polyline)
    ax.annotate(
        f"{short_model(l_peak['model_name_arena'], 20)}\n"
        f"Score {l_peak['elo']:.0f} · \\${l_peak['blended_3_1_usd_per_mtok']:.2g}",
        xy=(l_peak["price_plot"], l_peak["elo"]),
        xytext=(0.93, 0.96),
        xycoords='data',
        textcoords='axes fraction',
        fontsize=8.5,
        color=LATE_CURVE,
        ha="right",
        va="top",
        fontweight="medium",
        arrowprops=dict(
            arrowstyle="-",
            color=LATE_CURVE,
            lw=0.95,
            shrinkA=2,
            shrinkB=6,
            connectionstyle="arc3,rad=-0.12",
        ),
        bbox=dict(boxstyle="round,pad=0.3", fc=BG, ec="#D6D3D1", lw=0.5, alpha=0.96),
        zorder=12,
    )
    ax.annotate(
        f"{short_model(l_cheap['model_name_arena'], 16)}\n\\${max(l_cheap['blended_3_1_usd_per_mtok'], 0):.3g}",
        xy=(l_cheap["price_plot"], l_cheap["elo"]),
        xytext=(14, -28),
        textcoords="offset points",
        fontsize=8,
        color=MUTED,
        ha="left",
        va="top",
        arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.7),
        bbox=dict(boxstyle="round,pad=0.2", fc=BG, ec="none", alpha=0.9),
        zorder=11,
    )

    # Corner story captions
    ax.text(
        0.97,
        0.08,
        "THEN\nexpensive · lower score",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=9,
        color=EARLY_CURVE,
        fontfamily=BODY_FONT,
        fontweight="medium",
        linespacing=1.35,
    )
    ax.text(
        0.04,
        0.92,
        "NOW\ncheaper · higher score",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9,
        color=LATE_CURVE,
        fontfamily=BODY_FONT,
        fontweight="medium",
        linespacing=1.35,
    )

    format_price_axis(ax)
    format_elo_axis(ax, ymax=1570)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color("#D6D3D1")

    leg = ax.legend(loc="lower right", frameon=False, fontsize=10, bbox_to_anchor=(0.98, 0.18))
    for t in leg.get_texts():
        t.set_color(INK)

    add_title_block(
        fig,
        "The frontier migrated up and left",
        "What happened: peak intelligence rose while the whole Pareto curve stretched into cheaper territory",
    )
    add_footnote(fig, CURRENCY_FOOTNOTE + "  ·  ghost trails = monthly samples along the way")

    png = OUT / "migration.png"
    fig.savefig(png, dpi=DPI, bbox_inches="tight", pad_inches=0.35)
    plt.close(fig)
    return png


# ─────────────────────────────────────────────────────────────
# 6. Storyboard — includes migration hero
# ─────────────────────────────────────────────────────────────
def make_storyboard(frontier: pd.DataFrame, metrics: pd.DataFrame, same: pd.DataFrame):
    fig = plt.figure(figsize=(16.0, 11.0))
    gs = fig.add_gridspec(
        2,
        2,
        width_ratios=[1.3, 1],
        height_ratios=[1.2, 1],
        left=0.06,
        right=0.97,
        top=0.86,
        bottom=0.09,
        wspace=0.20,
        hspace=0.30,
    )

    weeks_all = pd.DatetimeIndex(sorted(frontier["week_start"].unique()))
    cmap = time_cmap()
    norm_fn = week_norm(pd.Series(weeks_all))
    early_w, late_w = weeks_all[0], weeks_all[-1]

    # --- Panel A: Migration hero (early vs late + ghosts) ---
    ax0 = fig.add_subplot(gs[:, 0])
    for y in range(1150, 1550, 50):
        ax0.axhline(y, color=GRID, lw=0.5, zorder=0)

    for w in sample_weeks(weeks_all, every_n=5):
        if w in (early_w, late_w):
            continue
        wdf = frontier[frontier["week_start"] == w]
        x, y, _ = frontier_xy(wdf)
        t = norm_fn(w)
        if len(x) >= 2:
            ax0.plot(x, y, color=cmap(t), lw=0.9 + 0.7 * t, alpha=0.16 + 0.25 * t, solid_capstyle="round")

    edf = frontier[frontier["week_start"] == early_w]
    ex, ey, _ = frontier_xy(edf)
    ax0.plot(ex, ey, color=EARLY_CURVE, lw=2.8, zorder=5, solid_capstyle="round", label=early_w.strftime("%b %Y"))
    ldf = frontier[frontier["week_start"] == late_w]
    lx, ly, _ = frontier_xy(ldf)
    ax0.plot(lx, ly, color=LATE_CURVE, lw=3.0, zorder=6, solid_capstyle="round", label=late_w.strftime("%b %Y"))
    ax0.scatter(lx, ly, color=LATE_CURVE, s=20, zorder=7, edgecolors="white", linewidths=0.5)

    # Arrow
    def centroid(x, y):
        return (float(np.exp(np.mean(np.log(np.clip(x, PRICE_FLOOR, None))))), float(np.mean(y)))

    c0 = centroid(ex, ey)
    c1 = centroid(lx, ly)
    ax0.add_patch(
        FancyArrowPatch(
            c0,
            c1,
            transform=ax0.transData,
            arrowstyle="-|>",
            mutation_scale=18,
            lw=2.0,
            color="#BE123C",
            alpha=0.8,
            connectionstyle="arc3,rad=-0.18",
            zorder=8,
        )
    )
    ax0.text(
        np.exp(0.5 * (np.log(c0[0]) + np.log(c1[0]))),
        0.5 * (c0[1] + c1[1]) + 22,
        "up & left",
        fontsize=10,
        color="#BE123C",
        fontfamily=DISPLAY_FONT,
        fontweight="semibold",
        ha="center",
    )

    # Latest peak label in empty top-right margin
    l_peak = ldf.loc[ldf["elo"].idxmax()]
    ax0.annotate(
        short_model(l_peak["model_name_arena"], 18),
        xy=(l_peak["price_plot"], l_peak["elo"]),
        xytext=(0.96, 0.96),
        xycoords='data',
        textcoords='axes fraction',
        fontsize=7.5,
        color=LATE_CURVE,
        ha="right",
        va="top",
        arrowprops=dict(
            arrowstyle="-",
            color=LATE_CURVE,
            lw=0.7,
            shrinkA=1,
            shrinkB=5,
            connectionstyle="arc3,rad=-0.1",
        ),
        bbox=dict(boxstyle="round,pad=0.2", fc=BG, ec="none", alpha=0.95),
        zorder=9,
    )

    format_price_axis(ax0)
    format_elo_axis(ax0, ymax=1570)
    ax0.legend(frameon=False, fontsize=9, loc="lower right")
    ax0.set_title(
        "A  ·  Migration: bottom-right → top-left",
        loc="left",
        fontsize=12,
        fontfamily=DISPLAY_FONT,
        pad=10,
    )

    # --- Panel B: peak capability with envelope ---
    ax1 = fig.add_subplot(gs[0, 1])
    ax1.fill_between(metrics["week_start"], 1150, metrics["running_max_elo"], color=PEAK_LINE, alpha=0.07)
    ax1.plot(metrics["week_start"], metrics["max_elo"], color=RAW_PEAK, lw=1.1, alpha=0.5)
    ax1.plot(metrics["week_start"], metrics["running_max_elo"], color=PEAK_LINE, lw=2.2)
    ax1.set_ylim(1150, 1580)
    ax1.yaxis.set_major_locator(mticker.MultipleLocator(100))
    ax1.xaxis.set_major_locator(mdates.YearLocator())
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    for spine in ("left", "bottom"):
        ax1.spines[spine].set_color("#D6D3D1")
    for yv in range(1200, 1500, 100):
        ax1.axhline(yv, color=GRID, lw=0.5, zorder=0)
    ax1.set_ylabel("Max Text/coding score", color=MUTED, fontsize=9)
    ax1.set_title(
        "B  ·  Peak Text/coding score ceiling (running max)",
        loc="left",
        fontsize=12,
        fontfamily=DISPLAY_FONT,
        pad=10,
    )
    d_elo = metrics["running_max_elo"].iloc[-1] - metrics["max_elo"].iloc[0]
    ax1.text(
        0.97,
        0.12,
        f"+{d_elo:.0f}",
        transform=ax1.transAxes,
        ha="right",
        fontsize=18,
        fontfamily=DISPLAY_FONT,
        fontweight="semibold",
        color=ACCENT,
    )
    ax1.text(
        0.03,
        0.95,
        "faint = raw · bold = ceiling",
        transform=ax1.transAxes,
        fontsize=7.5,
        color=MUTED,
        va="top",
    )

    # --- Panel C: price collapse (2 early anchors, with LOCF) ---
    ax2 = fig.add_subplot(gs[1, 1])
    prefer = [pd.Timestamp("2024-04-01"), pd.Timestamp("2024-12-30")]
    available = sorted(same["anchor_week"].unique())
    palette = ["#0EA5E9", "#F43F5E"]
    for i, p in enumerate(prefer):
        aw = min(available, key=lambda a: abs((a - p).days))
        sub = same[same["anchor_week"] == aw].sort_values("week_start")
        elo = sub["anchor_max_elo"].iloc[0]
        filled = draw_price_series(ax2, sub, color=palette[i], lw=2.0, zorder=3)
        obs = filled[~filled["min_blended_price_for_anchor_elo"].isna()]
        p0 = float(obs["min_blended_price_for_anchor_elo"].iloc[0])
        p1 = float(obs["min_blended_price_for_anchor_elo"].iloc[-1])
        fac = p0 / p1 if p1 > 0 else 0
        ax2.plot([], [], color=palette[i], lw=2.0, label=f"Score ≥ {elo:.0f}  (~{fac:.0f}×)")
    ax2.set_yscale("log")
    ax2.set_ylim(PRICE_FLOOR * 0.9, 50)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"\\${v:g}"))
    ax2.xaxis.set_major_locator(mdates.YearLocator())
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    for spine in ("left", "bottom"):
        ax2.spines[spine].set_color("#D6D3D1")
    ax2.legend(frameon=False, fontsize=8.5, loc="upper right")
    ax2.set_ylabel(r"\$/MTok (log)", color=MUTED, fontsize=9)
    ax2.set_title(
        "C  ·  Fixed-score cost collapses",
        loc="left",
        fontsize=12,
        fontfamily=DISPLAY_FONT,
        pad=10,
    )

    fig.text(
        0.06,
        0.95,
        "Three frames of the same story",
        fontsize=22,
        fontfamily=DISPLAY_FONT,
        fontweight="semibold",
        color=INK,
        va="top",
    )
    fig.text(
        0.06,
        0.905,
        "Migration up-left · rising score ceiling · collapsing price at a fixed score threshold",
        fontsize=11,
        color=MUTED,
    )
    fig.text(
        0.06,
        0.025,
        CURRENCY_FOOTNOTE,
        fontsize=7.5,
        color=MUTED,
    )

    png = OUT / "storyboard.png"
    fig.savefig(png, dpi=DPI, bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)
    return png


def write_docs(frontier, metrics, same):
    weeks = sorted(frontier["week_start"].unique())
    first, last = weeks[0], weeks[-1]
    peak0 = metrics.iloc[0]
    peak1 = metrics.iloc[-1]
    env1 = metrics["running_max_elo"].iloc[-1]

    collapse_lines = []
    for aw in [
        pd.Timestamp("2024-04-01"),
        pd.Timestamp("2024-04-08"),
        pd.Timestamp("2024-07-01"),
        pd.Timestamp("2024-12-30"),
    ]:
        available = sorted(same["anchor_week"].unique())
        aw = min(available, key=lambda a: abs((a - aw).days))
        sub = same[same["anchor_week"] == aw].sort_values("week_start")
        filled = fill_price_gaps(sub)
        obs = filled[~filled["min_blended_price_for_anchor_elo"].isna()]
        elo = obs["anchor_max_elo"].iloc[0]
        p0 = float(obs["min_blended_price_for_anchor_elo"].iloc[0])
        p1 = float(obs["min_blended_price_for_anchor_elo"].iloc[-1])
        fac = p0 / p1 if p1 else 0
        drop = 100 * (1 - p1 / p0) if p0 else 0
        collapse_lines.append(
            f"- Peak score of {aw.date()} (~{elo:.0f}): ${p0:g} → ${p1:g}/MTok "
            f"(−{drop:.0f}%, ~{fac:.0f}× cheaper)"
        )

    readme = f"""# Story visuals — coding score × price frontier

Editorial charts for Arena Text **coding** score. Legacy files and some labels use “Elo,” though post-January 2024 ratings use Bradley–Terry estimation. **Frontier polylines only** — no scatter-cloud spaghetti.

## Deliverables

| File | Story beat |
|------|------------|
| `frontier_evolution.png` (+ `.svg`) | Many weekly frontiers overlaid, colored by date |
| `frontier_evolution.mp4` | **Every week** (coding panel frames); older curves stay as a muted color trail |
| `peak_capability.png` | Raw peak score (faint) + **running-max envelope** (bold ceiling) |
| `price_collapse.png` | Same-score-threshold cost; gaps ≤8 wks filled (dashed = imputed) |
| `migration.png` | **Hero:** early vs latest frontier, up-left migration |
| `storyboard.png` | One-pager: migration + peak ceiling + price collapse |

## Design notes (v2)

- **Typography:** Inter / Inter Display (bundled under `fonts/`); warm paper background `#F7F5F2`.
- **Color:** continuous time colormap (muted stone → indigo → vivid rose). Older frontiers sit quiet; latest is vivid and thicker.
- **Animation trail:** history **accumulates** — prior weekly curves remain on screen in muted time-colors; only the newest week is vivid.
- **Labels:** sparse callouts with leader lines + paper-backed text in empty margins (no polyline collisions; Opus 5 peak sits above the curve).
- **Peak chart:** raw weekly maximum score as ghost; bold line is the monotonic **running maximum** (“capability frontier ceiling”). Mid-2025 Arena wiggles annotated as relative rating noise.
- **Price collapse:** NaN weeks (no qualifying model) filled with LOCF / log-linear interp when the gap is ≤8 weeks; imputed segments drawn **dashed**.
- **Omitted models:** Gemini 4 Carbon (#1 on the 2026-10-28 board; announced at $2/$10 introductory but not yet on Google's pricing page) and MiMo v2.6 Pro / Flash (Xiaomi) are rated but have no list price in our sources, so they are excluded from the price axis. We do **not** invent or merge scores.
- **Encoding:** log price (x), Text/coding score (y). Free ($0) models are explicit and floored at `$0.05` only for log display.
- **Retina:** PNGs at 220 dpi.

## Rebuild

```bash
python -m venv .venv && source .venv/bin/activate  # or your env
python scripts/viz/make_story_viz.py
python scripts/viz/make_story_viz.py --skip-anim   # static only
python scripts/viz/make_story_viz.py --every-n 3 --fps 10
```

Data inputs: `export/coding/01_*.csv`, `02_*.csv`, `03_*.csv`.
"""
    (OUT / "README.md").write_text(readme)

    interp = f"""# Interpretation — coding frontier story

**What changed ( {first.date()} → {last.date()}, {len(weeks)} weeks ):**

1. **Shape / migration.** The score–price Pareto frontier marches **up and left**: a higher peak score and a longer cheap tail. Early weeks are short, expensive stubs (GPT-4-class). Later weeks stretch from sub-$0.10 flash/open models up to ~{peak1['max_elo']:.0f} premium peaks. See `migration.png` for the clearest before→after.

2. **Peak capability (ceiling, not wiggles).** Raw weekly maximum score rose from **{peak0['max_elo']:.0f}** (`{peak0['peak_model']}`) to **{peak1['max_elo']:.0f}** (`{peak1['peak_model']}`). The **running maximum** (capability frontier ceiling) ends at **{env1:.0f}** — about **+{env1 - peak0['max_elo']:.0f} points**.

   **Why the mid-2025 dip?** Around the Gemini 2.5 Pro plateau, the Arena score wobbles a few points week to week. **Arena ratings are relative** (leaderboard composition drifts); small dips are not true capability loss. The bold envelope line tells the real story: the observed ceiling does not go backwards.

3. **Price collapse (fixed published score).** Holding an earlier peak score threshold fixed, the cheapest blended $/MTok falls by roughly two orders of magnitude on early anchors:
{chr(10).join(collapse_lines)}

   Weeks with no qualifying matched model appear as NaNs in the export; charts fill gaps ≤8 weeks (LOCF / log-linear) and draw those segments dashed.

**How to read the charts.** Ignore dominated points — only the frontier curve matters. Color = time. In the MP4, older weekly curves **stay on screen** as a muted trail so you watch the migration accumulate.

**Caveats / omissions.** Arena scores are relative and the estimator/model pool changed over time. Panel ends {last.date()}. **Gemini 4 Argon (introductory $2/$10 through Nov 30), Claude Sonnet/Haiku 5.5, GPT-6.1 Sol, Muse Wonder and Step 3.5 Flash/Step 5 Preview enter the panel between weeks 2026-09-28 and 2026-10-26. Gemini 4 Carbon (#1 on the 2026-10-28 board) and MiMo v2.6 Pro have no list price and are excluded.** Text/coding and WebDev scores are not interchangeable. Free ($0) prices are explicit and floored at $0.05 only on log axes; the August 31 GLM-5.3 Flash rate was promotional.
"""
    (OUT / "INTERPRETATION.md").write_text(interp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-anim", action="store_true")
    ap.add_argument("--every-n", type=int, default=3, help="Sample every N weeks for static overlay")
    ap.add_argument("--fps", type=int, default=10)
    args = ap.parse_args()

    style_rc()
    frontier, metrics, same = load_data()
    OUT.mkdir(parents=True, exist_ok=True)

    print(f"Fonts: body={BODY_FONT}, display={DISPLAY_FONT}")
    print(f"Weeks: {frontier['week_start'].nunique()}")

    p1 = make_frontier_evolution(frontier, every_n=args.every_n)
    print("wrote", p1)

    p_mig = make_migration(frontier)
    print("wrote", p_mig)

    p3 = make_peak_capability(metrics)
    print("wrote", p3)

    p4 = make_price_collapse(same)
    print("wrote", p4)

    p5 = make_storyboard(frontier, metrics, same)
    print("wrote", p5)

    write_docs(frontier, metrics, same)
    print("wrote README.md + INTERPRETATION.md")

    if not args.skip_anim:
        p2 = make_frontier_animation(frontier, fps=args.fps)
        print("wrote", p2)
    else:
        print("skipped animation")


if __name__ == "__main__":
    main()
