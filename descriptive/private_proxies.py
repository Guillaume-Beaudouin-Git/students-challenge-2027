"""What the listed cousins of private assets did in the two shocks of 2026.

Descriptive. Listed funds are not private assets: they are marked every day, carry equity beta and
trade at premiums or discounts to the value of what they hold. That is why they are useful here:
they show, day by day, what quarterly appraisals of unlisted assets show late or not at all.

Proxies (total return in dollars, adjusted closes, Yahoo Finance): developed equities URTH; listed
infrastructure IGF; listed private equity PSP; business development companies, which hold private
loans, BIZD; leveraged loans BKLN.

    python3 private_proxies.py > outputs/private_proxies.txt
"""
import json
import warnings

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import yfinance as yf

CUT = "2026-11-20"
NAMES = {"URTH": "Developed equities", "IGF": "Listed infrastructure", "PSP": "Listed private equity",
         "BIZD": "Listed private-debt lenders (BDCs)", "BKLN": "Leveraged loans"}
EPISODES = {"oil shock, 27 Feb to 31 Mar 2026": ("2026-02-27", "2026-03-31"),
            "AI correction, 6 Oct to 20 Nov 2026": ("2026-10-06", "2026-11-20"),
            "2026 to 20 Nov": ("2025-12-31", "2026-11-20")}


def adj(ticker: str) -> pd.Series:
    df = yf.download(ticker, start="2025-06-01", end="2026-11-21", auto_adjust=False, progress=False, threads=False)
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    return df["Adj Close"].dropna()


px = pd.concat({t: adj(t) for t in NAMES}, axis=1).dropna().loc[:CUT]
r = px.pct_change().dropna()
out = {}
for t, name in NAMES.items():
    row = {}
    for label, (a, b) in EPISODES.items():
        seg = px[t].loc[a:b]
        row[label] = round(float(seg.iloc[-1] / seg.iloc[0] - 1) * 100, 1)
    y = r[t].loc["2026"]
    row["volatility 2026, %"] = round(float(y.std(ddof=1) * np.sqrt(252)) * 100, 1)
    row["correlation with equities 2026"] = round(float(y.corr(r["URTH"].loc["2026"])), 2)
    row["fall from 2026 high to 20 Nov, %"] = round(float(px[t].loc[CUT] / px[t].loc["2026"].max() - 1) * 100, 1)
    out[name] = row
    print(f"{name:38s} ({t})", row)
json.dump(out, open("outputs/private_proxies.json", "w"), indent=1)
