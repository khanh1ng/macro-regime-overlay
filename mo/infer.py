"""Inference for Sharpe-ratio differences: Ledoit-Wolf (2008) HAC test and the significance rule of
Step 11 (every stationary-bootstrap 90% interval excludes zero and Ledoit-Wolf p < 0.10)."""
import numpy as np
from scipy import stats as st

from . import boot as B

NW_LAGS = 6
BLOCKS = (6, 12, 24)


def newey_west(y, lags):
    """HAC covariance of the mean of the columns of y (T x k), Bartlett kernel."""
    y = y - y.mean(axis=0)
    T = len(y)
    S = y.T @ y / T
    for j in range(1, lags + 1):
        G = y[j:].T @ y[:-j] / T
        S += (1 - j / (lags + 1)) * (G + G.T)
    return S


def ledoit_wolf(ex1, ex2, lags=NW_LAGS):
    """Ledoit and Wolf (2008) HAC test of SR1 - SR2 (monthly excess returns). Returns the annualised
    difference, its standard error and the two-sided p-value."""
    x = np.column_stack([ex1, ex2, ex1 ** 2, ex2 ** 2])
    T = len(x)
    m1, m2, g1, g2 = x.mean(axis=0)
    diff = m1 / np.sqrt(g1 - m1 ** 2) - m2 / np.sqrt(g2 - m2 ** 2)
    grad = np.array([g1 / (g1 - m1 ** 2) ** 1.5, -g2 / (g2 - m2 ** 2) ** 1.5,
                     -0.5 * m1 / (g1 - m1 ** 2) ** 1.5, 0.5 * m2 / (g2 - m2 ** 2) ** 1.5])
    se = np.sqrt(grad @ newey_west(x, lags) @ grad / T)
    return dict(diff_ann=round(float(diff * np.sqrt(12)), 3), se_ann=round(float(se * np.sqrt(12)), 3),
                p=round(float(2 * st.norm.sf(abs(diff / se))), 4))


def compare(frame, pairs, rf):
    """Ledoit-Wolf and bootstrap intervals at every block length, and the significance verdict."""
    ex = frame.values - rf.reindex(frame.index).values[:, None]
    cols = list(frame.columns)
    out = {}
    cis = {}
    for blk in BLOCKS:
        B.MEAN_BLOCK = blk
        cis[blk] = B.boot(frame, pairs)
    B.MEAN_BLOCK = 12
    for a, b in pairs:
        k = f"{a} - {b}"
        lw = ledoit_wolf(ex[:, cols.index(a)], ex[:, cols.index(b)])
        ci = {str(blk): cis[blk][k]["sharpe_ci90"] for blk in BLOCKS}
        excl = all(v[0] > 0 or v[1] < 0 for v in ci.values())
        out[k] = {"sharpe_diff": cis[12][k]["sharpe_diff"], "ci90": ci, "ledoit_wolf": lw,
                  "maxdd_diff_pp": cis[12][k]["maxdd_diff_pp"], "significant": bool(excl and lw["p"] < 0.10)}
    return out
