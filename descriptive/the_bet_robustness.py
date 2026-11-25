"""Checks on the bet of Logbook entry 005, added on 25 November 2026 after an outside review.

The review asked four questions that the_bet.py does not answer. This script answers them with the
same data and the same cut-off (close of 20 November 2026). It changes no figure of the_bet.py and
is not pre-registered.

1. Is the bet a complete account of the equity sleeve? No: the_bet.py measures two tilts, each
   against the index. Their active weights (-9.2 and +12.5 points of the sleeve) do not sum to zero,
   and the 2.5% of the index held in all utilities is treated as if it returned what our networks
   return. Here the sleeve is completed: the six at half their index weight, 15% in the networks, no
   other utility, and the rest held like the rest of the index. The index is split into the six,
   all utilities (iShares Global Utilities ETF, JXI, as a proxy) and what remains, whose return is
   the one that makes the three add up to the index over the period, at today's weights.
2. Six times what? 15% of the sleeve is compared with 2.5% for all utilities in the index. The
   eight network companies alone weigh much less: an upper bound is printed, from full market
   values (the index counts the free float only, which is smaller).
3. Does the result depend on weighting the six as the index does today? The same periods with the
   six equally weighted.
4. Is the sensitivity of the networks to the ten-year yield robust? The same regression with
   standard errors that allow for changing variance and serial correlation (Newey-West, Bartlett
   kernel, lag set by the usual rule), a 95% interval, the regression without the index, two
   sub-periods, and the estimate without the five weeks of largest yield moves. It is a historical
   association over four years, not a causal estimate and not a forecast.
5. Why these six? The basket is ours: the four largest buyers of AI computing capacity and their two
   largest suppliers in the index. It is not a ranking by size. Apple, the largest line of the
   index, and Tesla are left at index weight: their capital expenditure is printed beside the four's.

    python3 the_bet_robustness.py > outputs/the_bet_robustness.txt
"""
import io
import json
import subprocess
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import yfinance as yf

CUT = "2026-11-20"
SIX = {"NVDA": 5.2333, "MSFT": 4.0961, "GOOGL": 1.8284 + 1.4446, "AMZN": 2.5866, "AVGO": 1.6395, "META": 1.5020}   # % of URTH, as in the_bet.py
NETWORKS = {"EXC": "USD", "ED": "USD", "ES": "USD", "NG.L": "GBP", "TRN.MI": "EUR", "RED.MC": "EUR", "EOAN.DE": "EUR", "H.TO": "CAD"}
W_SIX, W_UTIL = sum(SIX.values()) / 100, 0.025
W_SIX_OURS, W_NET_OURS, SLEEVE = W_SIX / 2, 4.5 / 30, 0.30
A_SIX, A_NET = W_SIX_OURS - W_SIX, W_NET_OURS - W_UTIL
A_REST = (1 - W_SIX_OURS - W_NET_OURS) - (1 - W_SIX - W_UTIL)          # what funds the two tilts
PERIODS = {"2023": ("2022-12-30", "2023-12-29"), "2024": ("2023-12-29", "2024-12-31"), "2025": ("2024-12-31", "2025-12-31"),
           "2026 to 20 Nov": ("2025-12-31", CUT), "oil shock, 27 Feb - 31 Mar 2026": ("2026-02-27", "2026-03-31"),
           "between the two shocks, 31 Mar - 6 Oct 2026": ("2026-03-31", "2026-10-06"),
           "AI correction, 6 Oct - 20 Nov 2026": ("2026-10-06", CUT)}


def frame(ticker: str, start: str = "2014-12-20") -> pd.DataFrame:
    df = yf.download(ticker, start=start, end="2026-11-26", auto_adjust=False, progress=False, threads=False)
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    return df


def adj(ticker: str) -> pd.Series:
    return frame(ticker)["Adj Close"].dropna()


def total(series: pd.Series, a: str, b: str) -> float:
    return float((1 + series.loc[a:b].iloc[1:]).prod() - 1)


fx = {"GBP": adj("GBPUSD=X"), "EUR": adj("EURUSD=X"), "CAD": adj("CADUSD=X")}
px = {t: adj(t) for t in list(SIX) + ["URTH", "JXI"]}
for t, ccy in NETWORKS.items():
    s = adj(t)
    px[t] = s if ccy == "USD" else (s * fx[ccy].reindex(s.index).ffill()).dropna()
ret = pd.DataFrame(px).ffill().pct_change()
w6 = pd.Series(SIX) / sum(SIX.values())
six, six_equal = (ret[list(SIX)] * w6).sum(axis=1), ret[list(SIX)].mean(axis=1)
net, idx, util = ret[list(NETWORKS)].mean(axis=1), ret["URTH"], ret["JXI"]

# the returns must be those of the_bet.py, or the comparison below means nothing
saved = json.loads((Path(__file__).parent / "outputs" / "the_bet.json").read_text())["periods"]
for name, (a, b) in PERIODS.items():
    for key, series in (("six_%", six), ("networks_%", net), ("index_%", idx)):
        assert abs(total(series, a, b) * 100 - saved[name][key]) < 0.06, (name, key, total(series, a, b) * 100, saved[name][key])
print("period returns identical to outputs/the_bet.json: yes")

# 1 · the sleeve completed
print("\n1. THE TWO TILTS AND THE COMPLETE SLEEVE, in % of the portfolio (30% in equities)")
print("   active weights, points of the sleeve: six %+.2f | networks against all utilities %+.2f | the rest %+.2f | sum %+.2f"
      % (A_SIX * 100, A_NET * 100, A_REST * 100, round((A_SIX + A_NET + A_REST) * 100, 2) + 0.0))
print("   %-46s %9s %9s %9s %11s %10s %11s" % ("period", "utilities", "the rest", "two tilts", "complete", "difference", "sleeve"))
for name, (a, b) in PERIODS.items():
    r6, rn, ri, ru = total(six, a, b), total(net, a, b), total(idx, a, b), total(util, a, b)
    rest = (ri - W_SIX * r6 - W_UTIL * ru) / (1 - W_SIX - W_UTIL)
    two = A_SIX * (r6 - ri) + A_NET * (rn - ri)
    sleeve = W_SIX_OURS * r6 + W_NET_OURS * rn + (1 - W_SIX_OURS - W_NET_OURS) * rest
    complete = sleeve - ri
    print("   %-46s %+8.1f%% %+8.1f%% %+9.2f %+11.2f %+10.2f %+10.1f%%"
          % (name, ru * 100, rest * 100, two * SLEEVE * 100, complete * SLEEVE * 100, (complete - two) * SLEEVE * 100, sleeve * 100))
print("   'two tilts' is the figure of the application file. 'complete' is the return of the whole sleeve less the index.")
print("   The rest of the index is a residual at today's weights: before 2026 the six weighed less than today, so the")
print("   residual is too low in the years when they rose most. Our own stock picks inside the rest are not in either figure.")

# 2 · what the eight weigh in the index
print("\n2. WHAT THE EIGHT NETWORK COMPANIES WEIGH, upper bound from full market values at the close of 20 November")
def value_usd(t: str, ccy: str) -> float:
    fi = yf.Ticker(t).fast_info
    close = frame(t, start="2026-10-01")["Close"].dropna()
    local = float(fi["marketCap"]) * float(close.loc[:CUT].iloc[-1]) / float(fi["lastPrice"])
    if fi["currency"] == "GBp":                      # London quotes in pence
        local /= 100
    return local if ccy == "USD" else local * float(fx[ccy].loc[:CUT].iloc[-1])
six_value = sum(value_usd(t, "USD") for t in SIX)
index_value = six_value / W_SIX                      # the six are 18.33% of the fund: its total follows
values = {t: value_usd(t, ccy) for t, ccy in NETWORKS.items()}
for t, v in values.items():
    print("   %-8s $%6.1fbn  %.3f%%" % (t, v / 1e9, v / index_value * 100))
eight = sum(values.values()) / index_value
print("   the eight together: $%.0fbn, at most %.2f%% of the index | 15%% of our sleeve is %.0f times that, and %.0f times the 2.5%% of all utilities"
      % (sum(values.values()) / 1e9, eight * 100, W_NET_OURS / eight, W_NET_OURS / W_UTIL))

# 3 · the six equally weighted
print("\n3. THE SIX EQUALLY WEIGHTED, same periods (two tilts, % of the portfolio)")
for name, (a, b) in PERIODS.items():
    r6, re_, rn, ri = total(six, a, b), total(six_equal, a, b), total(net, a, b), total(idx, a, b)
    print("   %-46s six as in the index %+7.1f%% -> %+6.2f | six equally weighted %+7.1f%% -> %+6.2f"
          % (name, r6 * 100, (A_SIX * (r6 - ri) + A_NET * (rn - ri)) * SLEEVE * 100, re_ * 100, (A_SIX * (re_ - ri) + A_NET * (rn - ri)) * SLEEVE * 100))

# 4 · the networks and the ten-year yield, weekly
def fit(y: np.ndarray, X: np.ndarray, lags: int):
    """Coefficients, plain and Newey-West standard errors, R squared."""
    n, k = X.shape
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    u = y - X @ b
    xtx = np.linalg.inv(X.T @ X)
    plain = np.sqrt(np.diag(u @ u / (n - k) * xtx))
    xu = X * u[:, None]
    s = xu.T @ xu
    for lag in range(1, lags + 1):
        g = xu[lag:].T @ xu[:-lag]
        s += (1 - lag / (lags + 1)) * (g + g.T)
    hac = np.sqrt(np.diag(xtx @ s @ xtx * n / (n - k)))
    return b, plain, hac, 1 - (u @ u) / ((y - y.mean()) @ (y - y.mean()))


wk = (1 + pd.DataFrame({"net": net, "idx": idx, "six": six}).loc["2022-12-30":CUT]).resample("W-FRI").prod() - 1
csv = subprocess.run(["curl", "-s", "--max-time", "40", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10&cosd=2022-12-20&coed=2026-11-25"], capture_output=True, text=True).stdout
y10 = pd.to_numeric(pd.read_csv(io.StringIO(csv), index_col=0, parse_dates=True).iloc[:, 0], errors="coerce").dropna()
d = wk.join(y10.resample("W-FRI").last().diff().rename("dy")).dropna()
print("\n4. NETWORKS AND THE TEN-YEAR TREASURY YIELD, weekly, %s to %s" % (d.index[0].date(), d.index[-1].date()))


def line(label: str, data: pd.DataFrame, with_index: bool = True) -> None:
    n = len(data)
    lags = int(np.floor(4 * (n / 100) ** (2 / 9)))
    X = np.column_stack([np.ones(n), data["idx"], data["dy"]] if with_index else [np.ones(n), data["dy"]])
    b, plain, hac, r2 = fit(data["net"].to_numpy(), X, lags)
    c, s_plain, s_hac = b[-1] * 10, plain[-1] * 10, hac[-1] * 10          # % per 0.10 point of yield
    print("   %-44s %3d weeks | %+.2f%% per +0.10 point | s.e. %.2f plain, %.2f Newey-West (%d lags) | t %.1f | 95%%: %+.2f to %+.2f | R2 %.2f"
          % (label, n, c, s_plain, s_hac, lags, c / s_hac, c - 1.96 * s_hac, c + 1.96 * s_hac, r2))


line("with the index (the figure of the file)", d)
line("without the index", d, with_index=False)
line("2023 and 2024", d.loc[:"2024-12-31"])
line("2025 and 2026", d.loc["2025-01-01":])
line("without the five weeks of largest yield moves", d.drop(d["dy"].abs().nlargest(5).index))
d["bet"] = A_SIX * (d["six"] - d["idx"]) + A_NET * (d["net"] - d["idx"])
n = len(d)
lags = int(np.floor(4 * (n / 100) ** (2 / 9)))
b, plain, hac, r2 = fit(d["bet"].to_numpy(), np.column_stack([np.ones(n), d["idx"]]), lags)
print("   beta of the two tilts to the index: %+.3f | s.e. %.3f plain, %.3f Newey-West | R2 %.2f" % (b[1], plain[1], hac[1], r2))

# 5 · who is not in the six
print("\n5. CAPITAL EXPENDITURE OVER THE LAST TWELVE MONTHS REPORTED, $bn (cash-flow statements, Yahoo Finance)")
capex = {t: -float(yf.Ticker(t).ttm_cashflow.loc["Capital Expenditure"].iloc[0]) / 1e9 for t in ("MSFT", "GOOGL", "AMZN", "META", "AAPL", "TSLA")}
print("   the four buyers: " + ", ".join("%s %.0f" % (t, capex[t]) for t in ("MSFT", "GOOGL", "AMZN", "META")) + " | left at index weight: AAPL %.0f, TSLA %.0f" % (capex["AAPL"], capex["TSLA"]))
