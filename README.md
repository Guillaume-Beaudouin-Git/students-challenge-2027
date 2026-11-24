# The Students Challenge 2027 — evidence repository

This repository holds the one quantitative exhibit of our application file to
*The Students Challenge 2027* (Natixis Investment Managers): a test of the rule we use to
keep a portfolio under the mandate's 10% volatility cap.

The order of the commits is the point:

1. [`PREREGISTRATION.md`](PREREGISTRATION.md) — the specification, the hypotheses and the
   decision rules, committed and time-stamped (RFC 3161, see [`timestamps/`](timestamps/))
   **before** the data were downloaded and the code was run.
2. The code and its tests.
3. One execution, and its results, published whatever they are.
4. [`POST_REVIEW.md`](POST_REVIEW.md) — what an independent review took away from our
   reading of the result, what survives, and one sentence of the specification clarified.
   **Not pre-registered**: it was written after the results were known.

5. [`descriptive/`](descriptive/) — the scripts behind the other exhibits of the application file,
   with their saved outputs: the opening allocation and the allocations of our four scenarios
   (`allocation_paths.py`), three allocations replayed through seven past shocks
   (`stress_tests.py`), the base effect on Brent (`base_effect.py`), what markets priced for rates
   and inflation (`market_pricing.py`), today's ceiling of the rule at several targets
   (`rule_ceiling_today.py`), the carbon intensity of sovereign issuers (`sovereign_carbon.py`),
   the arithmetic of the stock example (`stock_example.py`), the weight of the largest AI names in
   the index (`index_concentration.py`), the bet of Logbook entry 005 with its unfavourable periods
   (`the_bet.py`) and listed proxies of private assets (`private_proxies.py`). **Descriptive, on public data, written after the results above were
   known. None of it is pre-registered.**
6. [`logbook/`](logbook/) — the Logbook: every decision written before the order and scored after
   it. Five entries so far, all proposals. Their fingerprints are time-stamped too.

## Who we are

Six students of the Master in Money, Banking, Finance and Insurance at the Université de Rennes.

| Seat | Member |
|---|---|
| Chair, risk rule | Guillaume Beaudouin |
| ESG, stewardship | Juliette Le Gall |
| Portfolio strategy, deputy chair | Tom Artur |
| Macro, sovereign bonds | Ewan Morellec |
| Equity research, data | Alexandre Le Bigaut |
| Risk control, AI register | Conrad Agossou |

`probe_coverage.py` is the only script that ran before the freeze. It reads first and last
dates and row counts, and computes no return.

The data are not in the repository (Yahoo Finance and FRED, both public); the files a run
used are identified by their SHA-256 in `data/MANIFEST.json`.

Prepared with an AI coding assistant (Claude Code) under human direction. How we govern the
use of AI is described in the application file.
