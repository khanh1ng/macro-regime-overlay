"""Step 2: does the regime known at the end of month t predict returns in month t+1?
For each asset and classifier: mean excess return by regime with Newey-West errors, and a Wald test
that all four regime means are equal. Writes results/s2_predict.json."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mo.config import RESULTS  # noqa: E402
from mo.data import monthly_returns  # noqa: E402
from mo import macro, regime as R  # noqa: E402
from mo.stats import ols_hac, wald, contrast  # noqa: E402

ASSETS = ["SEEGX", "SPY", "IWF", "QQQ", "IEF", "TLT", "SHY", "TIP", "GLD", "HYG", "UUP", "DBC"]
CLASSIFIERS = ["rt_raw", "rt_smooth3_persist3", "revised_lag2"]
HAC = 6

labels = pd.read_csv(RESULTS / "s1_regimes.csv", index_col=0)
labels.index = pd.PeriodIndex(labels.index, freq="M")
rf = macro.tbill_monthly()


def excess(ticker):
    r = monthly_returns(ticker)
    r.index = r.index.to_period("M")
    return (r - rf.reindex(r.index)).dropna()


def test(y, lab):
    """y: excess return in month t+1; lab: regime at the end of month t."""
    d = pd.concat([y.rename("y"), lab.shift(1).rename("reg")], axis=1).dropna()
    X = pd.get_dummies(d.reg).reindex(columns=R.REGIMES, fill_value=0).astype(float)
    keep = list(X.columns[X.sum() >= 1])
    b, V = ols_hac(d.y.values, X[keep].values, HAC)
    se = np.sqrt(np.diag(V))
    out = {"months": int(len(d)), "start": str(d.index[0]), "by_regime": {}}
    for j, k in enumerate(keep):
        sub = d.y[d.reg == k]
        out["by_regime"][k] = {
            "n": int(len(sub)),
            "ann_excess_pct": round(1200 * float(sub.mean()), 2),
            "ann_vol_pct": round(100 * float(sub.std() * np.sqrt(12)), 2),
            "sharpe": round(float(sub.mean() / sub.std() * np.sqrt(12)), 2),
            "t_hac": round(float(b[j] / se[j]), 2),
        }
    k = len(keep)
    Rm = np.zeros((k - 1, k))
    for j in range(k - 1):
        Rm[j, j], Rm[j, j + 1] = 1, -1
    out["wald_equal_means_p"] = round(wald(b, V, Rm)[1], 4)
    if "Stagflation" in keep:
        c = [1.0 if x == "Stagflation" else -1.0 / (k - 1) for x in keep]
        est, t = contrast(b, V, c)
        out["stagflation_minus_others_ann_pct"] = round(1200 * est, 2)
        out["stagflation_minus_others_t"] = round(t, 2)
    return out


res = {}
for cl in CLASSIFIERS:
    res[cl] = {a: test(excess(a), labels[cl]) for a in ASSETS}

# Sub-periods: before the overlay's evaluation window, and the window itself (decisions from 2007-03).
PERIODS = {"pre_2007_03": (None, "2007-03"), "from_2007_04": ("2007-04", None)}
res_sub = {per: {cl: {a: test(excess(a).loc[s0:s1], labels[cl]) for a in ASSETS
                      if len(excess(a).loc[s0:s1]) >= 60}
                 for cl in CLASSIFIERS}
           for per, (s0, s1) in PERIODS.items()}

# Smallest Stagflation contrast for the fund that a 5% two-sided test would detect with 80% power:
# (1.96 + 0.84) times the standard error implied by the reported estimate and t-statistic.
mde = {}
for per, block in [("full", res)] + list(res_sub.items()):
    r = block["rt_raw"]["SEEGX"]
    se = abs(r["stagflation_minus_others_ann_pct"] / r["stagflation_minus_others_t"])
    mde[per] = {"estimate": r["stagflation_minus_others_ann_pct"], "se": round(se, 2),
                "min_detectable_ann_pct": round(2.8 * se, 2)}

n_tests = len(CLASSIFIERS) * len(ASSETS)
summary = {}
for cl in CLASSIFIERS:
    ps = {a: res[cl][a]["wald_equal_means_p"] for a in ASSETS}
    summary[cl] = {
        "wald_p": ps,
        "n_p_below_0.05": int(sum(p < 0.05 for p in ps.values())),
        "n_p_below_bonferroni": int(sum(p < 0.05 / n_tests for p in ps.values())),
        "stagflation_contrast_fund": (res[cl]["SEEGX"].get("stagflation_minus_others_ann_pct"),
                                      res[cl]["SEEGX"].get("stagflation_minus_others_t")),
    }
out = {"hac_lags": HAC, "n_tests": n_tests, "bonferroni_level": round(0.05 / n_tests, 5),
       "summary": summary, "fund_stagflation_mde_rt_raw": mde, "full": res, **res_sub}
(RESULTS / "s2_predict.json").write_text(json.dumps(out, indent=1))
print(json.dumps(summary, indent=1))
print(json.dumps(mde, indent=1))
