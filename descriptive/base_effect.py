"""Brent: change over a year of the monthly average price, and what it becomes if the price stays flat.

Figure of page 3 of the application file. Descriptive, not pre-registered. Front-month futures (Yahoo `BZ=F`), monthly averages of
daily closes. Actual to the close of 20 November 2026; from 21 November every session is set at the
close of the 20th. A flat price is an assumption, written on the chart: it is the central scenario's.

    python3 base_effect.py > outputs/base_effect.txt
"""
import warnings

warnings.filterwarnings("ignore")

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf

CUT = pd.Timestamp("2026-11-20")
INK, TEAL, GREY, RED, LIGHT = "#1B2A41", "#0E7C7B", "#9AA5B1", "#B5382A", "#E6EAEE"
OUT = Path(__file__).resolve().parent / "figures" / "fig_base_effect.svg"

plt.rcParams.update({
    "font.family": ["Avenir Next", "Helvetica Neue", "DejaVu Sans"],
    "font.size": 7, "axes.edgecolor": GREY, "axes.linewidth": 0.6,
    "xtick.color": INK, "ytick.color": INK, "text.color": INK,
    "xtick.major.size": 0, "ytick.major.size": 0, "svg.fonttype": "none",
})

df = yf.download("BZ=F", start="2025-01-01", end="2026-11-21", auto_adjust=False, progress=False, threads=False)
df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
close = df["Close"].dropna().loc[:CUT]
flat = float(close.iloc[-1])
future = pd.bdate_range(CUT + pd.Timedelta(days=1), "2027-04-30")
path = pd.concat([close, pd.Series(flat, index=future)])
monthly = path.resample("M").mean()
yoy = (monthly / monthly.shift(12) - 1).dropna() * 100
yoy = yoy.loc["2026-01":"2027-04"]
actual = yoy.index <= pd.Timestamp("2026-10-31")

print("Brent close on 20 Nov 2026: %.2f" % flat)
print("monthly average:", {d.strftime("%Y-%m"): round(float(v), 1) for d, v in monthly.loc["2025-01":"2027-04"].items()})
print("change over a year, %:", {d.strftime("%Y-%m"): round(float(v)) for d, v in yoy.items()})

fig, ax = plt.subplots(figsize=(2.95, 1.5))
x = range(len(yoy))
colors = [TEAL if a else LIGHT for a in actual]
edges = [TEAL if a else GREY for a in actual]
ax.bar(x, yoy.values, width=0.72, color=colors, edgecolor=edges, linewidth=0.6)
ax.axhline(0, color=INK, linewidth=0.6)
ax.set_xticks(list(x))
ax.set_xticklabels([d.strftime("%b")[0] for d in yoy.index])
ax.set_yticks([-20, 0, 20, 40, 60])
ax.set_yticklabels(["−20%", "0", "+20%", "+40%", "+60%"])
ax.set_ylim(-24, 84)
ax.grid(axis="y", color=LIGHT, linewidth=0.5)
ax.set_axisbelow(True)
for side in ("top", "right", "left"):
    ax.spines[side].set_visible(False)
ax.spines["bottom"].set_visible(False)

months = list(yoy.index.strftime("%Y-%m"))


def label(month: str, dx: float, dy: float, ha: str, color: str) -> None:
    i = months.index(month)
    v = float(yoy.iloc[i])
    ax.text(i + dx, v + dy, f"{v:+.0f}%".replace("-", "−"), ha=ha, va="bottom" if dy > 0 else "top",
            fontsize=7, fontweight="bold", color=color)


label("2026-10", 0.36, 2.0, "right", TEAL)
label("2027-03", 0.30, -3.0, "right", RED)
label("2027-04", -0.30, -3.0, "left", RED)
first_proj = int(actual.sum())
ax.axvline(first_proj - 0.5, color=GREY, linewidth=0.6, linestyle=(0, (3, 2)))
ax.text(first_proj - 0.3, 82, f"if Brent stays at ${flat:.0f}", fontsize=6.6, color=INK, va="top", ha="left")
ax.set_xlim(-0.75, len(yoy) + 0.55)
for year, month in (("2026", "2026-01"), ("2027", "2027-01")):
    ax.text(months.index(month), -0.17, year, transform=ax.get_xaxis_transform(), fontsize=6.6, color=GREY, va="top", ha="center")
fig.subplots_adjust(left=0.13, right=0.995, top=0.985, bottom=0.265)
fig.savefig(OUT)
print("figure:", OUT.name)
