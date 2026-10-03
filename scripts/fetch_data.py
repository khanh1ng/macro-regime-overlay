"""Download every input into data/. No API key is needed.

    python scripts/fetch_data.py

* Yahoo Finance: daily close, adjusted close and every distribution for the funds, ETFs and the
  long-history proxies (data/raw/).
* FRED: CPI (not seasonally adjusted and adjusted), current industrial production, 3-month T-bill
  (data/alfred/FRED_*.csv).
* Philadelphia Fed Real-Time Data Set: every published vintage of industrial production
  (data/alfred/iptmvmd.xlsx).

The end date is fixed in mo/config.py (END), so a later download covers the same window. Vendors can
still revise history; scripts/s0_verify.py checks the result against the fund's annual report.
"""
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mo.config import RAW, ALFRED, TICKERS, END  # noqa: E402
from mo.data import download  # noqa: E402

PROXIES = ["VWEHX", "VFISX", "VFITX", "VUSTX", "GC=F", "DX-Y.NYB", "^SPGSCI"]
OTHER_MARKETS = ["VIVAX", "NAESX", "VGTSX", "VEIEX"]
FRED = ["CPIAUCNS", "CPIAUCSL", "INDPRO", "TB3MS"]
PHILLY_IP = ("https://www.philadelphiafed.org/-/media/frbp/assets/surveys-and-data/"
             "real-time-data/data-files/xlsx/iptmvmd.xlsx")


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    ALFRED.mkdir(parents=True, exist_ok=True)
    for t in TICKERS + PROXIES + OTHER_MARKETS:
        px, _ = download(t)
        print(f"{t:9s} {px.index[0].date()} to {px.index[-1].date()} ({len(px)} days)")
        time.sleep(0.5)
    import pandas_datareader.data as web
    for s in FRED:
        web.DataReader(s, "fred", "1947-01-01", END).to_csv(ALFRED / f"FRED_{s}.csv")
        print(f"FRED {s}")
    r = requests.get(PHILLY_IP, headers={"User-Agent": "Mozilla/5.0"}, timeout=120)
    r.raise_for_status()
    (ALFRED / "iptmvmd.xlsx").write_bytes(r.content)
    print("Philadelphia Fed IP vintages")


if __name__ == "__main__":
    main()
