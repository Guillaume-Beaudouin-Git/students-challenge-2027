"""Tests on synthetic data only: they run before any real return is read."""
import numpy as np
import pandas as pd
import pytest

from riskbudget import core


def _calendar(n: int, start: str = "2020-01-01") -> pd.DatetimeIndex:
    return pd.bdate_range(start, periods=n)


def test_ewma_cov_recursion_matches_manual():
    rng = np.random.default_rng(0)
    r = rng.normal(0, 0.01, size=(80, 2))
    cov = core.ewma_cov(r, lam=0.94, init=60)
    assert np.isnan(cov[58]).all()
    np.testing.assert_allclose(cov[59], r[:60].T @ r[:60] / 60)
    manual = 0.94 * cov[59] + 0.06 * np.outer(r[60], r[60])
    np.testing.assert_allclose(cov[60], manual)


def test_ewma_cov_uses_no_future_row():
    rng = np.random.default_rng(1)
    r = rng.normal(0, 0.01, size=(100, 2))
    base = core.ewma_cov(r)[80]
    altered = r.copy()
    altered[81:] *= 50.0
    np.testing.assert_allclose(core.ewma_cov(altered)[80], base)


def test_target_weight_is_largest_admissible():
    daily = lambda ann: ann**2 / core.TRADING_DAYS  # noqa: E731
    cov = np.array([[daily(0.16), 0.0], [0.0, daily(0.04)]])
    w = core.target_weight(cov, target=0.08)
    vols = core.ex_ante_vol(cov)
    assert vols[np.isclose(core.GRID, w)][0] <= 0.08
    above = core.GRID[core.GRID > w + 1e-9]
    if above.size:
        assert core.ex_ante_vol(cov, above[:1])[0] > 0.08


def test_target_weight_caps_at_80_when_calm():
    daily = lambda ann: ann**2 / core.TRADING_DAYS  # noqa: E731
    cov = np.array([[daily(0.06), 0.0], [0.0, daily(0.03)]])
    assert core.target_weight(cov) == pytest.approx(0.80)


def test_target_weight_falls_back_to_min_vol_mix():
    daily = lambda ann: ann**2 / core.TRADING_DAYS  # noqa: E731
    sd_e, sd_b = np.sqrt(daily(0.70)), np.sqrt(daily(0.10))
    cov = np.array([[sd_e**2, -0.3 * sd_e * sd_b], [-0.3 * sd_e * sd_b, sd_b**2]])
    vols = core.ex_ante_vol(cov)
    assert vols.min() > 0.08
    assert core.target_weight(cov) == pytest.approx(core.GRID[int(np.argmin(vols))])


def test_decision_days_are_last_session_of_each_week():
    idx = _calendar(30, "2024-12-16")
    days = core.decision_days(idx)
    assert all(d.dayofweek == 4 for d in days[:-1])
    assert days[-1] == idx[-1] or days[-1].dayofweek == 4
    assert len(days) == len(set(zip(idx.isocalendar()["year"], idx.isocalendar()["week"])))


def test_weights_in_force_lag_is_two_sessions():
    idx = _calendar(20)
    tau = idx[4]
    w = core.weights_in_force(idx, pd.Series({tau: 0.5}))
    assert w.iloc[:6].isna().all()          # τ and τ+1 still earn the old (absent) weight
    assert w.iloc[6] == 0.5                 # first return earned at the new weight is τ+2
    assert (w.iloc[6:] == 0.5).all()


def test_weights_in_force_successive_targets():
    idx = _calendar(20)
    w = core.weights_in_force(idx, pd.Series({idx[4]: 0.5, idx[9]: 0.3}))
    assert w.iloc[10] == 0.5 and w.iloc[11] == 0.3


def test_weekly_targets_respects_burn_in_and_point_in_time():
    rng = np.random.default_rng(2)
    idx = _calendar(400)
    r = pd.DataFrame(rng.normal(0, [0.012, 0.004], size=(400, 2)), index=idx, columns=["E", "B"])
    targets = core.weekly_targets(r)
    assert idx.get_loc(targets.index[0]) >= core.BURN_IN_SESSIONS
    cut = targets.index[20]
    truncated = core.weekly_targets(r.loc[:cut])
    pd.testing.assert_series_equal(targets.loc[:cut], truncated, check_names=False)


def test_mix_returns_and_rolling_vol():
    idx = _calendar(130)
    rng = np.random.default_rng(3)
    r = pd.DataFrame(rng.normal(0, 0.01, size=(130, 2)), index=idx, columns=["E", "B"])
    mix = core.mix_returns(r, 0.6)
    np.testing.assert_allclose(mix, 0.6 * r["E"] + 0.4 * r["B"])
    v = core.rolling_vol(mix)
    assert v.iloc[:62].isna().all() and not np.isnan(v.iloc[62])
    assert v.iloc[62] == pytest.approx(mix.iloc[:63].std(ddof=1) * np.sqrt(252))


def test_breach_episodes_runs():
    idx = _calendar(10)
    vol = pd.Series([0.05, 0.11, 0.12, 0.09, 0.08, 0.13, 0.07, 0.11, 0.11, 0.11], index=idx)
    eps = core.breach_episodes(vol)
    assert [(e.days, round(e.peak, 2)) for e in eps] == [(2, 0.12), (1, 0.13), (3, 0.11)]
    assert eps[-1].end == idx[-1]


def test_stationary_bootstrap_indices_properties():
    rng = np.random.default_rng(4)
    n, block = 2000, 50
    idx = core.stationary_bootstrap_indices(n, block, 40, rng)
    assert idx.shape == (40, n) and idx.min() >= 0 and idx.max() < n
    steps = (idx[:, 1:] - idx[:, :-1]) % n
    continued = (steps == 1).mean()
    assert continued == pytest.approx(1 - 1 / block, abs=0.01)


def test_bootstrap_mean_centres_on_sample_mean():
    rng = np.random.default_rng(5)
    x = rng.normal(0.3, 1.0, size=3000)
    dist = core.bootstrap_mean(x, mean_block=20, n_resamples=2000, seed=7)
    assert dist.mean() == pytest.approx(x.mean(), abs=0.01)
    assert dist.std() == pytest.approx(1.0 / np.sqrt(3000), rel=0.25)


def test_bootstrap_sharpe_diff_is_zero_for_identical_series():
    rng = np.random.default_rng(6)
    a = rng.normal(0.0004, 0.01, size=1500)
    dist = core.bootstrap_sharpe_diff(a, a.copy(), mean_block=20, n_resamples=500, seed=8)
    np.testing.assert_allclose(dist, 0.0, atol=1e-12)


def test_sharpe_and_drawdown():
    r = pd.Series([0.10, -0.50, 0.20])
    assert core.max_drawdown(r) == pytest.approx(-0.50)
    x = np.array([0.01, 0.02, 0.03])
    assert core.sharpe(x) == pytest.approx(np.sqrt(252) * 0.02 / 0.01)
