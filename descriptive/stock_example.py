"""Arithmetic behind the stock example of the application file (Logbook entry 002).

Descriptive. Prices from Yahoo Finance; deal terms from the companies' releases of 5 October 2026
(offer of $205 a share in cash for PTC, equity value $22.6bn) and of 19 October 2026 (25 million
new Schneider shares placed at 240 euros). The share count before the placement is today's count
less those 25 million.

    python3 stock_example.py > outputs/stock_example.txt
"""
import warnings

warnings.filterwarnings("ignore")

import yfinance as yf

OFFER, EQUITY_VALUE_USD, NEW_SHARES, PLACEMENT_PRICE = 205.0, 22.6e9, 25e6, 240.0


def close(ticker: str, start: str = "2026-01-01"):
    df = yf.download(ticker, start=start, end="2026-11-21", auto_adjust=False, progress=False, threads=False)
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    return df["Close"].dropna()


su, ptc, fx = close("SU.PA"), close("PTC", "2026-09-25"), close("EURUSD=X", "2026-09-25")
before, day, last = float(su.loc["2026-10-02"]), float(su.loc["2026-10-05"]), float(su.loc["2026-11-20"])
shares_now = yf.Ticker("SU.PA").fast_info.get("shares")
shares_before = shares_now - NEW_SHARES
ptc_before = float(ptc.loc["2026-10-02"])
premium_usd = (OFFER - ptc_before) * EQUITY_VALUE_USD / OFFER
eurusd = float(fx.loc[:"2026-10-05"].iloc[-1])
lost = (before - day) * shares_before
print("Schneider close: 2 Oct %.2f | 5 Oct %.2f (%.1f%%) | 20 Nov %.2f (%.1f%% from 2 Oct) | 2026 low %.2f on %s"
      % (before, day, (day / before - 1) * 100, last, (last / before - 1) * 100, float(su.min()), su.idxmin().date()))
print("PTC close on 2 Oct %.2f -> premium of the offer %.1f%%" % (ptc_before, (OFFER / ptc_before - 1) * 100))
print("premium paid: $%.2fbn = EUR %.2fbn at %.4f" % (premium_usd / 1e9, premium_usd / eurusd / 1e9, eurusd))
print("shares before the placement: %.1fm | value lost on 5 Oct: EUR %.1fbn = %.1f times the premium"
      % (shares_before / 1e6, lost / 1e9, lost / (premium_usd / eurusd)))
print("20 Nov against the placement price of %.0f: %.1f%%" % (PLACEMENT_PRICE, (last / PLACEMENT_PRICE - 1) * 100))
print("PTC on 20 Nov: %.2f, %.1f%% under the offer" % (float(ptc.loc[:"2026-11-20"].iloc[-1]), (float(ptc.loc[:"2026-11-20"].iloc[-1]) / OFFER - 1) * 100))

# What the price assumes: the growth of free cash flow that makes the discounted flows equal the
# market value (ten years of growth, then 2.5% a year, discounted at 8.5%), and the same free-cash-flow
# yield for the two other large makers of electrical equipment. Free cash flow and market value as
# Yahoo Finance reports them (trailing twelve months), read on the day the script is run.
R, G_TERMINAL, YEARS = 0.085, 0.025, 10


def implied_growth(flow0: float, value: float) -> float:
    lo, hi = -0.5, 1.0
    for _ in range(200):
        g = (lo + hi) / 2
        flows = sum(flow0 * (1 + g) ** k / (1 + R) ** k for k in range(1, YEARS + 1))
        terminal = flow0 * (1 + g) ** YEARS * (1 + G_TERMINAL) / (R - G_TERMINAL) / (1 + R) ** YEARS
        lo, hi = (g, hi) if flows + terminal < value else (lo, g)
    return g


for ticker, name in (("SU.PA", "Schneider Electric"), ("ETN", "Eaton"), ("ABBN.SW", "ABB")):
    info = yf.Ticker(ticker).info
    fcf, mcap = info.get("freeCashflow"), info.get("marketCap")
    line = "%s: free cash flow %.2fbn, market value %.1fbn, yield %.2f%%" % (name, fcf / 1e9, mcap / 1e9, fcf / mcap * 100)
    if ticker == "SU.PA":
        line += " | growth the price needs for ten years: %.1f%% a year" % (implied_growth(fcf, mcap) * 100)
    print(line)

# What the business earns on its capital: operating income of the last fiscal year after tax, over
# invested capital, both as Yahoo Finance reports them.
_t = yf.Ticker("SU.PA")
_inc, _bs = _t.income_stmt, _t.balance_sheet
_ebit, _tax, _capital = float(_inc.loc["Operating Income"].iloc[0]), float(_inc.loc["Tax Rate For Calcs"].iloc[0]), float(_bs.loc["Invested Capital"].iloc[0])
print("Schneider, fiscal year to %s: operating income %.2fbn, tax rate %.1f%%, invested capital %.1fbn -> return on invested capital %.1f%%"
      % (_inc.columns[0].date(), _ebit / 1e9, _tax * 100, _capital / 1e9, _ebit * (1 - _tax) / _capital * 100))
