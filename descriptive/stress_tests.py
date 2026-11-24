"""Replay of three allocations of the application file through seven past shocks, and one invented shock.

Descriptive, on fund proxies, with weights held constant (rebalanced daily). Not pre-registered:
written on 24 November 2026 after the allocations were chosen, and two of the seven episodes (the
two shocks of 2026) are the ones the allocations were designed around. It answers one question:
what would each allocation have lost, and how volatile would it have been, if nobody had touched it?

Allocations: the opening one; the central scenario's; our reference mix (35% developed equities, 55%
Treasuries of 3 to 7 years, 10% bills); and where the breach procedure leads, which is equities at our
internal floor of 23% and every bond under two years. Five points of the equity sleeve of the first
two are electricity networks and listed infrastructure.
Proxies: developed equities = 60% SPY + 40% EFA; bills and cash = BIL; notes under 2 years = half BIL,
half SHY; Treasuries of 2 to 5 years and dollar supranational bonds = IEI; Treasuries of 5 to 10 years
= IEF; inflation-linked = TIP; commodities = DBC; listed infrastructure = IGF. Adjusted closes, Yahoo
Finance, from January 2008 (first full month of IGF) to 20 November 2026.

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


tickers = ["SPY", "EFA", "BIL", "SHY", "IEI", "TIP", "DBC", "IEF", "IGF"]
px = pd.concat({t: adj(t) for t in tickers}, axis=1).dropna().loc["2008-01-01":CUT]
r = px.pct_change().dropna()
r["E"] = 0.6 * r["SPY"] + 0.4 * r["EFA"]

# weights by proxy; cash is counted with bills
OPENING = {"E": 0.25, "IGF": 0.05, "BIL": 0.125 + 0.10, "SHY": 0.125, "IEI": 0.15 + 0.10, "TIP": 0.05, "DBC": 0.05}
CENTRAL = {"E": 0.30, "IGF": 0.05, "BIL": 0.035 + 0.03, "SHY": 0.035, "IEI": 0.15 + 0.10, "IEF": 0.20, "TIP": 0.05, "DBC": 0.05}
REFERENCE = {"E": 0.35, "IEI": 0.55, "BIL": 0.10}      # our reference mix: 35% equities, 55% Treasuries of 3 to 7 years, 10% bills
AFTER_BREACH = {"E": 0.23, "BIL": 0.385 + 0.05, "SHY": 0.335}
FLOOR_AND_BILLS = {"E": 0.20, "BIL": 0.80}      # the mandate's equity floor with nothing else at risk
PORTFOLIOS = {"opening allocation": OPENING, "central scenario allocation": CENTRAL, "reference mix 35/55/10": REFERENCE,
              "after the breach procedure (23% equities, bonds under 2 years)": AFTER_BREACH,
              "20% equities, 80% bills": FLOOR_AND_BILLS}
for name, w in PORTFOLIOS.items():
    assert abs(sum(w.values()) - 1.0) < 1e-9, (name, sum(w.values()))

ret = pd.DataFrame({name: sum(wt * r[a] for a, wt in w.items()) for name, w in PORTFOLIOS.items()})
vol = ret.rolling(WINDOW).std(ddof=1) * np.sqrt(252)

EPISODES = [
    ("Financial crisis", "2008-09-12", "2009-03-09"),
    ("Euro crisis, US downgrade", "2011-07-22", "2011-10-03"),
    ("Taper tantrum", "2013-05-21", "2013-09-05"),
    ("Covid", "2020-02-19", "2020-03-23"),
    ("Inflation and rate rises", "2022-01-03", "2022-10-14"),
    ("Oil shock", "2026-02-27", "2026-03-31"),
    ("AI correction", "2026-10-06", "2026-11-20"),
]

out = {"sample": [str(ret.index[0].date()), str(ret.index[-1].date()), int(len(ret))], "episodes": [], "full_sample": {}, "hypothetical": {}}
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
        peak = float(v_seg[name].max())
        row[name] = {"return": round(total, 4), "peak_vol_63": round(peak, 4)}
        print(f"  {name:62s} return {total * 100:+6.1f}% | highest 63-session volatility {peak * 100:5.1f}%")
    out["episodes"].append(row)

print("\nfull sample:")
for name in PORTFOLIOS:
    v = vol[name].dropna()
    above = v > CAP
    stats = {"sessions_above_cap": round(float(above.mean()), 4), "sessions_above_9": round(float((v > 0.09).mean()), 4),
             "highest_vol_63": round(float(v.max()), 4), "highest_vol_date": str(v.idxmax().date()),
             "vol": round(float(ret[name].std(ddof=1) * np.sqrt(252)), 4),
             "by_year": {int(y): int(n) for y, n in above.groupby(above.index.year).sum().items() if n}}
    out["full_sample"][name] = stats
    print(f"  {name:62s}", stats)

# An invented shock, by arithmetic: equities -15%, yields +0.75 point at every maturity, a broad
# commodity basket +20% (Brent near $130). Duration is taken as 0.9 x average maturity of each sleeve;
# inflation-linked bonds are assumed flat (higher real yields offset by higher inflation compensation).
SHOCK = {"equities": -15.0, "yields": +0.75, "commodities": +20.0}
SLEEVE_VIEW = {   # weights in %, average maturities in years
    "opening allocation": {"equities": 30, "commodities": 5, "bonds": [(25, 0.5), (15, 3.5), (10, 5.0)]},
    "central scenario allocation": {"equities": 35, "commodities": 5, "bonds": [(7, 0.5), (15, 3.5), (20, 7.5), (10, 5.0)]},
    "reference mix 35/55/10": {"equities": 35, "commodities": 0, "bonds": [(55, 5.0)]},
    "after the breach procedure (23% equities, bonds under 2 years)": {"equities": 23, "commodities": 0, "bonds": [(72, 1.0)]},
}
print("\ninvented shock", SHOCK)
for name, s in SLEEVE_VIEW.items():
    bond_loss = sum(w * 0.9 * m * SHOCK["yields"] for w, m in s["bonds"]) / 100
    total = s["equities"] * SHOCK["equities"] / 100 + s["commodities"] * SHOCK["commodities"] / 100 - bond_loss
    out["hypothetical"][name] = round(total, 2)
    print(f"  {name:62s} {total:+.1f}%  (equities {s['equities'] * SHOCK['equities'] / 100:+.1f}, bonds {-bond_loss:+.1f}, commodities {s['commodities'] * SHOCK['commodities'] / 100:+.1f})")
json.dump(out, open("outputs/stress_tests.json", "w"), indent=1)
