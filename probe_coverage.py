"""Coverage probe: first/last date and row counts only. No return or risk statistic is computed here."""
import warnings
warnings.filterwarnings("ignore")
import io
import urllib.request

import pandas as pd
import yfinance as yf

TICKERS = ["SPY", "EFA", "IEF", "SHY", "BIL", "IBGM.AS", "IBGM.L", "SXRQ.DE", "EUNH.DE", "IEGA.L", "EXX6.DE", "IGOV", "FXE", "EURUSD=X", "URTH", "GLD", "TIP"]

for t in TICKERS:
    try:
        df = yf.download(t, start="2000-01-01", auto_adjust=False, progress=False, threads=False)
        if df.empty:
            print(f"{t:10s} EMPTY")
            continue
        cols = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        print(f"{t:10s} {df.index[0].date()} -> {df.index[-1].date()}  rows={len(df):5d}  cols={sorted(set(cols))}")
    except Exception as e:  # noqa: BLE001
        print(f"{t:10s} ERROR {type(e).__name__}: {str(e)[:80]}")

for sid in ["DEXUSEU", "DTB3", "SOFR", "DGS10", "VIXCLS"]:
    try:
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
        raw = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=40).read()
        s = pd.read_csv(io.BytesIO(raw))
        print(f"FRED {sid:8s} {s.iloc[0, 0]} -> {s.iloc[-1, 0]}  rows={len(s)}")
    except Exception as e:  # noqa: BLE001
        print(f"FRED {sid:8s} ERROR {type(e).__name__}: {str(e)[:80]}")
