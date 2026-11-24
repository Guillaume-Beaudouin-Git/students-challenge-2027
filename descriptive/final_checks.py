"""Last checks of 24 November 2026, made after the second review of the application file.

Each line printed here backs a figure of the file that is not in another script's output.
Cut-off for market data: close of Friday 20 November 2026 (the rebound of Monday 23 is quoted
in a source note only). Company figures are those Yahoo Finance returns on the day of the run.

    python3 final_checks.py > outputs/final_checks.txt

The free-cash-flow yields of the three candidates of entry 002 and the allocation's expected return
are in stock_example.py and allocation_paths.py.
"""
import warnings

warnings.filterwarnings("ignore")

import pandas as pd
import yfinance as yf
from scipy.optimize import brentq

CUT = "2026-11-20"
R, G_TERMINAL, YEARS = 0.085, 0.025, 10


def closes(ticker: str, start: str = "2025-09-01") -> pd.Series:
    df = yf.download(ticker, start=start, end="2026-11-25", auto_adjust=False, progress=False, threads=False)
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    return df["Close"].dropna()


def implied_growth(fcf: float, value: float) -> float:
    """Constant growth of a cash flow over ten years that justifies `value`."""
    def gap(g: float) -> float:
        flows = sum(fcf * (1 + g) ** t / (1 + R) ** t for t in range(1, YEARS + 1))
        terminal = fcf * (1 + g) ** YEARS * (1 + G_TERMINAL) / (R - G_TERMINAL) / (1 + R) ** YEARS
        return flows + terminal - value
    return brentq(gap, -0.5, 1.0)


# 1 · the rebound quoted in the source note of page 3
sp, vix = closes("^GSPC"), closes("^VIX")
print("S&P 500: close 20 Nov %.2f, close 23 Nov %.2f, change %+.2f%% | VIX close 23 Nov %.2f"
      % (sp.loc[CUT], sp.loc["2026-11-23"], (sp.loc["2026-11-23"] / sp.loc[CUT] - 1) * 100, vix.loc["2026-11-23"]))

# 2 · the base effect on US crude (page 3, "where we differ")
wti = closes("CL=F", start="2025-01-01")
monthly = wti.resample("M").mean()
m = lambda ym: float(monthly.loc[monthly.index.strftime("%Y-%m") == ym].iloc[0])
last = float(wti.loc[:CUT].iloc[-1])
print("WTI futures: monthly average Oct 2025 %.1f, Mar 2026 %.1f, Oct 2026 %.1f | close 20 Nov %.1f"
      % (m("2025-10"), m("2026-03"), m("2026-10"), last))
print("WTI over a year: October 2026 %+.0f%% | March 2027 if the price stays at the 20 Nov close %+.0f%%"
      % ((m("2026-10") / m("2025-10") - 1) * 100, (last / m("2026-03") - 1) * 100))

# 3 · Schneider Electric (Entry 002): one basis for the yield and for the implied growth
tk = yf.Ticker("SU.PA")
info, cf = tk.info, tk.cashflow
fcf, mcap = info["freeCashflow"], info["marketCap"]
ev = mcap + (info.get("totalDebt") or 0.0) - (info.get("totalCash") or 0.0)
print("Schneider: free cash flow, trailing %.2f bn | market value %.1f bn | yield %.2f%%" % (fcf / 1e9, mcap / 1e9, fcf / mcap * 100))
print("Schneider: implied ten-year growth of that cash flow at %.1f%% discount, %.1f%% terminal growth: "
      "%.2f%% against market value (the basis of the 4.0%% yield) | %.2f%% against enterprise value (earlier draft, mixed basis)"
      % (R * 100, G_TERMINAL * 100, implied_growth(fcf, mcap) * 100, implied_growth(fcf, ev) * 100))
ocf25, capex25 = float(cf.loc["Operating Cash Flow"].iloc[0]), float(cf.loc["Capital Expenditure"].iloc[0])
print("Schneider 2025 accounts: operating cash flow %.2f bn, capital expenditure %.2f bn, kept %.0f%%"
      % (ocf25 / 1e9, -capex25 / 1e9, (ocf25 + capex25) / ocf25 * 100))

# 4 · the three AI spenders named on pages 3 and 8, same measure
ocf = capex = 0.0
for t in ("MSFT", "GOOGL", "META"):
    q = yf.Ticker(t).quarterly_cashflow
    cols = list(q.columns[:4])
    ocf += float(q.loc["Operating Cash Flow", cols].sum())
    capex += -float(q.loc["Capital Expenditure", cols].sum())
print("Microsoft + Alphabet + Meta, last four quarters: operating cash flow %.1f bn, capital expenditure %.1f bn (%.0f%%), kept %.0f%%"
      % (ocf / 1e9, capex / 1e9, capex / ocf * 100, (1 - capex / ocf) * 100))
