"""The opening allocation of the application file and the allocations its four scenarios lead to.

Descriptive, on fund proxies. Not pre-registered: written on 24 November 2026, after the results of
the pre-registered test were known. For each allocation it prints: expected volatility with the
covariances of 20 November 2026 and with those of 31 March 2026, the day the oil shock ended and a
date when equities and Treasuries were falling together (exponentially weighted, decay 0.94, as in
the risk rule); the share of volatility carried by each block; what the allocation would have
returned in the two shocks of 2026; the average maturity of its bonds; its expected return under
stated assumptions; what a fall of half a point in bond yields would add; the number of lines.

Proxies: developed equities = 60% SPY + 40% EFA; bills and notes under 2 years = half BIL, half SHY;
Treasuries of 2 to 5 years and dollar supranational bonds = IEI (3 to 7 years, so on the long side);
Treasuries of 5 to 10 years = IEF; inflation-linked = TIP; commodities = DBC, which holds agricultural
contracts and gold that the exchange-traded commodity we would buy does not; cash earns the bill return.
Four and a half points of the equity sleeve are electricity networks, proxied by a listed-infrastructure fund (IGF).

    python3 allocation_paths.py > outputs/allocation_paths.txt
"""
import json
import warnings

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import yfinance as yf

CUT = "2026-11-20"
STRESS_DATE = "2026-03-31"
LAMBDA, INIT = 0.94, 60

# sleeve: (proxy mix, assumed average maturity in years, assumed yield or expected return in % a year,
#          lines at the open)
SOFR, BILL, FIVE, TEN, EQUITY_PREMIUM = 3.92, 4.12, 4.70, 4.91, 4.0
NETWORKS = 4.5    # points of the equity sleeve held in electricity networks (three lines of 1.5%), proxied by IGF
SLEEVES = {
    "Equities, developed markets": ({"E": 1.0}, None, SOFR + EQUITY_PREMIUM, 24),     # six AI giants at half weight, three networks, fifteen others
    "Treasury bills and notes under 2 years": ({"BIL": 0.5, "SHY": 0.5}, 0.5, BILL, 6),
    "Treasuries of 2 to 5 years": ({"IEI": 1.0}, 3.5, (BILL + FIVE) / 2, 4),
    "Treasuries of 5 to 10 years": ({"IEF": 1.0}, 7.5, (FIVE + TEN) / 2, 0),
    "Inflation-linked Treasuries, 5 years": ({"TIP": 1.0}, 5.0, FIVE, 2),
    "Dollar green bonds, supranational": ({"IEI": 1.0}, 5.0, FIVE, 3),
    "Commodities (energy and metals)": ({"DBC": 1.0}, None, SOFR, 2),
    "Cash": ({"BIL": 1.0}, None, SOFR, 0),
}
BONDS = [k for k, v in SLEEVES.items() if v[1] is not None]
#                                          opening central relief oil-spike AI-de-rating
ALLOCATIONS = {
    "Equities, developed markets":            (30, 35, 38, 25, 23),
    "Treasury bills and notes under 2 years": (25, 7, 14, 40, 17),
    "Treasuries of 2 to 5 years":             (15, 15, 15, 5, 15),
    "Treasuries of 5 to 10 years":            (0, 20, 10, 0, 25),
    "Inflation-linked Treasuries, 5 years":   (5, 5, 3, 10, 5),
    "Dollar green bonds, supranational":      (10, 10, 10, 5, 10),
    "Commodities (energy and metals)":        (5, 5, 0, 10, 0),
    "Cash":                                   (10, 3, 10, 5, 5),
}
NAMES = ["opening", "central", "relief", "third oil spike", "AI de-rating goes on"]
NON_DOLLAR_SHARE_OF_EQUITIES = 1 / 3      # about the weight of non-US shares in a developed-market index
YIELD_FALL = 0.5                          # percentage points, for the sensitivity line


def adj(ticker: str) -> pd.Series:
    df = yf.download(ticker, start="2024-06-01", end="2026-11-21", auto_adjust=False, progress=False, threads=False)
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    return df["Adj Close"].dropna()


def ewma_cov(x: np.ndarray) -> np.ndarray:
    cov = x[:INIT].T @ x[:INIT] / INIT
    for t in range(INIT, len(x)):
        cov = LAMBDA * cov + (1 - LAMBDA) * np.outer(x[t], x[t])
    return cov * 252


tickers = ["SPY", "EFA", "BIL", "SHY", "IEI", "IEF", "TIP", "DBC", "IGF"]
px = pd.concat({t: adj(t) for t in tickers}, axis=1).dropna().loc[:CUT]
r = px.pct_change().dropna()
r["E"] = 0.6 * r["SPY"] + 0.4 * r["EFA"]
assets = ["E", "BIL", "SHY", "IEI", "IEF", "TIP", "DBC", "IGF"]
cov_now = ewma_cov(r[assets].to_numpy())
cov_stress = ewma_cov(r[assets].loc[:STRESS_DATE].to_numpy())
corr = lambda c, i, j: c[i, j] / np.sqrt(c[i, i] * c[j, j])
print("covariances as of", r.index[-1].date(), "| volatility of each proxy, %:", {a: round(float(np.sqrt(cov_now[i, i])) * 100, 1) for i, a in enumerate(assets)},
      "| correlation equities / Treasuries 3-7y: %.2f" % corr(cov_now, 0, 3))
print("covariances as of", STRESS_DATE, "| volatility of each proxy, %:", {a: round(float(np.sqrt(cov_stress[i, i])) * 100, 1) for i, a in enumerate(assets)},
      "| correlation equities / Treasuries 3-7y: %.2f" % corr(cov_stress, 0, 3))

EPISODES = {"oil shock, 27 Feb to 31 Mar 2026": ("2026-02-27", "2026-03-31"), "AI correction, 6 Oct to 20 Nov 2026": ("2026-10-06", "2026-11-20")}
out = {}
for k, name in enumerate(NAMES):
    weights = {s: ALLOCATIONS[s][k] / 100 for s in SLEEVES}
    assert abs(sum(weights.values()) - 1) < 1e-9, name
    w = pd.Series(0.0, index=assets)
    for sleeve, wt in weights.items():
        if sleeve == "Cash":
            continue                      # cash carries no risk here; it earns the bill return in the replays
        for a, m in SLEEVES[sleeve][0].items():
            w[a] += wt * m
    w["E"] -= NETWORKS / 100; w["IGF"] += NETWORKS / 100      # inside the equity sleeve
    vol = float(np.sqrt(w.to_numpy() @ cov_now @ w.to_numpy()))
    vol_stress = float(np.sqrt(w.to_numpy() @ cov_stress @ w.to_numpy()))
    contrib = pd.Series(cov_now @ w.to_numpy(), index=assets) * w / vol * 100
    blocks = {"equities": float(contrib["E"] + contrib["IGF"]), "bonds": float(contrib[["BIL", "SHY", "IEI", "IEF", "TIP"]].sum()), "commodities": float(contrib["DBC"]), "of which networks, inside equities": float(contrib["IGF"])}
    w_replay = w.copy(); w_replay["BIL"] += weights["Cash"]
    port = (r[assets] * w_replay).sum(axis=1)
    replays = {label: float((1 + port.loc[a:b].iloc[1:]).prod() - 1) * 100 for label, (a, b) in EPISODES.items()}
    bond_weight = sum(weights[s] for s in BONDS)
    maturity = sum(weights[s] * SLEEVES[s][1] for s in BONDS) / bond_weight
    expected = sum(weights[s] * SLEEVES[s][2] for s in SLEEVES)
    # price gain if yields fall by YIELD_FALL at every maturity, duration taken as 0.9 x maturity
    gain = sum(weights[s] * 0.9 * SLEEVES[s][1] * YIELD_FALL for s in BONDS)
    out[name] = {"weights_%": {s: ALLOCATIONS[s][k] for s in SLEEVES}, "expected_vol_%": round(vol * 100, 3), "expected_vol_31_march_covariances_%": round(vol_stress * 100, 3),
                 "vol_points_by_block": {b: round(v, 2) for b, v in blocks.items()}, "replay_return_%": {a: round(v, 2) for a, v in replays.items()},
                 "bond_sleeve_%": round(bond_weight * 100), "average_maturity_years": round(maturity, 2),
                 "non_dollar_%": round(weights["Equities, developed markets"] * NON_DOLLAR_SHARE_OF_EQUITIES * 100, 1),
                 "expected_return_%": round(expected, 2), "gain_if_yields_fall_half_a_point_%": round(gain, 2)}
    print(f"\n{name}: " + ", ".join(f"{ALLOCATIONS[s][k]}" for s in SLEEVES) + "  (sleeves in the order of the table)")
    for key, val in out[name].items():
        if key != "weights_%":
            print(f"  {key}: {val}")

lines = {s: SLEEVES[s][3] for s in SLEEVES if SLEEVES[s][3]}
largest = max(ALLOCATIONS[s][0] / n for s, n in lines.items())
print("\nopening allocation: lines per sleeve", lines, "| total", sum(lines.values()), "| largest line %.2f%% of the portfolio" % largest)
out["opening_lines"] = {"per_sleeve": lines, "total": sum(lines.values()), "largest_line_%": round(largest, 2)}
json.dump(out, open("outputs/allocation_paths.json", "w"), indent=1)
