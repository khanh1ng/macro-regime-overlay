"""Step 12: does the real-time stock-bond correlation explain the sign of the Stagflation effect?
Writes results/s9_mechanism.json."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mo.config import RESULTS  # noqa: E402
from mo import macro  # noqa: E402
from mo.backtest import fund_series, mret  # noqa: E402
from mo.stats import ols_hac, contrast  # noqa: E402

WIN, HAC, MIN_CELL = 36, 6, 12
REG = ["Goldilocks", "Reflation", "Disinflation", "Stagflation"]
rf = macro.tbill_monthly()
fund = fund_series()
bond = mret("VFITX")
corr = fund.rolling(WIN).corr(bond.reindex(fund.index))  # known at the end of month t
labels = pd.read_csv(RESULTS / "s1_regimes.csv", index_col=0)["rt_raw"]
labels.index = pd.PeriodIndex(labels.index, freq="M")

d = pd.DataFrame({"y": (fund - rf.reindex(fund.index)).shift(-1), "reg": labels.reindex(fund.index),
                  "pos": (corr > 0).astype(float).where(corr.notna())}).dropna()
d.index.name = "decision"


def fit(df):
    cols, X = [], []
    for st in (1.0, 0.0):
        for r in REG:
            cols.append((r, st))
            X.append(((df.reg == r) & (df.pos == st)).astype(float).values)
    X = np.column_stack(X)
    keep = X.sum(axis=0) > 0
    b, V = ols_hac(df.y.values, X[:, keep], HAC)
    cols = [c for c, k in zip(cols, keep) if k]
    out = {"cells": {f"{r}|{'pos' if s else 'neg'}": int(((df.reg == r) & (df.pos == s)).sum()) for r, s in cols}}

    def c_for(st):
        c = np.zeros(len(cols))
        others = [j for j, (r, s) in enumerate(cols) if s == st and r != "Stagflation"]
        for j, (r, s) in enumerate(cols):
            if s == st and r == "Stagflation":
                c[j] = 1.0
        for j in others:
            c[j] = -1.0 / len(others)
        return c
    res = {}
    for st, name in ((1.0, "pos"), (0.0, "neg")):
        if ("Stagflation", st) in cols:
            est, t = contrast(b, V, c_for(st))
            res[name] = {"stag_minus_others_ann_pct": round(1200 * est, 2), "t": round(t, 2)}
    if "pos" in res and "neg" in res:
        est, t = contrast(b, V, c_for(1.0) - c_for(0.0))
        res["pos_minus_neg"] = {"ann_pct": round(1200 * est, 2), "t": round(t, 2)}
    out.update(res)
    return out


out = {"window_months": WIN, "first_decision": str(d.index[0]), "months": int(len(d)),
       "share_pos": {"pre_2007": round(float(d.loc[:"2007-02", "pos"].mean()), 3),
                     "post_2007": round(float(d.loc["2007-03":, "pos"].mean()), 3)},
       "stag_share_pos": {"pre_2007": round(float(d.loc[:"2007-02"].query("reg=='Stagflation'").pos.mean()), 3),
                          "post_2007": round(float(d.loc["2007-03":].query("reg=='Stagflation'").pos.mean()), 3)},
       "full": fit(d), "pre_2007": fit(d.loc[:"2007-02"]), "post_2007": fit(d.loc["2007-03":])}
f = out["full"]
pred = ("pos" in f and "neg" in f and f["pos"]["stag_minus_others_ann_pct"] > 0
        and f["neg"]["stag_minus_others_ann_pct"] < 0 and abs(f["pos_minus_neg"]["t"]) > 2)
within = []
for sub in ("pre_2007", "post_2007"):
    s = out[sub]
    ok_cells = all(s["cells"].get(f"Stagflation|{k}", 0) >= MIN_CELL for k in ("pos", "neg"))
    if ok_cells and "pos" in s and "neg" in s:
        within.append(s["pos"]["stag_minus_others_ann_pct"] > 0 > s["neg"]["stag_minus_others_ann_pct"])
out["within_subperiod_testable"] = len(within)
out["supported"] = bool(pred and any(within))
out["verdict"] = "supported" if out["supported"] else ("not identifiable" if not within else "not supported")
(RESULTS / "s9_mechanism.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
