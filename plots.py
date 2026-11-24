"""Figures drawn from results/. Plotting only: numbers come from run_exhibit.py and post_review.py outputs.

The grey line is the constant mix with the same full-sample volatility as the rule (post-review comparison).
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results"
INK, TEAL, GREY, RED, LIGHT = "#1B2A41", "#0E7C7B", "#9AA5B1", "#B5382A", "#E6EAEE"

plt.rcParams.update({
    "font.family": ["Avenir Next", "Helvetica Neue", "DejaVu Sans"],
    "font.size": 7.5, "axes.edgecolor": GREY, "axes.linewidth": 0.6,
    "xtick.color": INK, "ytick.color": INK, "text.color": INK, "axes.labelcolor": INK,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.major.size": 2.5, "ytick.major.size": 0,
    "svg.fonttype": "none",
})


def fig_vol_cap() -> None:
    d = pd.read_csv(OUT / "daily_series.csv", index_col=0, parse_dates=True)
    res = json.loads((OUT / "results.json").read_text())
    post = pd.read_csv(OUT / "post_review_series.csv", index_col=0, parse_dates=True)
    pr_json = json.loads((OUT / "post_review.json").read_text())
    v = pd.DataFrame({"vol63_RULE": d["vol63_RULE"], "vol63_STATIC": post["vol63_SAME_RISK"]}).dropna() * 100
    w = d["w_rule"].loc[v.index] * 100
    w_static = pr_json["static_equal_volatility"]["equity_weight"] * 100

    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(6.89, 2.05), sharex=True,
                                  gridspec_kw={"height_ratios": [3.0, 1], "hspace": 0.14})
    ax.fill_between(v.index, v["vol63_STATIC"], color=LIGHT, linewidth=0)
    ax.plot(v.index, v["vol63_STATIC"], color=GREY, linewidth=0.7)
    ax.plot(v.index, v["vol63_RULE"], color=TEAL, linewidth=0.95)
    ax.axhline(10, color=RED, linewidth=0.8, linestyle=(0, (4, 2)))
    ax.text(v.index[25], 11.2, "Mandate cap 10%", color=RED, fontsize=7.5, va="bottom", fontweight="bold")
    ax.set_ylim(0, 37)
    ax.set_yticks([0, 10, 20, 30])
    ax.set_yticklabels(["0", "10%", "20%", "30%"])
    ax.grid(axis="y", color=LIGHT, linewidth=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)

    pr = res["portfolios"]["RULE"]
    ps = {"highest_63d_vol": pr_json["static_equal_volatility"]["highest_63d_vol"]}
    ds, dr = v["vol63_STATIC"].idxmax(), pd.Timestamp(pr["highest_63d_vol_date"])
    ax.annotate(f"Constant {w_static:.0f}/{100 - w_static:.0f} mix, same risk:\npeaks at {ps['highest_63d_vol'] * 100:.1f}%",
                xy=(ds, ps["highest_63d_vol"] * 100), xytext=(ds + pd.Timedelta(days=330), 31.5),
                fontsize=7.5, color="#5B6876", va="center",
                arrowprops={"arrowstyle": "-", "color": GREY, "linewidth": 0.5, "shrinkA": 1, "shrinkB": 2})
    ax.annotate(f"Rule peaks at {pr['highest_63d_vol'] * 100:.1f}%",
                xy=(dr, pr["highest_63d_vol"] * 100), xytext=(dr - pd.Timedelta(days=1500), 24.5),
                fontsize=7.5, color=TEAL, va="center", fontweight="bold",
                arrowprops={"arrowstyle": "-", "color": TEAL, "linewidth": 0.5, "shrinkA": 1, "shrinkB": 2})

    ax2.fill_between(w.index, 20, w, step="post", color=TEAL, alpha=0.22, linewidth=0)
    ax2.plot(w.index, w, color=TEAL, linewidth=0.55, drawstyle="steps-post")
    ax2.set_ylim(15, 85)
    ax2.set_yticks([20, 80])
    ax2.set_yticklabels(["20%", "80%"])
    ax2.axhline(20, color=GREY, linewidth=0.5)
    ax2.axhline(80, color=GREY, linewidth=0.5)
    ax2.text(v.index[25], 50, "Equity weight set by the rule", fontsize=7.5, color=INK, va="center",
             bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.2, "alpha": 0.85})
    for side in ("top", "right", "left"):
        ax2.spines[side].set_visible(False)
    ax2.xaxis.set_major_locator(mdates.YearLocator(2))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax2.set_xlim(v.index[0], v.index[-1])
    fig.subplots_adjust(left=0.047, right=0.997, top=0.985, bottom=0.095)
    fig.savefig(OUT / "fig_vol_cap.svg")
    fig.savefig(OUT / "fig_vol_cap.png", dpi=220)
    plt.close(fig)


if __name__ == "__main__":
    fig_vol_cap()
    print("figures written to", OUT)
