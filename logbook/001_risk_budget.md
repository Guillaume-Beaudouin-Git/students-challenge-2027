# Entry 001 · Risk budget

| | |
|---|---|
| Date | 24 November 2026 |
| Owner | Guillaume Beaudouin (chair, risk rule) |
| Challenger | Ewan Morellec (macro seat) |
| Status | Proposal, not yet voted |
| Review | Every Friday close |

## Decision

The rule we will run targets **7%** of expected volatility, one point under the 8% we tested. On
the data of 20 November it gives an equity ceiling of **31%** (37% at 8%). We open at **30%**.

The rule, in one line: each week, hold the largest equity weight whose expected volatility is at
most the target. The committee may carry less than the ceiling, never more.

## Evidence

- VIX at 35.9 on 20 November 2026. S&P 500 down 8.6% in a week.
- Equity volatility of 23% on the rule's measure (exponentially weighted, decay 0.94).
- Ceiling by target, same data: 37% at 8%, 31% at 7%, 28% at 6.5%, 23% at 6%
  ([`descriptive/rule_ceiling_today.py`](../descriptive/rule_ceiling_today.py)).

## What is wrong with our own tool

In the backtest the 8% rule held 76% equities on 5 November 2026, the day the S&P 500 lost 4.4%,
and its three-month volatility (63 sessions) is now at 10.5%, above the mandate's cap. Calm before a shock is
the rule's weak point: low volatility takes it toward its ceiling just before volatility returns.
The pre-registered test and its postscript say the same ([`POST_REVIEW.md`](../POST_REVIEW.md)).

## What we changed

1. The target goes from 8% to 7%.
2. A ladder acts before the cap: at 8% of realised volatility no order may add risk; at 9% equities
   go halfway to our 23% floor and bonds over five years are sold into bills, each day above 9%; at
   10% on the organisers' measure equities go to 23% and every bond under two years.
3. This version has not been tested. Its specification will be time-stamped and run once before
   29 January 2027, against a criterion written now: at most 5% of 63-session windows above the cap.
4. If it fails, we hold a constant 30% in equities and keep the ladder.

## Objection

*Ewan: a low ceiling after an 11.6% fall in the S&P 500 sells at the bottom.*

Guillaume: the ceiling limits risk and takes no view on direction. It rises again as volatility falls,
by 10 points a week at most.

## Wrong if

The second test fails its criterion: we then use the fallback above.
