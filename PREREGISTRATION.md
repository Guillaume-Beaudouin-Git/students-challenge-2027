# Pre-registration — can a one-line risk budget keep a mandate-shaped portfolio under a 10% volatility cap?

**Status: frozen before any return was computed.** Written on 24 November 2026 for the
application file of our team to *The Students Challenge 2027* (Natixis Investment Managers).
This file is committed, and its SHA-256 fingerprint is time-stamped by an independent
RFC 3161 authority, before the data are downloaded and before the code is run. It is never
edited afterwards: any deviation is appended to `AMENDMENTS.md`.

The specification is executed **once**. The outcome is printed in the application file
whatever it is.

## 1. Why this test

The Contest Rules (Article 5) describe a long-only, unlevered portfolio with 20% to 80% in
developed-market equities, 20% to 80% in sovereign bonds and a **maximum volatility of 10%**.
Our process gives the control of that cap to a simple rule rather than to a forecast. Before
asking anyone to trust the rule, we test it on 24 years of data, under the mandate's own
bounds, and we write down in advance what would count as a failure.

This is a test of a **risk-control rule on two index proxies**. It is not a test of the
portfolio we would run, which holds individual securities, and it makes no claim of excess
return.

## 2. Data

| block | instrument | source | field |
|---|---|---|---|
| US equities | SPY | Yahoo Finance | daily adjusted close (dividends reinvested) |
| Developed equities ex-US | EFA | Yahoo Finance | daily adjusted close |
| US Treasuries 7–10 years | IEF | Yahoo Finance | daily adjusted close |
| Cash | DTB3 (3-month Treasury bill) | FRED | daily rate, per cent |

- Window: 30 July 2002 (first session of IEF) to 20 November 2026, both included.
- Calendar: sessions on which SPY, EFA and IEF all have a price.
- Daily simple returns. Equity block `E = 0.60 × SPY + 0.40 × EFA` (fixed mix, rebalanced
  daily). Bond block `B = IEF`.
- Cash return on day *t* = DTB3 of the previous available day / 100 / 252.
- The raw downloads are stored locally with their SHA-256 in `data/MANIFEST.json`. Yahoo
  revises adjusted prices, so a later download can move the figures slightly; the manifest
  identifies the files this run used.

## 3. The rule

1. **Risk estimate.** RiskMetrics exponentially weighted covariance of the daily returns of
   (E, B), zero mean, decay λ = 0.94: `Σ_t = 0.94 × Σ_{t−1} + 0.06 × r_t r_t'`. It is
   initialised with the second-moment matrix of the first 60 sessions; no decision is taken
   during the first 126 sessions.
2. **Decision.** On the last session τ of each calendar week, compute the annualised ex-ante
   volatility `σ(w) = sqrt(252 × w' Σ_τ w)` of every mix `w = (w_E, 1 − w_E)` on the grid
   `w_E = 20%, 21%, …, 80%`. The target is **the largest equity weight whose ex-ante
   volatility is at most 8%**. If no mix on the grid meets 8%, the target is the mix with the
   lowest ex-ante volatility on the grid.
3. **Execution.** The target decided at the close of τ is traded at the close of the next
   session τ+1 and earns returns from τ+2 (signal at T−1, trade at T). Between two trades the
   portfolio is held at its standing target. Fees are not charged: Article 5.2 of the Rules
   excludes them. Turnover is reported.

Every parameter is fixed here and none was tuned: λ = 0.94 is the RiskMetrics daily
convention, 8% is the cap minus a two-point margin, 63 sessions is one quarter.

## 4. Comparators

- **STATIC** — a constant mix whose equity weight is the time-average of the rule's weights
  over the evaluation sample, rounded to the nearest per cent. Same average exposure, no
  adjustment.
- **FLOOR** — constant 20% equities, 80% Treasuries: the least equity the mandate allows.
  It measures what no rule could have avoided.
- **60/40** — for reference only.

All portfolios are evaluated on the same days: from the first day a rule weight is in force
to 20 November 2026.

## 5. Metric

`V_t` = annualised realised volatility of the last 63 sessions (standard deviation of daily
returns × √252). Sixty-three sessions is about the length of the Challenge's management
period. A day is a **breach** when `V_t > 10%`. The breach frequency `BF` of a portfolio is
the share of days in breach, over all days with a complete window.

## 6. Hypotheses and decision rules

Two tests form the family. Confidence bounds are one-sided at the Šidák-adjusted level for
two tests and a 5% family level: 1 − (1 − 0.05)^(1/2) = 2.53% per test.

**H1 (primary) — the rule breaches the cap less often than the static mix.**
Statistic `Δ = BF(STATIC) − BF(RULE)`, the mean of `d_t = breach_STATIC,t − breach_RULE,t`.
Inference by stationary bootstrap of `d_t` (Politis and Romano, 1994), mean block length
252 sessions, 10,000 resamples, seed 20261124. `L1` is the 2.53% quantile of the bootstrap
means.
- **PASS** if `L1 > 0`.
- **FAIL** if `Δ ≤ 0`.
- **NOT SHOWN** otherwise.

**H2 (secondary) — the rule does not cost risk-adjusted return.**
Statistic `S = Sharpe(RULE) − Sharpe(STATIC)`, each Sharpe ratio computed on daily returns in
excess of cash and annualised by √252. Inference by paired stationary bootstrap of the two
excess-return series (same resampled days), mean block length 63 sessions, 10,000
resamples, seed 20261125. `L2` and `U2` are the 2.53% and 97.47% quantiles of the bootstrap
distribution of `S`.
- **NON-INFERIOR** if `L2 > −0.10`.
- **INFERIOR** if `U2 < −0.10`.
- **NOT SHOWN** otherwise; the half-width `(U2 − L2) / 2` is then reported as what this
  sample can detect.

We do **not** test whether the rule raises returns, and we will not claim that it does.

## 7. What each outcome commits us to

- H1 **FAIL** or **NOT SHOWN**: we do not present volatility budgeting as our risk control,
  and the application says so.
- H1 **PASS**: the rule is our first line of defence. The breaches that remain are reported
  with their dates, and with the share that FLOOR also breaches.
- H2 anything but **NON-INFERIOR**: we state that the rule is a risk control whose effect on
  return this sample cannot settle.

## 8. Reported whatever the outcome

For RULE, STATIC, FLOOR and 60/40: breach frequency, highest `V_t`, the dated breach
episodes, annualised return in excess of cash, full-sample volatility, Sharpe ratio, maximum
drawdown. For RULE also: mean, minimum and maximum equity weight, share of weeks at the 20%
and 80% bounds, annual turnover, and the share of its breach days on which FLOOR is also in
breach. For information only: the Newey–West (6 lags) t-statistic of the mean daily return
difference RULE − STATIC.

## 9. Descriptive exhibit, no test — the currency inside the euro sovereign sleeve

The portfolio is valued in US dollars and may not use derivatives, so euro-area sovereign
bonds cannot be currency-hedged. We describe what that does to their risk, with no
hypothesis and no decision attached.

- Euro sovereigns 7–10 years: iShares € Govt Bond 7-10yr UCITS ETF (IBGM.AS, in euros),
  adjusted close, Yahoo Finance. EUR/USD: `EURUSD=X` close, Yahoo Finance.
- Weekly returns from the last available observation of each calendar week, first week of
  2008 to 20 November 2026, so that the different closing times of European and US markets
  do not distort the figures. Annualised by √52.
- Reported: annualised volatility of E, of IEF, of the euro sovereign fund in euros, of the
  same fund in US dollars, and of EUR/USD; the correlation of each with E; the mean weekly
  return of each during the worst 10% of weeks for E.

## 10. What we will not do

- No second specification, no parameter search, no sub-period chosen after reading.
- A defect in the code may be corrected if the specification is untouched; every execution
  is logged in `RUNLOG.md` with its date and reason.
