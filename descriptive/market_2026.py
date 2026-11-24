"""What moved in 2026: returns of each asset class in the oil shock and in the AI correction (the
table of page 3 of the application file), the fall of the S&P 500 from its record, the VIX, and what
the tested rule did. Descriptive, on fund proxies; Yahoo Finance. Written on 24 November 2026.

    python3 market_2026.py > outputs/market_2026.txt
"""
import warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import yfinance as yf

def px(t, col):
    df = yf.download(t, start="2025-12-20", end="2026-11-25", auto_adjust=False, progress=False, threads=False)
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    return df[col].dropna()

S = {"SPY": "Adj Close", "EFA": "Adj Close", "URTH": "Adj Close", "IEF": "Adj Close", "TLT": "Adj Close", "SHY": "Adj Close", "BIL": "Adj Close",
     "GLD": "Adj Close", "IBGM.AS": "Adj Close", "EURUSD=X": "Close", "BZ=F": "Close", "TIP": "Adj Close", "^VIX": "Close", "^GSPC": "Close",
     "SOXX": "Adj Close", "^IXIC": "Close", "DBC": "Adj Close", "PDBC": "Adj Close"}
P = {t: px(t, c) for t, c in S.items()}

def chg(t, a, b):
    s = P[t]
    return (s.loc[:b].iloc[-1] / s.loc[:a].iloc[-1] - 1) * 100

def eur_usd(a, b):
    return ((1 + chg("IBGM.AS", a, b) / 100) * (1 + chg("EURUSD=X", a, b) / 100) - 1) * 100

for label, a, b in [("oil shock 27 Feb -> 31 Mar", "2026-02-27", "2026-03-31"), ("peak->trough 6 Oct -> 20 Nov", "2026-10-06", "2026-11-20"), ("week 13 -> 20 Nov", "2026-11-13", "2026-11-20"),
                    ("30 Oct -> 20 Nov", "2026-10-30", "2026-11-20"), ("YTD to 20 Nov", "2025-12-31", "2026-11-20"), ("YTD to 24 Nov", "2025-12-31", "2026-11-24")]:
    print(f"\n{label}")
    for t in ["^GSPC", "SPY", "URTH", "EFA", "^IXIC", "SOXX", "IEF", "TLT", "SHY", "BIL", "TIP", "GLD", "IBGM.AS", "EURUSD=X", "BZ=F", "DBC"]:
        print(f"  {t:9s} {chg(t, a, b):+7.1f}%")
    print(f"  {'EUROGOV in USD':9s} {eur_usd(a, b):+7.1f}%")

# The table of page 3 of the application file ("The market in 2026: returns in the two shocks"):
# one fund per asset class, total return in dollars, close to close.
ROWS = [("Developed equities", "URTH"), ("US Treasuries", "IEF"), ("Euro sovereigns", None), ("Gold", "GLD"),
        ("Broad commodities", "DBC"), ("Treasury bills", "BIL")]
WINDOWS = [("oil shock, 27 Feb - 31 Mar", "2026-02-27", "2026-03-31"), ("AI correction, 6 Oct - 20 Nov", "2026-10-06", "2026-11-20"),
           ("2026 to 20 Nov", "2025-12-31", "2026-11-20")]
print("\nTABLE OF PAGE 3 (fund used: URTH, IEF, IBGM.AS converted into dollars, GLD, DBC, BIL)")
print("  %-20s" % "" + "".join("%32s" % w[0] for w in WINDOWS))
for name, t in ROWS:
    print("  %-20s" % name + "".join("%31.1f%%" % (eur_usd(a, b) if t is None else chg(t, a, b)) for _, a, b in WINDOWS))

r = pd.concat({t: P[t].pct_change() for t in ("SPY", "EFA", "IEF", "GLD")}, axis=1).dropna()
e = 0.6 * r["SPY"] + 0.4 * r["EFA"]
print("\nstock-bond daily correlation (E vs IEF): last 63 sessions to 20 Nov:", round(e.loc[:"2026-11-20"].tail(63).corr(r["IEF"].loc[:"2026-11-20"].tail(63)), 2),
      "| 2026 YTD:", round(e.loc["2026":"2026-11-20"].corr(r["IEF"].loc["2026":"2026-11-20"]), 2))
print("equity-gold daily correlation 2026 YTD:", round(e.loc["2026":"2026-11-20"].corr(r["GLD"].loc["2026":"2026-11-20"]), 2))
print("S&P from 6 Oct high close to 20 Nov close: %.1f%%" % chg("^GSPC", "2026-10-06", "2026-11-20"))
print("VIX on 22 Sep, 23 Oct, 4 Nov, 5 Nov, 20 Nov:", [round(float(P["^VIX"].loc[:d].iloc[-1]), 1) for d in ("2026-09-22", "2026-10-23", "2026-11-04", "2026-11-05", "2026-11-20")])

d = pd.read_csv("../results/daily_series.csv", index_col=0, parse_dates=True)
def cum(col, a, b):
    x = d.loc[a:b, col]
    return ((1 + x).prod() - 1) * 100
print("\nRULE vs STATIC vs 60/40")
print("  5 Nov one day:    rule %.2f%% (w=%.2f)  static %.2f%%  60/40 %.2f%%" % (d.loc["2026-11-05", "r_RULE"] * 100, d.loc["2026-11-05", "w_rule"], d.loc["2026-11-05", "r_STATIC"] * 100, d.loc["2026-11-05", "r_6040"] * 100))
print("  16-20 Nov:        rule %.2f%%  static %.2f%%  60/40 %.2f%%  weights %s" % (cum("r_RULE", "2026-11-16", "2026-11-20"), cum("r_STATIC", "2026-11-16", "2026-11-20"), cum("r_6040", "2026-11-16", "2026-11-20"), d.loc["2026-11-16":"2026-11-20", "w_rule"].tolist()))
print("  7 Oct-20 Nov:     rule %.2f%%  static %.2f%%  60/40 %.2f%%" % (cum("r_RULE", "2026-10-07", "2026-11-20"), cum("r_STATIC", "2026-10-07", "2026-11-20"), cum("r_6040", "2026-10-07", "2026-11-20")))
print("  2026 YTD to 20 Nov: rule %.2f%%  static %.2f%%  60/40 %.2f%%" % (cum("r_RULE", "2026-01-01", "2026-11-20"), cum("r_STATIC", "2026-01-01", "2026-11-20"), cum("r_6040", "2026-01-01", "2026-11-20")))
print("  rule weights around: ", d.loc["2026-10-19":"2026-11-20", "w_rule"].round(2).to_dict())
