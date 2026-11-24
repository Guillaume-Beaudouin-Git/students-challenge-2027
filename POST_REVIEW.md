# Postscript — what an independent review took away from H1

Written on 24 November 2026, after the single run. **Nothing here is pre-registered.** The
verdicts of `PREREGISTRATION.md` stand as they were computed: H1 PASS, H2 NOT SHOWN. This note
records a harder question that a reviewer asked afterwards, and what the answer does to our
reading. Code: `post_review.py`. Output: `results/post_review.json`.

## The objection

H1 compared the rule with a constant mix holding the same *average equity weight* (58%). That
comparator was fixed before the run, but it carries more risk than the rule: 10.5% of
volatility over the sample against 8.6%. A fairer comparator holds the same *risk*.

## The answer

| 2003–2026 | Rule | Constant 47/53, same volatility | Constant 43/57, same excess return |
|---|---:|---:|---:|
| Days above the 10% cap | 13.5% | 12.9% | 10.7% |
| Highest 63-session volatility | 18.5% | 34.3% | 31.1% |
| Largest drawdown | −20.3% | −24.8% | −22.1% |
| Sharpe ratio | 0.59 | 0.62 | 0.63 |

At equal risk, a constant mix is above the cap about as often as the rule, with a slightly
better Sharpe ratio. Our comparator had flattered the rule.

## What survives

- **The extremes.** The rule's worst quarter is 18.5% of volatility against 31–34%; its largest
  loss is smaller.
- **Where the breaches fall.** In 2008–09, 2020 and 2022–23 the rule is above the cap on 387
  days, the 47/53 mix on 549. In all other years the rule is above it on 416 days, the mix on
  216. The mechanism is not that a weekly rule "sees spikes late". Calm markets take the rule
  toward its 80% ceiling (its weight averages 64% over the quarter before such an episode,
  against 58% over the sample), and one bad day then sits in a 63-session measure for a quarter.

## What would have complied

With equities at the 20% floor and the rest in 7–10-year Treasuries, volatility is above 10% on
5.8% of days. With 40% in those Treasuries and 40% in bills, on 1.1%. Maturity is a lever on the
cap as real as the equity weight; the statement in an earlier draft that "no allocation could
have complied" was wrong.

A lower target alone does not solve it either. Descriptively, on data we have now seen:

| Target | 5% | 6% | 6.5% | 7% | 7.5% | 8% |
|---|---:|---:|---:|---:|---:|---:|
| Days above the cap | 6.2% | 6.3% | 7.2% | 8.7% | 11.6% | 13.5% |

## What we commit to

The portfolio will not be run at an 8% target. Before the test allocation of 29 January we will
specify, time-stamp and run a second test combining a lower target, the maturity lever and
slower re-risking, with the criterion written here first: **at most 5% of 63-session windows
above the cap.** These data have been seen, so that test cannot be a proof. The management
period of the Challenge is the out-of-sample test.
