"""Today's equity ceiling of the one-line rule, at several volatility targets.

Descriptive, written on 24 November 2026 after the pre-registered test. It is not a second run of
that test: it computes one number, the ceiling the rule gives on the covariances of 20 November
2026, for the 8% target that was tested and for lower ones. The largest equity weight between 20%
and 80% whose expected volatility, with the rest in 7-10-year Treasuries, is at most the target.
Covariances: exponentially weighted, decay 0.94, daily returns from June 2024.
Proxies: developed equities = 60% SPY + 40% EFA; Treasuries = IEF. Adjusted closes, Yahoo Finance.

    python3 rule_ceiling_today.py > outputs/rule_ceiling_today.txt
"""
import warnings

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import yfinance as yf

CUT, LAMBDA, INIT = "2026-11-20", 0.94, 60


def adj(ticker: str) -> pd.Series:
    df = yf.download(ticker, start="2024-06-01", end="2026-11-21", auto_adjust=False, progress=False, threads=False)
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    return df["Adj Close"].dropna()


px = pd.concat({t: adj(t) for t in ("SPY", "EFA", "IEF")}, axis=1).dropna().loc[:CUT]
r = px.pct_change().dropna()
r["E"] = 0.6 * r["SPY"] + 0.4 * r["EFA"]
x = r[["E", "IEF"]].to_numpy()
cov = x[:INIT].T @ x[:INIT] / INIT
for t in range(INIT, len(x)):
    cov = LAMBDA * cov + (1 - LAMBDA) * np.outer(x[t], x[t])
cov *= 252
print("as of", r.index[-1].date(), "| equity volatility %.1f%%, Treasury volatility %.1f%%, correlation %.2f"
      % (np.sqrt(cov[0, 0]) * 100, np.sqrt(cov[1, 1]) * 100, cov[0, 1] / np.sqrt(cov[0, 0] * cov[1, 1])))
for target in (0.08, 0.07, 0.065, 0.06):
    best = None
    for w in np.arange(0.20, 0.8001, 0.01):
        v = float(np.sqrt(np.array([w, 1 - w]) @ cov @ np.array([w, 1 - w])))
        if v <= target:
            best = w
    print("target %.1f%% -> equity ceiling %s" % (target * 100, "none above the 20%% floor" if best is None else "%.0f%%" % (best * 100)))
