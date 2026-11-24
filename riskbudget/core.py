"""Pure functions implementing PREREGISTRATION.md. No I/O, no plotting."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

TRADING_DAYS = 252
LAMBDA = 0.94
INIT_SESSIONS = 60
BURN_IN_SESSIONS = 126
TARGET_VOL = 0.08
CAP_VOL = 0.10
WINDOW = 63
GRID = np.arange(20, 81) / 100.0  # equity weights 20%, 21%, ..., 80%


def ewma_cov(returns: np.ndarray, lam: float = LAMBDA, init: int = INIT_SESSIONS) -> np.ndarray:
    """RiskMetrics zero-mean EWMA covariance.

    ``cov[t]`` uses returns up to and including row ``t``. Rows before ``init - 1`` are NaN;
    row ``init - 1`` is the second-moment matrix of the first ``init`` rows.
    """
    n_obs, n_assets = returns.shape
    if n_obs < init:
        raise ValueError(f"need at least {init} observations, got {n_obs}")
    cov = np.full((n_obs, n_assets, n_assets), np.nan)
    state = returns[:init].T @ returns[:init] / init
    cov[init - 1] = state
    for t in range(init, n_obs):
        r = returns[t][:, None]
        state = lam * state + (1.0 - lam) * (r @ r.T)
        cov[t] = state
    return cov


def ex_ante_vol(cov: np.ndarray, grid: np.ndarray = GRID) -> np.ndarray:
    """Annualised ex-ante volatility of every (w_E, 1 - w_E) mix on ``grid`` for one 2x2 covariance."""
    w_e = grid
    w_b = 1.0 - grid
    var = w_e**2 * cov[0, 0] + w_b**2 * cov[1, 1] + 2.0 * w_e * w_b * cov[0, 1]
    return np.sqrt(TRADING_DAYS * var)


def target_weight(cov: np.ndarray, target: float = TARGET_VOL, grid: np.ndarray = GRID) -> float:
    """Largest equity weight on the grid whose ex-ante volatility is at most ``target``.

    If no mix meets the target, the mix with the lowest ex-ante volatility on the grid.
    """
    vols = ex_ante_vol(cov, grid)
    admissible = np.flatnonzero(vols <= target)
    if admissible.size:
        return float(grid[admissible.max()])
    return float(grid[int(np.argmin(vols))])


def decision_days(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Last session of each calendar (ISO) week."""
    iso = index.isocalendar()
    key = iso["year"].astype(int) * 100 + iso["week"].astype(int)
    last = pd.Series(index, index=index).groupby(key.values).max()
    return pd.DatetimeIndex(sorted(last.values))


def weekly_targets(
    returns: pd.DataFrame,
    lam: float = LAMBDA,
    init: int = INIT_SESSIONS,
    burn_in: int = BURN_IN_SESSIONS,
    target: float = TARGET_VOL,
) -> pd.Series:
    """Target equity weight decided at the close of each eligible decision day.

    ``returns`` has two columns, equity block then bond block. A decision day is eligible
    once ``burn_in`` return observations precede it (no decision during the first
    ``burn_in`` sessions).
    """
    cov = ewma_cov(returns.to_numpy(), lam=lam, init=init)
    positions = returns.index.get_indexer(decision_days(returns.index))
    out: dict[pd.Timestamp, float] = {}
    for pos in positions:
        if pos < burn_in:
            continue
        out[returns.index[pos]] = target_weight(cov[pos], target=target)
    return pd.Series(out, name="target_w_equity")


def weights_in_force(index: pd.DatetimeIndex, targets: pd.Series) -> pd.Series:
    """Equity weight earning the return of each day.

    A target decided at the close of τ is traded at the close of τ+1 and earns returns from
    τ+2 (signal at T-1, trade at T). NaN before the first target is in force.
    """
    weights = pd.Series(np.nan, index=index, name="w_equity")
    positions = index.get_indexer(targets.index)
    if (positions < 0).any():
        raise ValueError("a decision day is missing from the return calendar")
    effective = positions + 2
    keep = effective < len(index)
    weights.iloc[effective[keep]] = targets.to_numpy()[keep]
    return weights.ffill()


def mix_returns(returns: pd.DataFrame, w_equity: pd.Series | float) -> pd.Series:
    """Daily return of a two-block mix held at ``w_equity`` (series or constant)."""
    equity, bond = returns.iloc[:, 0], returns.iloc[:, 1]
    return w_equity * equity + (1.0 - w_equity) * bond


def rolling_vol(r: pd.Series, window: int = WINDOW) -> pd.Series:
    """Annualised realised volatility of the trailing ``window`` sessions."""
    return r.rolling(window).std(ddof=1) * np.sqrt(TRADING_DAYS)


@dataclass(frozen=True)
class Episode:
    start: pd.Timestamp
    end: pd.Timestamp
    days: int
    peak: float


def breach_episodes(vol: pd.Series, cap: float = CAP_VOL) -> list[Episode]:
    """Contiguous runs of days on which the trailing volatility exceeds ``cap``."""
    v = vol.dropna()
    flag = (v > cap).to_numpy()
    episodes: list[Episode] = []
    start = None
    for i, on in enumerate(flag):
        if on and start is None:
            start = i
        if start is not None and (not on or i == len(flag) - 1):
            end = i if on else i - 1
            seg = v.iloc[start : end + 1]
            episodes.append(Episode(seg.index[0], seg.index[-1], len(seg), float(seg.max())))
            start = None
    return episodes


def sharpe(excess: np.ndarray) -> float:
    """Annualised Sharpe ratio of a daily excess-return series."""
    sd = excess.std(ddof=1)
    return float(np.sqrt(TRADING_DAYS) * excess.mean() / sd) if sd > 0 else float("nan")


def max_drawdown(r: pd.Series) -> float:
    """Largest peak-to-trough loss of the compounded total-return path (negative number)."""
    wealth = (1.0 + r).cumprod()
    return float((wealth / wealth.cummax() - 1.0).min())


def stationary_bootstrap_indices(
    n: int, mean_block: float, n_resamples: int, rng: np.random.Generator
) -> np.ndarray:
    """Politis-Romano (1994) stationary bootstrap index matrix, shape (n_resamples, n).

    Each resample walks forward through the series (wrapping at the end) and restarts from a
    uniformly drawn position with probability ``1 / mean_block`` at every step.
    """
    restart = rng.random((n_resamples, n)) < 1.0 / mean_block
    restart[:, 0] = True
    starts = rng.integers(0, n, size=(n_resamples, n))
    pos = np.arange(n)
    last_restart = np.maximum.accumulate(np.where(restart, pos, 0), axis=1)
    start_at_restart = np.take_along_axis(starts, last_restart, axis=1)
    return (start_at_restart + pos - last_restart) % n


def bootstrap_mean(
    x: np.ndarray, mean_block: float, n_resamples: int, seed: int, chunk: int = 250
) -> np.ndarray:
    """Stationary-bootstrap distribution of the mean of ``x``."""
    rng = np.random.default_rng(seed)
    out = np.empty(n_resamples)
    for lo in range(0, n_resamples, chunk):
        m = min(chunk, n_resamples - lo)
        idx = stationary_bootstrap_indices(len(x), mean_block, m, rng)
        out[lo : lo + m] = x[idx].mean(axis=1)
    return out


def bootstrap_sharpe_diff(
    a: np.ndarray, b: np.ndarray, mean_block: float, n_resamples: int, seed: int, chunk: int = 250
) -> np.ndarray:
    """Paired stationary-bootstrap distribution of Sharpe(a) - Sharpe(b)."""
    if len(a) != len(b):
        raise ValueError("paired series must have the same length")
    rng = np.random.default_rng(seed)
    out = np.empty(n_resamples)
    scale = np.sqrt(TRADING_DAYS)
    for lo in range(0, n_resamples, chunk):
        m = min(chunk, n_resamples - lo)
        idx = stationary_bootstrap_indices(len(a), mean_block, m, rng)
        ra, rb = a[idx], b[idx]
        sa = scale * ra.mean(axis=1) / ra.std(axis=1, ddof=1)
        sb = scale * rb.mean(axis=1) / rb.std(axis=1, ddof=1)
        out[lo : lo + m] = sa - sb
    return out
