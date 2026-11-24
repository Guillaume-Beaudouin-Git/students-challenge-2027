"""Exploratory analysis written AFTER the single run, prompted by an independent review.

Not pre-registered. It changes no verdict of PREREGISTRATION.md; it asks a harder question than H1:
does the rule still look useful against constant mixes that carry the same risk, and what could have
kept the portfolio under the cap on the days the rule failed? Reads the same raw files as the run.
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import run_exhibit as rx  # noqa: E402
from riskbudget import core  # noqa: E402

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results"


def stats(r: pd.Series, cash: pd.Series) -> dict:
    v = core.rolling_vol(r).dropna()
    ex = (r - cash).to_numpy()
    return {"breach_frequency": float((v > core.CAP_VOL).mean()), "highest_63d_vol": float(v.max()),
            "full_sample_vol": float(r.std(ddof=1) * np.sqrt(252)), "ann_excess_return": float(ex.mean() * 252),
            "sharpe": core.sharpe(ex), "max_drawdown": core.max_drawdown(r)}


def main() -> None:
    daily = pd.read_csv(OUT / "daily_series.csv", index_col=0, parse_dates=True)
    prices = pd.concat({t: rx._load(t, "Adj Close") for t in ("SPY", "EFA", "IEF")}, axis=1).dropna()
    d = prices.pct_change().dropna()
    blocks = pd.DataFrame({"E": 0.6 * d["SPY"] + 0.4 * d["EFA"], "B": d["IEF"]}).loc[daily.index]
    cash = daily["cash"]
    rule = daily["r_RULE"]
    assert np.allclose(core.mix_returns(blocks, daily["w_rule"]), rule, atol=1e-7), "blocks do not reproduce the run"

    out: dict = {"note": "exploratory, not pre-registered; written after the single run", "rule": stats(rule, cash)}
    grid = np.arange(20, 81) / 100
    mixes = {w: core.mix_returns(blocks, float(w)) for w in grid}
    vol = {w: float(r.std(ddof=1) * np.sqrt(252)) for w, r in mixes.items()}
    ret = {w: float((r - cash).mean() * 252) for w, r in mixes.items()}
    w_vol = min(grid, key=lambda w: abs(vol[w] - out["rule"]["full_sample_vol"]))
    w_ret = min(grid, key=lambda w: abs(ret[w] - out["rule"]["ann_excess_return"]))
    out["static_equal_volatility"] = {"equity_weight": float(w_vol), **stats(mixes[w_vol], cash)}
    out["static_equal_return"] = {"equity_weight": float(w_ret), **stats(mixes[w_ret], cash)}

    # where the rule's breach days fall, against the equal-volatility mix
    v_rule = daily["vol63_RULE"].dropna()
    v_eq = core.rolling_vol(mixes[w_vol]).loc[v_rule.index]
    crisis = (v_rule.index.year.isin([2008, 2009, 2020, 2022, 2023]))
    out["breach_days"] = {
        "rule_total": int((v_rule > 0.10).sum()), "equal_vol_total": int((v_eq > 0.10).sum()),
        "rule_in_2008_09_2020_2022_23": int(((v_rule > 0.10) & crisis).sum()),
        "equal_vol_in_2008_09_2020_2022_23": int(((v_eq > 0.10) & crisis).sum()),
        "rule_in_other_years": int(((v_rule > 0.10) & ~crisis).sum()),
        "equal_vol_in_other_years": int(((v_eq > 0.10) & ~crisis).sum()),
    }
    # equity weight in force on the day each breach episode of the rule begins, outside the crisis years
    starts = [e.start for e in core.breach_episodes(daily["vol63_RULE"]) if e.start.year not in (2008, 2009, 2020, 2022, 2023) and e.days >= 10]
    w63 = daily["w_rule"].rolling(63).mean()
    out["calm_loading"] = {"episodes": len(starts), "mean_weight_over_the_63_sessions_before_start": float(np.mean([w63.loc[s] for s in starts])),
                           "mean_weight_full_sample": float(daily["w_rule"].mean())}

    # what could have complied: the equity floor with shorter maturities, proxied by cash
    for name, (we, wb) in {"floor_20_equity_80_treasuries_7_10y": (0.20, 0.80), "floor_20_equity_40_treasuries_40_bills": (0.20, 0.40),
                           "floor_20_equity_20_treasuries_60_bills": (0.20, 0.20)}.items():
        r = we * blocks["E"] + wb * blocks["B"] + (1 - we - wb) * cash
        v = core.rolling_vol(r).loc[v_rule.index]
        out[name] = {"breach_frequency": float((v > 0.10).mean()), "highest_63d_vol": float(v.max()),
                     "share_of_rule_breach_days_also_in_breach": float((v > 0.10)[v_rule > 0.10].mean())}

    # how low would the target have had to be: breach frequency of the rule at other targets (seen data, descriptive)
    out["breach_frequency_by_target"] = {}
    for target in (0.05, 0.06, 0.065, 0.07, 0.075, 0.08):
        t = core.weekly_targets(pd.DataFrame({"E": 0.6 * d["SPY"] + 0.4 * d["EFA"], "B": d["IEF"]}), target=target)
        w = core.weights_in_force(d.index, t).loc[daily.index]
        r = core.mix_returns(blocks, w)
        s = stats(r, cash)
        out["breach_frequency_by_target"][f"{target:.3f}"] = {"breach_frequency": s["breach_frequency"], "highest_63d_vol": s["highest_63d_vol"],
                                                              "mean_weight": float(w.mean()), "full_sample_vol": s["full_sample_vol"], "sharpe": s["sharpe"],
                                                              "ann_excess_return": s["ann_excess_return"]}
    pd.DataFrame({"vol63_RULE": daily["vol63_RULE"], "vol63_SAME_RISK": core.rolling_vol(mixes[w_vol])}).to_csv(
        OUT / "post_review_series.csv", float_format="%.8f")
    (OUT / "post_review.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
