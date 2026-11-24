"""Download the raw series named in PREREGISTRATION.md and write data/MANIFEST.json.

Raw files stay out of git (data/raw/ is ignored); the manifest records their SHA-256.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import warnings
from datetime import datetime, timezone
from pathlib import Path

warnings.filterwarnings("ignore")

import pandas as pd  # noqa: E402
import yfinance as yf  # noqa: E402

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
START, END_INCLUSIVE = "2002-07-30", "2026-11-20"
END_EXCLUSIVE = "2026-11-21"
YAHOO = {"SPY": START, "EFA": START, "IEF": START, "IBGM.AS": "2007-12-01", "EURUSD=X": "2007-12-01"}
FRED_DTB3 = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id=DTB3&cosd=2002-07-01&coed={END_INCLUSIVE}"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, dict] = {}
    for ticker, start in YAHOO.items():
        df = yf.download(ticker, start=start, end=END_EXCLUSIVE, auto_adjust=False, progress=False, threads=False)
        if df.empty:
            raise RuntimeError(f"Yahoo returned nothing for {ticker}")
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        df = df[["Adj Close", "Close"]]
        df.index.name = "Date"
        path = RAW / f"{ticker.replace('=', '_').replace('.', '_')}.csv"
        df.to_csv(path)
        manifest[ticker] = {"file": path.name, "source": "Yahoo Finance", "rows": len(df),
                            "first": str(df.index[0].date()), "last": str(df.index[-1].date()), "sha256": _sha256(path)}
    path = RAW / "DTB3.csv"
    subprocess.run(["curl", "-sS", "-L", "--max-time", "60", "-o", str(path), FRED_DTB3], check=True)
    dtb3 = pd.read_csv(path)
    if dtb3.shape[1] != 2 or len(dtb3) < 5000:
        raise RuntimeError("FRED did not return the DTB3 series")
    manifest["DTB3"] = {"file": path.name, "source": "FRED", "rows": len(dtb3),
                        "first": str(dtb3.iloc[0, 0]), "last": str(dtb3.iloc[-1, 0]), "sha256": _sha256(path)}
    out = {"fetched_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "files": manifest}
    (ROOT / "data" / "MANIFEST.json").write_text(json.dumps(out, indent=1) + "\n")
    for name, meta in manifest.items():
        print(f"{name:9s} {meta['first']} -> {meta['last']}  rows={meta['rows']}")


if __name__ == "__main__":
    main()
