"""End-to-end run on synthetic files: the pipeline is exercised before it meets real data."""
import json

import numpy as np
import pandas as pd

import run_exhibit


def _write_price(path, index, rng, vol, drift=0.0002):
    r = rng.normal(drift, vol, size=len(index))
    px = 100 * np.cumprod(1 + r)
    pd.DataFrame({"Adj Close": px, "Close": px}, index=pd.Index(index, name="Date")).to_csv(path)


def test_pipeline_runs_and_is_coherent(tmp_path):
    rng = np.random.default_rng(11)
    idx = pd.bdate_range("2005-01-03", "2012-12-28")
    raw = tmp_path / "raw"
    raw.mkdir()
    for name, vol in [("SPY", 0.012), ("EFA", 0.013), ("IEF", 0.004)]:
        _write_price(raw / f"{name}.csv", idx, rng, vol)
    late = idx[idx >= "2008-01-02"]
    _write_price(raw / "IBGM_AS.csv", late, rng, 0.003)
    _write_price(raw / "EURUSD_X.csv", late, rng, 0.006, drift=0.0)
    pd.DataFrame({"observation_date": idx.strftime("%Y-%m-%d"), "DTB3": 2.0}).to_csv(raw / "DTB3.csv", index=False)
    manifest = tmp_path / "MANIFEST.json"
    manifest.write_text(json.dumps({"fetched_at_utc": "synthetic", "files": {}}))

    res = run_exhibit.main(raw=raw, out=tmp_path / "results", runlog=tmp_path / "RUNLOG.md", manifest_path=manifest)

    daily = pd.read_csv(tmp_path / "results" / "daily_series.csv", index_col=0, parse_dates=True)
    assert daily["w_rule"].between(0.20, 0.80).all()
    assert res["H1"]["verdict"] in {"PASS", "FAIL", "NOT SHOWN"}
    assert res["H2"]["verdict"] in {"NON-INFERIOR", "INFERIOR", "NOT SHOWN"}
    assert res["H2"]["L2"] <= res["H2"]["sharpe_diff"] + 0.5 and res["H2"]["L2"] < res["H2"]["U2"]
    assert 0.20 <= res["static_equity_weight"] <= 0.80
    # the first weight in force comes two sessions after the first eligible decision
    first_decision = pd.read_csv(tmp_path / "results" / "weekly_targets.csv", index_col=0, parse_dates=True).index[0]
    assert daily.index[0] == idx[idx.get_loc(first_decision) + 2]
    # recompute one rule return by hand
    px = pd.concat({n: pd.read_csv(raw / f"{n}.csv", index_col=0, parse_dates=True)["Adj Close"] for n in ("SPY", "EFA", "IEF")}, axis=1)
    ret = px.pct_change()
    day = daily.index[300]
    by_hand = daily.loc[day, "w_rule"] * (0.6 * ret.loc[day, "SPY"] + 0.4 * ret.loc[day, "EFA"]) + (1 - daily.loc[day, "w_rule"]) * ret.loc[day, "IEF"]
    assert abs(by_hand - daily.loc[day, "r_RULE"]) < 1e-7
    assert abs(daily["cash"].iloc[10] - 0.02 / 252) < 1e-8  # the CSV keeps 8 decimals
    fx = res["fx_descriptive"]["series"]
    assert set(fx) == {"E", "IEF", "EUROGOV_EUR", "EURUSD", "EUROGOV_USD"}
    assert fx["EUROGOV_USD"]["ann_vol"] > fx["EUROGOV_EUR"]["ann_vol"]
    assert (tmp_path / "RUNLOG.md").read_text().count("\n") == 1
