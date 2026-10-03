"""Monthly backtest: asset returns with proxy splicing, strategy weights, drift-aware turnover and costs."""
import numpy as np
import pandas as pd

from .data import monthly_returns
from . import macro

# ETF -> (proxy, add T-bill to proxy return). Chosen on the 2007-05..2026-09 overlap (EVAL_LOG Step 3).
PROXY = {
    "HYG": ("VWEHX", False), "SHY": ("VFISX", False), "IEF": ("VFITX", False),
    "TLT": ("VUSTX", False), "GLD": ("GC=F", False), "DBC": ("^SPGSCI", True),
    "UUP": ("DX-Y.NYB", True),
}
COST_BPS = {"FUND": 0, "HYG": 2, "GLD": 1, "DBC": 5, "SHY": 1, "UUP": 3, "IEF": 1, "TLT": 1}

K_TABLE = {
    "Goldilocks":   {"FUND": 0.90, "HYG": 0.10},
    "Reflation":    {"FUND": 0.55, "HYG": 0.10, "GLD": 0.30, "DBC": 0.05},
    "Disinflation": {"FUND": 0.80, "HYG": 0.10, "GLD": 0.10},
    "Stagflation":  {"FUND": 0.25, "GLD": 0.25, "SHY": 0.30, "UUP": 0.20},
}
G_TABLE = {
    "Goldilocks":   {"FUND": 1.00},
    "Reflation":    {"FUND": 0.70, "SHY": 0.15, "GLD": 0.15},
    "Disinflation": {"FUND": 0.70, "SHY": 0.15, "GLD": 0.15},
    "Stagflation":  {"FUND": 0.70, "SHY": 0.15, "GLD": 0.15},
}
ASSETS = ["FUND", "HYG", "GLD", "DBC", "SHY", "UUP", "IEF", "TLT"]


def mret(ticker):
    r = monthly_returns(ticker)
    r.index = r.index.to_period("M")
    return r


def first_full_month(ticker):
    r = mret(ticker)
    return r.index[0]


def spliced(etf):
    """ETF return from its first full month; proxy before."""
    rf = macro.tbill_monthly()
    e = mret(etf)
    e = e.iloc[1:]  # the first monthly change may start mid-month
    p, add_rf = PROXY[etf]
    pr = mret(p)
    if add_rf:
        pr = (pr + rf.reindex(pr.index)).dropna()
    return pd.concat([pr[pr.index < e.index[0]], e]).sort_index()


def fund_series(fund="JLGMX"):
    """JLGMX from its first full month, SEEGX before. Other funds are used as they are."""
    if fund != "JLGMX":
        return mret(fund)
    a = mret("JLGMX").iloc[1:]
    b = mret("SEEGX")
    return pd.concat([b[b.index < a.index[0]], a]).sort_index()


def returns_panel(fund="JLGMX"):
    cols = {"FUND": fund_series(fund)}
    for a in ASSETS[1:]:
        cols[a] = spliced(a)
    return pd.DataFrame(cols)


def table_weights(labels, table):
    """Target weights decided at the end of each month from that month's regime label."""
    rows = {t: table[lab] for t, lab in labels.dropna().items()}
    return pd.DataFrame.from_dict(rows, orient="index").reindex(columns=ASSETS).fillna(0.0)


def run(weights, rets, start, end):
    """weights: target weights decided at the end of month t (index t), held over month t+1.
    Returns a frame indexed by return month with gross return, cost and net return.
    Turnover is measured against the weights after drift over the previous month."""
    months = pd.period_range(start, end, freq="M")
    W = weights.reindex(columns=ASSETS).fillna(0.0)
    cost = pd.Series(COST_BPS).reindex(ASSETS).fillna(0.0).values / 1e4
    prev = None
    out = []
    for m in months:
        t = m - 1
        w = W.loc[t].values
        r = rets.loc[m, ASSETS].values
        used = w != 0
        if np.isnan(r[used]).any():
            raise ValueError(f"missing return for an asset with weight in {m}")
        r = np.where(used, r, 0.0)
        turn = np.abs(w - prev) if prev is not None else np.abs(w)
        c = float(turn @ cost)
        gross = float(w @ r)
        out.append((m, gross, c, gross - c, float(turn.sum())))
        drift = w * (1 + r)
        prev = drift / drift.sum() if drift.sum() != 0 else w
    return pd.DataFrame(out, columns=["month", "gross", "cost", "net", "turnover"]).set_index("month")


def metrics(r, rf):
    """r: monthly net returns. Sharpe uses arithmetic monthly excess returns."""
    r = r.dropna()
    ex = r - rf.reindex(r.index)
    w = (1 + r).cumprod()
    wealth = pd.concat([pd.Series([1.0]), w.reset_index(drop=True)])
    dd = wealth / wealth.cummax() - 1
    yrs = len(r) / 12
    roll12 = (1 + r).rolling(12).apply(np.prod, raw=True) - 1
    return {
        "months": int(len(r)),
        "cagr_pct": round(100 * (w.iloc[-1] ** (1 / yrs) - 1), 2),
        "vol_pct": round(100 * r.std() * np.sqrt(12), 2),
        "sharpe": round(float(ex.mean() / ex.std() * np.sqrt(12)), 3),
        "maxdd_pct": round(100 * float(dd.min()), 2),
        "worst12_pct": round(100 * float(roll12.min()), 2),
        "end_value_per_1": round(float(w.iloc[-1]), 4),
    }
