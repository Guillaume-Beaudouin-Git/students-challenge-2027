"""Execute PREREGISTRATION.md once and write results/. Refuses to run on an altered specification."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import statsmodels.api as sm  # noqa: E402

from riskbudget import core  # noqa: E402

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "results"
FROZEN_SHA256 = "1bc296c43b7a76bebba9e302202f28cd6ddb8922dc4f31a04686dc3a90fd003e"
ALPHA = 1.0 - (1.0 - 0.05) ** 0.5          # Šidák, two tests, 5% family level
N_BOOT = 10_000
SEED_H1, SEED_H2 = 20261124, 20261125
BLOCK_H1, BLOCK_H2 = 252, 63
MARGIN = -0.10
W_EQ = {"SPY": 0.60, "EFA": 0.40}


def _load(name: str, column: str) -> pd.Series:
    df = pd.read_csv(RAW / f"{name}.csv", parse_dates=["Date"], index_col="Date")
    return df[column].astype(float).dropna()


def _cash(index: pd.DatetimeIndex) -> pd.Series:
    raw = pd.read_csv(RAW / "DTB3.csv")
    raw.columns = ["Date", "DTB3"]
    s = pd.to_numeric(raw["DTB3"], errors="coerce")
    s.index = pd.to_datetime(raw["Date"])
    s = s.dropna()
    full = s.reindex(index.union(s.index)).ffill().shift(1)
    return (full.reindex(index) / 100.0 / core.TRADING_DAYS).rename("cash")


def _week_key(index: pd.DatetimeIndex) -> np.ndarray:
    iso = index.isocalendar()
    return (iso["year"].astype(int) * 100 + iso["week"].astype(int)).to_numpy()


def _weekly_last(s: pd.Series) -> pd.Series:
    return s.groupby(_week_key(s.index)).last()


def _portfolio_stats(r: pd.Series, cash: pd.Series, vol: pd.Series) -> dict:
    excess = (r - cash).to_numpy()
    v = vol.dropna()
    return {
        "breach_frequency": float((v > core.CAP_VOL).mean()),
        "breach_days": int((v > core.CAP_VOL).sum()),
        "highest_63d_vol": float(v.max()),
        "highest_63d_vol_date": str(v.idxmax().date()),
        "episodes": [{"start": str(e.start.date()), "end": str(e.end.date()), "days": e.days, "peak": e.peak}
                     for e in core.breach_episodes(vol)],
        "ann_excess_return": float(excess.mean() * core.TRADING_DAYS),
        "full_sample_vol": float(r.std(ddof=1) * np.sqrt(core.TRADING_DAYS)),
        "sharpe": core.sharpe(excess),
        "max_drawdown": core.max_drawdown(r),
    }


def main(raw: Path = RAW, out: Path = OUT, runlog: Path = ROOT / "RUNLOG.md",
         manifest_path: Path = ROOT / "data" / "MANIFEST.json") -> dict:
    """Run the specification on the files in ``raw``. The path arguments exist for the synthetic test."""
    global RAW
    RAW = raw
    spec_hash = hashlib.sha256((ROOT / "PREREGISTRATION.md").read_bytes()).hexdigest()
    if spec_hash != FROZEN_SHA256:
        sys.exit("PREREGISTRATION.md differs from the frozen, time-stamped version: refusing to run.")
    out.mkdir(exist_ok=True)

    # --- data -------------------------------------------------------------------------
    prices = pd.concat({t: _load(t, "Adj Close") for t in ("SPY", "EFA", "IEF")}, axis=1).dropna()
    daily = prices.pct_change().dropna()
    blocks = pd.DataFrame({"E": W_EQ["SPY"] * daily["SPY"] + W_EQ["EFA"] * daily["EFA"], "B": daily["IEF"]})
    cash_all = _cash(blocks.index)
    if blocks.isna().any().any() or cash_all.isna().any():
        sys.exit("unfinished input (NaN): refusing to render a verdict.")

    # --- rule -------------------------------------------------------------------------
    targets = core.weekly_targets(blocks)
    w_all = core.weights_in_force(blocks.index, targets)
    sample = w_all.dropna().index
    r, w, cash = blocks.loc[sample], w_all.loc[sample], cash_all.loc[sample]
    w_static = round(float(w.mean()), 2)
    ports = {
        "RULE": core.mix_returns(r, w),
        "STATIC": core.mix_returns(r, w_static),
        "FLOOR": core.mix_returns(r, 0.20),
        "60/40": core.mix_returns(r, 0.60),
    }
    vols = {k: core.rolling_vol(v) for k, v in ports.items()}
    valid = vols["RULE"].dropna().index
    breach = {k: (v.loc[valid] > core.CAP_VOL) for k, v in vols.items()}

    # --- H1 ---------------------------------------------------------------------------
    d = breach["STATIC"].astype(float).to_numpy() - breach["RULE"].astype(float).to_numpy()
    delta = float(d.mean())
    dist1 = core.bootstrap_mean(d, BLOCK_H1, N_BOOT, SEED_H1)
    l1 = float(np.quantile(dist1, ALPHA))
    h1 = "PASS" if l1 > 0 else ("FAIL" if delta <= 0 else "NOT SHOWN")

    # --- H2 ---------------------------------------------------------------------------
    ex_rule, ex_static = (ports["RULE"] - cash).to_numpy(), (ports["STATIC"] - cash).to_numpy()
    s_diff = core.sharpe(ex_rule) - core.sharpe(ex_static)
    dist2 = core.bootstrap_sharpe_diff(ex_rule, ex_static, BLOCK_H2, N_BOOT, SEED_H2)
    l2, u2 = float(np.quantile(dist2, ALPHA)), float(np.quantile(dist2, 1.0 - ALPHA))
    h2 = "NON-INFERIOR" if l2 > MARGIN else ("INFERIOR" if u2 < MARGIN else "NOT SHOWN")

    # --- reported whatever the outcome ------------------------------------------------
    stats = {k: _portfolio_stats(ports[k], cash, vols[k]) for k in ports}
    in_sample_targets = targets.loc[targets.index <= sample[-1]]
    trades = in_sample_targets.diff().abs().dropna()
    years = len(sample) / core.TRADING_DAYS
    rule_breach = breach["RULE"]
    diff = (ports["RULE"] - ports["STATIC"]).to_numpy()
    nw = sm.OLS(diff, np.ones_like(diff)).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
    rule_extra = {
        "mean_weight": float(w.mean()), "min_weight": float(w.min()), "max_weight": float(w.max()),
        "share_weeks_at_20": float((in_sample_targets <= 0.20 + 1e-9).mean()),
        "share_weeks_at_80": float((in_sample_targets >= 0.80 - 1e-9).mean()),
        "annual_turnover_equity_weight": float(trades.sum() / years),
        "share_breach_days_floor_also_breaches": (float(breach["FLOOR"][rule_breach].mean()) if rule_breach.any() else None),
        "newey_west_t_mean_diff_vs_static": float(nw.tvalues[0]),
        "n_weekly_decisions": int(len(in_sample_targets)),
    }

    # --- descriptive exhibit: currency inside the euro sovereign sleeve ---------------
    e_level = (1.0 + blocks["E"]).cumprod()
    weekly = pd.concat({
        "E": _weekly_last(e_level), "IEF": _weekly_last(prices["IEF"]),
        "EUROGOV_EUR": _weekly_last(_load("IBGM_AS", "Adj Close")), "EURUSD": _weekly_last(_load("EURUSD_X", "Close")),
    }, axis=1)
    weekly = weekly.loc[weekly.index >= 200801].dropna()
    wk = weekly.pct_change().dropna()
    wk["EUROGOV_USD"] = (1.0 + wk["EUROGOV_EUR"]) * (1.0 + wk["EURUSD"]) - 1.0
    worst = wk["E"] <= wk["E"].quantile(0.10)
    fx = {
        "n_weeks": int(len(wk)), "first_week": int(wk.index[0]), "last_week": int(wk.index[-1]),
        "series": {c: {"ann_vol": float(wk[c].std(ddof=1) * np.sqrt(52)),
                       "corr_with_E": float(wk[c].corr(wk["E"])),
                       "mean_return_worst_decile_E_weeks": float(wk.loc[worst, c].mean()),
                       "min_week": float(wk[c].min()), "max_week": float(wk[c].max())} for c in wk.columns},
    }

    # --- write ------------------------------------------------------------------------
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    manifest = json.loads(manifest_path.read_text())
    results = {
        "specification_sha256": spec_hash, "code_commit": commit,
        "run_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "data_fetched_at_utc": manifest["fetched_at_utc"],
        "sample": {"first_day": str(sample[0].date()), "last_day": str(sample[-1].date()), "days": int(len(sample)),
                   "days_with_full_window": int(len(valid)), "years": years},
        "static_equity_weight": w_static, "alpha_one_sided_sidak": ALPHA,
        "H1": {"delta": delta, "L1": l1, "verdict": h1, "bootstrap": {"mean_block": BLOCK_H1, "n": N_BOOT, "seed": SEED_H1}},
        "H2": {"sharpe_diff": s_diff, "L2": l2, "U2": u2, "half_width": (u2 - l2) / 2.0, "margin": MARGIN, "verdict": h2,
               "bootstrap": {"mean_block": BLOCK_H2, "n": N_BOOT, "seed": SEED_H2}},
        "portfolios": stats, "rule": rule_extra, "fx_descriptive": fx,
    }
    (out / "results.json").write_text(json.dumps(results, indent=1) + "\n")
    series = pd.DataFrame({"w_rule": w, "cash": cash})
    for k in ports:
        tag = k.replace("/", "")
        series[f"r_{tag}"], series[f"vol63_{tag}"] = ports[k], vols[k]
    series.to_csv(out / "daily_series.csv", float_format="%.8f")
    targets.rename("target_w_equity").to_csv(out / "weekly_targets.csv", float_format="%.2f")
    wk.to_csv(out / "weekly_fx_returns.csv", float_format="%.8f")
    with runlog.open("a") as fh:
        fh.write(f"- {results['run_at_utc']} — code {commit[:7]} — data fetched {manifest['fetched_at_utc']} — "
                 f"H1 {h1}, H2 {h2}\n")
    return results


if __name__ == "__main__":
    res = main()
    print(json.dumps({"H1": res["H1"], "H2": res["H2"], "static_w": res["static_equity_weight"], "sample": res["sample"]}, indent=1))
