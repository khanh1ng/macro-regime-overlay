"""Growth x inflation regimes.

The decision is taken at the end of month t and applies to returns in month t+1. At that time:
- industrial production is known through month t-1 (the vintage dated t, released mid-month);
- CPI is known through month t-1 (released mid-month t; not seasonally adjusted, never revised).

Growth direction:    change over 6 months in the year-on-year growth of IP.
Inflation direction: change over 6 months in the year-on-year growth of CPI.
Regime: Goldilocks (g up, i down), Reflation (g up, i up), Disinflation (g down, i down),
Stagflation (g down, i up).
"""
import numpy as np
import pandas as pd

from . import macro

REGIMES = ["Goldilocks", "Reflation", "Disinflation", "Stagflation"]


def _label(g, i):
    out = pd.Series(np.nan, index=g.index, dtype=object)
    ok = g.notna() & i.notna()
    out[ok & (g > 0) & (i <= 0)] = "Goldilocks"
    out[ok & (g > 0) & (i > 0)] = "Reflation"
    out[ok & (g <= 0) & (i <= 0)] = "Disinflation"
    out[ok & (g <= 0) & (i > 0)] = "Stagflation"
    return out


def _direction(level):
    yoy = 100 * level.pct_change(12)
    return yoy - yoy.shift(6)


def realtime_signals(decision_months, ip_vint=None, cpi=None, extra_lag=0):
    """Growth and inflation direction as known at the end of each decision month.

    For decision month t the IP series is the vintage dated t and the last usable observation is
    the latest one it contains (normally t-1). CPI uses observations up to t-1.
    extra_lag delays both inputs by further months (sensitivity only)."""
    ip_vint = macro.ip_vintages() if ip_vint is None else ip_vint
    cpi = macro.cpi_nsa() if cpi is None else cpi
    cpi_dir = _direction(cpi)
    rows = {}
    for t in decision_months:
        v = t - extra_lag
        if v not in ip_vint.columns:
            continue
        series = ip_vint[v].dropna()
        series = series[series.index <= v - 1]
        if len(series) < 19:
            continue
        g_dir = _direction(series)
        obs = series.index[-1]
        c_obs = min(v - 1, cpi_dir.dropna().index[-1])
        rows[t] = {"g": g_dir.iloc[-1], "i": cpi_dir.get(c_obs, np.nan), "ip_obs": obs, "cpi_obs": c_obs}
    return pd.DataFrame.from_dict(rows, orient="index")


def revised_signals(decision_months, lag=2):
    """The classifier as it is usually backtested: today's revised IP, seasonally adjusted CPI,
    and a fixed publication lag."""
    g = _direction(macro.ip_latest()).shift(lag)
    i = _direction(macro.cpi_sa()).shift(lag)
    return pd.DataFrame({"g": g, "i": i}).reindex(decision_months)


def smooth(sig, window=3):
    return sig[["g", "i"]].rolling(window, min_periods=window).mean()


def classify(sig):
    return _label(sig["g"], sig["i"])


def persist(labels, k=3):
    """Switch to a new regime only after it has been observed for k consecutive months;
    otherwise keep the regime in force. Uses only current and past labels."""
    out, current, run_label, run = [], None, None, 0
    for lab in labels:
        if pd.isna(lab):
            out.append(current)
            continue
        if lab == run_label:
            run += 1
        else:
            run_label, run = lab, 1
        if current is None or (lab != current and run >= k):
            current = lab
        out.append(current)
    return pd.Series(out, index=labels.index, dtype=object)


def spells(labels):
    lab = labels.dropna()
    block = (lab != lab.shift()).cumsum()
    return lab.groupby(block).agg(["first", "size"]).rename(columns={"first": "regime", "size": "months"})
