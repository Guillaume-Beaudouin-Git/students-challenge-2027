"""What markets priced for US policy rates and inflation at the close of 20 November 2026.

Descriptive. Federal funds futures (Yahoo Finance, CBOT) give the average effective rate expected for
a month: 100 minus the price. Treasury yields, the five-year inflation compensation and the five-year
real yield come from FRED (series DGS2, DGS5, DGS10, T5YIE, DFII5), fetched with curl because the
site times out from Python on this machine.

    python3 market_pricing.py > outputs/market_pricing.txt
"""
import subprocess
import warnings

warnings.filterwarnings("ignore")

import yfinance as yf

CUT = "2026-11-20"
for series in ("DFEDTARL", "DFEDTARU", "EFFR", "DGS2", "DGS5", "DGS10", "T5YIE", "DFII5"):
    csv = subprocess.run(["curl", "-s", "--max-time", "30", f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}&cosd=2026-11-16&coed={CUT}"],
                         capture_output=True, text=True).stdout.strip().splitlines()
    print(f"FRED {series}: {csv[-1] if csv else 'no data'}")
for ticker, label in (("ZQZ26.CBT", "December 2026"), ("ZQF27.CBT", "January 2027"), ("ZQM27.CBT", "June 2027"), ("ZQZ27.CBT", "December 2027")):
    df = yf.download(ticker, start="2026-11-10", end="2026-11-21", auto_adjust=False, progress=False, threads=False)
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    c = df["Close"].dropna()
    print(f"fed funds future {label} ({ticker}): close {float(c.iloc[-1]):.3f} on {c.index[-1].date()} -> average effective rate expected {100 - float(c.iloc[-1]):.2f}%")
