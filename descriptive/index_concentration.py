"""How much of the developed-equity index sits in the companies that buy or sell most of the AI build-out.

Descriptive. Latest published top holdings of the iShares MSCI World ETF (URTH), read through
Yahoo Finance. The six: NVIDIA, Microsoft, Alphabet (both share classes), Amazon, Broadcom, Meta.

    python3 index_concentration.py > outputs/index_concentration.txt
"""
import warnings

warnings.filterwarnings("ignore")

import yfinance as yf

SIX = ("NVDA", "MSFT", "GOOGL", "GOOG", "AMZN", "AVGO", "META")
fd = yf.Ticker("URTH").funds_data
top = fd.top_holdings
print(top.to_string())
w = top.iloc[:, -1]
print("ten largest holdings: %.1f%% of the fund" % (float(w.sum()) * 100))
print("the six AI names: %.1f%% of the fund" % (float(w[[s for s in SIX if s in w.index]].sum()) * 100))
print("sector weights, %:", {k: round(v * 100, 1) for k, v in fd.sector_weightings.items()})
