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

`probe_coverage.py` is the only script that ran before the freeze. It reads first and last
dates and row counts, and computes no return.

The data are not in the repository (Yahoo Finance and FRED, both public); the files a run
used are identified by their SHA-256 in `data/MANIFEST.json`.

Prepared with an AI coding assistant (Claude Code) under human direction. How we govern the
use of AI is described in the application file.
