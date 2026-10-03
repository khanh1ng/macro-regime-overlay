"""Stationary bootstrap of differences in Sharpe ratio and maximum drawdown between strategies."""
import numpy as np

from . import macro

N_BOOT, MEAN_BLOCK, SEED = 5000, 12, 0
rf = macro.tbill_monthly()


def sharpe(ex):
    return ex.mean(axis=0) / ex.std(axis=0, ddof=1) * np.sqrt(12)


def maxdd(r):
    w = np.vstack([np.ones((1, r.shape[1])), np.cumprod(1 + r, axis=0)])
    return (w / np.maximum.accumulate(w, axis=0) - 1).min(axis=0)


def stationary_idx(n, rng):
    """Politis-Romano stationary bootstrap indices with geometric block lengths."""
    idx = np.empty(n, dtype=int)
    idx[0] = rng.integers(n)
    for i in range(1, n):
        idx[i] = rng.integers(n) if rng.random() < 1 / MEAN_BLOCK else (idx[i - 1] + 1) % n
    return idx


def boot(frame, pairs):
    """frame: monthly net returns, columns = strategies. pairs: (a, b) differences to bootstrap."""
    r = frame.values
    ex = r - rf.reindex(frame.index).values[:, None]
    cols = list(frame.columns)
    rng = np.random.default_rng(SEED)
    d_s = {p: [] for p in pairs}
    d_m = {p: [] for p in pairs}
    for _ in range(N_BOOT):
        i = stationary_idx(len(r), rng)
        s, m = sharpe(ex[i]), maxdd(r[i])
        for a, b in pairs:
            d_s[(a, b)].append(s[cols.index(a)] - s[cols.index(b)])
            d_m[(a, b)].append(100 * (m[cols.index(a)] - m[cols.index(b)]))
    s0, m0 = sharpe(ex), maxdd(r)
    out = {}
    for a, b in pairs:
        ds, dm = np.array(d_s[(a, b)]), np.array(d_m[(a, b)])
        out[f"{a} - {b}"] = {
            "sharpe_diff": round(float(s0[cols.index(a)] - s0[cols.index(b)]), 3),
            "sharpe_ci90": [round(float(x), 3) for x in np.percentile(ds, [5, 95])],
            "sharpe_ci95": [round(float(x), 3) for x in np.percentile(ds, [2.5, 97.5])],
            "sharpe_share_le0": round(float((ds <= 0).mean()), 3),
            "maxdd_diff_pp": round(float(100 * (m0[cols.index(a)] - m0[cols.index(b)])), 2),
            "maxdd_ci90": [round(float(x), 2) for x in np.percentile(dm, [5, 95])],
            "maxdd_share_le0": round(float((dm <= 0).mean()), 3),
        }
    return out
