"""Step 11: robustness of the inference (specification in docs/RESEARCH_LOG.md, Step 11).
Writes results/s10_robustness.json."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mo.config import RESULTS  # noqa: E402
from mo import macro  # noqa: E402
from mo import boot as B  # noqa: E402
from mo.backtest import returns_panel  # noqa: E402
from mo.strategies import build  # noqa: E402

PERIODS = {"P1": ("2007-04", "2026-09"), "P0": ("2000-10", "2007-03"), "Pall": ("2000-10", "2026-09")}
PAIRS = [("K", "Fund"), ("S-K", "Fund"), ("K", "S-K")]
BLOCKS = (6, 12, 24)
NW_LAGS = 6
CRISIS = ("2007-10", "2009-03")

rf = macro.tbill_monthly()
labels = pd.read_csv(RESULTS / "s1_regimes.csv", index_col=0)
labels.index = pd.PeriodIndex(labels.index, freq="M")
rets = returns_panel()


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


def frame_for(per, drop=None):
    s, e = PERIODS[per]
    res, _ = build(labels["rt_raw"], rets, s, e)
    f = pd.DataFrame({k: v.net for k, v in res.items()})[["K", "S-K", "Fund"]]
    if drop:
        f = f[(f.index < pd.Period(drop[0], "M")) | (f.index > pd.Period(drop[1], "M"))]
    return f


def excess(f):
    return f.values - rf.reindex(f.index).values[:, None]


out = {"spec": "docs/RESEARCH_LOG.md, Step 11", "nw_lags": NW_LAGS, "periods": {}, "crisis_removed": {}}
for per in PERIODS:
    f = frame_for(per)
    ex = excess(f)
    cols = list(f.columns)
    row = {"months": len(f), "ledoit_wolf": {}, "bootstrap_ci90": {}}
    for a, b in PAIRS:
        row["ledoit_wolf"][f"{a} - {b}"] = ledoit_wolf(ex[:, cols.index(a)], ex[:, cols.index(b)])
    for blk in BLOCKS:
        B.MEAN_BLOCK = blk
        res = B.boot(f, PAIRS)
        row["bootstrap_ci90"][str(blk)] = {k: v["sharpe_ci90"] for k, v in res.items()}
    B.MEAN_BLOCK = 12
    sig = {}
    for a, b in PAIRS:
        k = f"{a} - {b}"
        all_ex0 = all((row["bootstrap_ci90"][str(blk)][k][0] > 0) or (row["bootstrap_ci90"][str(blk)][k][1] < 0)
                      for blk in BLOCKS)
        sig[k] = bool(all_ex0 and row["ledoit_wolf"][k]["p"] < 0.10)
    row["significant"] = sig
    out["periods"][per] = row

f = frame_for("P1", CRISIS)
ex = excess(f)
cols = list(f.columns)
res = B.boot(f, PAIRS)
out["crisis_removed"] = {"removed": list(CRISIS), "months": len(f),
                         **{k: {"sharpe_diff": v["sharpe_diff"], "ci90": v["sharpe_ci90"],
                                "ledoit_wolf": ledoit_wolf(ex[:, cols.index(k.split(' - ')[0])],
                                                           ex[:, cols.index(k.split(' - ')[1])])}
                            for k, v in res.items()}}

s2 = json.loads((RESULTS / "s2_predict.json").read_text())["fund_stagflation_mde_rt_raw"]
a, b = s2["pre_2007_03"], s2["from_2007_04"]
z = (a["estimate"] - b["estimate"]) / np.sqrt(a["se"] ** 2 + b["se"] ** 2)
out["h3_difference"] = {"pre": a["estimate"], "post": b["estimate"], "diff": round(a["estimate"] - b["estimate"], 2),
                        "z": round(float(z), 2), "p": round(float(2 * st.norm.sf(abs(z))), 4)}

(RESULTS / "s10_robustness.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
