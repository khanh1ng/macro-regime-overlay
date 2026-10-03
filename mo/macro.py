"""Macro inputs: real-time industrial production vintages, unrevised CPI, and the T-bill rate."""
import pandas as pd

from .config import ALFRED


def _fred(series):
    s = pd.read_csv(ALFRED / f"FRED_{series}.csv", index_col=0, parse_dates=True).squeeze("columns")
    s.index = s.index.to_period("M")
    return s.astype(float)


def ip_vintages():
    """Philadelphia Fed real-time data set: rows are observation months, columns are vintages.
    Vintage 'IPTyyMm' is the data as known in the middle of month yyyy-mm."""
    x = pd.read_excel(ALFRED / "iptmvmd.xlsx")
    x.index = pd.PeriodIndex(x.pop("DATE").str.replace(":", "-"), freq="M")
    cols = {}
    for c in x.columns:
        yy, mm = c[3:].split("M")
        yy = int(yy)
        year = 1900 + yy if yy >= 62 else 2000 + yy
        cols[c] = pd.Period(f"{year}-{int(mm):02d}", freq="M")
    x = x.rename(columns=cols)
    return x.apply(pd.to_numeric, errors="coerce")


def ip_latest():
    return _fred("INDPRO")


def cpi_nsa():
    """Not seasonally adjusted CPI is never revised, so its year-on-year change is real-time
    once published (around the middle of the following month)."""
    return _fred("CPIAUCNS")


def cpi_sa():
    return _fred("CPIAUCSL")


def tbill_monthly(through="2026-09"):
    """Monthly risk-free return from the 3-month T-bill rate (percent per year).
    The latest published month is carried forward to `through` (TB3MS ends one month early)."""
    s = _fred("TB3MS") / 100 / 12
    idx = pd.period_range(s.index[0], through, freq="M")
    return s.reindex(idx).ffill()
