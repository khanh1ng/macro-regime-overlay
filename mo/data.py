"""Download and load daily prices with distributions, so total returns can be rebuilt and checked."""
import json
import time

import numpy as np
import pandas as pd
import requests

from .config import RAW, START, END

HEADERS = {"User-Agent": "Mozilla/5.0"}


def _yahoo(ticker):
    p1 = int(pd.Timestamp(START).timestamp())
    p2 = int(pd.Timestamp(END).timestamp())
    url = (f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}"
           f"?interval=1d&period1={p1}&period2={p2}&includeAdjustedClose=true"
           f"&events=div,split,capitalGain")
    for attempt in range(4):
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code == 200:
            return r.json()["chart"]["result"][0]
        time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"{ticker}: HTTP {r.status_code}")


def download(ticker):
    """Save raw close, adjusted close and every distribution event for one ticker."""
    j = _yahoo(ticker)
    idx = pd.to_datetime(j["timestamp"], unit="s").normalize()
    q = j["indicators"]
    px = pd.DataFrame({"close": q["quote"][0]["close"],
                       "adjclose": q["adjclose"][0]["adjclose"]}, index=idx)
    px = px[~px.index.duplicated(keep="last")].dropna()
    px.index.name = "date"
    px.to_csv(RAW / f"{ticker}.csv")
    ev = j.get("events", {})
    (RAW / f"{ticker}_events.json").write_text(json.dumps(ev, indent=1, sort_keys=True))
    return px, ev


def load(ticker):
    px = pd.read_csv(RAW / f"{ticker}.csv", index_col=0, parse_dates=True)
    ev = json.loads((RAW / f"{ticker}_events.json").read_text())
    return px, ev


def distributions(ev):
    """All cash distributions (dividends and capital gains) per ex-date, in $ per share."""
    rows = []
    for kind in ("dividends", "capitalGains"):
        for v in ev.get(kind, {}).values():
            rows.append((pd.to_datetime(v["date"], unit="s").normalize(), kind, v["amount"]))
    d = pd.DataFrame(rows, columns=["date", "kind", "amount"])
    return d.groupby("date")["amount"].sum() if len(d) else pd.Series(dtype=float)


def rebuilt_total_return(px, ev):
    """Daily total return from closes plus reinvested distributions:
    r_t = (P_t + D_t) / P_{t-1} - 1, with D_t paid on the ex-date.
    Yahoo closes are already split-adjusted, so splits need no further treatment."""
    c = px["close"]
    d = distributions(ev).reindex(c.index).fillna(0.0)
    return (c + d) / c.shift(1) - 1


def daily_returns(ticker):
    px, _ = load(ticker)
    return px["adjclose"].pct_change().dropna()


def monthly_returns(ticker):
    px, _ = load(ticker)
    m = px["adjclose"].resample("M").last()
    return m.pct_change().dropna()
