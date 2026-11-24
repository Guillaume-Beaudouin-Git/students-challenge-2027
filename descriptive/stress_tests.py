"""Replay of the opening allocation of the application file through five past shocks.

Descriptive, on fund proxies, with weights held constant (rebalanced daily). Not pre-registered:
written on 24 November 2026 after the opening allocation was chosen. It answers one question:
what would this allocation have lost, and how volatile would it have been, if nobody had touched it?

Proxies: developed equities = 60% SPY + 40% EFA; bills and cash = BIL; notes under 2 years = half BIL,
half SHY; Treasuries of 2 to 5 years and dollar supranational bonds = IEI; inflation-linked = TIP;
commodities = DBC; reference mix = half equities, half IEF. Adjusted closes, Yahoo Finance, from
June 2007 (first full month of BIL) to 20 November 2026.

    python3 stress_tests.py > outputs/stress_tests.txt
"""
import json
import warnings

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import yfinance as yf

CUT = "2026-11-20"
CAP = 0.10
WINDOW = 63


def adj(ticker: str) -> pd.Series:
    df = yf.download(ticker, start="2007-05-25", end="2026-11-21", auto_adjust=False, progress=False, threads=False)
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    return df["Adj Close"].dropna()


tickers = ["SPY", "EFA", "BIL", "SHY", "IEI", "TIP", "DBC", "IEF"]
px = pd.concat({t: adj(t) for t in tickers}, axis=1).dropna().loc["2007-06-01":CUT]
r = px.pct_change().dropna()
r["E"] = 0.6 * r["SPY"] + 0.4 * r["EFA"]

OPENING = {"E": 0.30, "BIL": 0.125 + 0.10, "SHY": 0.125, "IEI": 0.15 + 0.10, "TIP": 0.05, "DBC": 0.05}
AT_FLOOR = {**OPENING, "E": 0.20, "BIL": OPENING["BIL"] + 0.10}
REFERENCE = {"E": 0.50, "IEF": 0.50}
FLOOR_AND_BILLS = {"E": 0.20, "BIL": 0.80}   # the mandate's equity floor with nothing else at risk
PORTFOLIOS = {"opening allocation (30% equities)": OPENING, "same, equities at the 20% floor": AT_FLOOR, "reference mix 50/50": REFERENCE,
              "20% equities, 80% bills": FLOOR_AND_BILLS}
for name, w in PORTFOLIOS.items():
    assert abs(sum(w.values()) - 1.0) < 1e-9, name

ret = pd.DataFrame({name: sum(wt * r[a] for a, wt in w.items()) for name, w in PORTFOLIOS.items()})
vol = ret.rolling(WINDOW).std(ddof=1) * np.sqrt(252)

EPISODES = [
    ("Financial crisis", "2008-09-12", "2009-03-09"),
    ("Covid", "2020-02-19", "2020-03-23"),
    ("Inflation and rate rises", "2022-01-03", "2022-10-14"),
    ("Oil shock", "2026-02-27", "2026-03-31"),
    ("AI correction", "2026-10-06", "2026-11-20"),
]

out = {"sample": [str(ret.index[0].date()), str(ret.index[-1].date()), int(len(ret))], "episodes": [], "full_sample": {}}
print("sample:", ret.index[0].date(), "to", ret.index[-1].date(), "|", len(ret), "sessions")
for label, start, end in EPISODES:
    seg = ret.loc[start:end].iloc[1:]          # returns after the close of the start day
    pos_end = ret.index.get_indexer([pd.Timestamp(end)], method="ffill")[0]
    v_seg = vol.iloc[: pos_end + WINDOW + 1].loc[start:]   # the 63-session measure, up to 63 sessions after the end
    row = {"episode": label, "from": start, "to": end}
    print(f"\n{label}: {start} to {end} ({len(seg)} sessions)")
    for name in PORTFOLIOS:
        cum = (1 + seg[name]).cumprod()
        total = float(cum.iloc[-1] - 1)
        dd = float((cum / cum.cummax().clip(lower=1.0) - 1).min())
        peak = float(v_seg[name].max())
        row[name] = {"return": round(total, 4), "deepest_fall": round(dd, 4), "peak_vol_63": round(peak, 4)}
        print(f"  {name:36s} return {total * 100:+6.1f}% | deepest fall {dd * 100:6.1f}% | highest 63-session volatility {peak * 100:5.1f}%")
    out["episodes"].append(row)

print("\nfull sample:")
for name in PORTFOLIOS:
    v = vol[name].dropna()
    cum = (1 + ret[name]).cumprod()
    stats = {"days_above_cap": round(float((v > CAP).mean()), 4), "highest_vol_63": round(float(v.max()), 4),
             "highest_vol_date": str(v.idxmax().date()), "vol": round(float(ret[name].std(ddof=1) * np.sqrt(252)), 4),
             "max_drawdown": round(float((cum / cum.cummax() - 1).min()), 4),
             "ann_return": round(float(cum.iloc[-1] ** (252 / len(ret)) - 1), 4)}
    out["full_sample"][name] = stats
    print(f"  {name:36s}", stats)

# where the breaches fall, by calendar year
for name in PORTFOLIOS:
    above = (vol[name].dropna() > CAP)
    print(f"\n{name}: sessions above the cap by year:", {int(y): int(n) for y, n in above.groupby(above.index.year).sum().items() if n})
json.dump(out, open("outputs/stress_tests.json", "w"), indent=1)
