"""Step 3/4: the frozen strategies and baselines over every period and classifier, plus attribution.
Writes results/s3_backtest.json and results/s3_monthly.csv."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mo.config import RESULTS  # noqa: E402
from mo import macro  # noqa: E402
from mo.backtest import returns_panel, metrics, PROXY, mret, spliced  # noqa: E402
from mo.strategies import build  # noqa: E402

PERIODS = {"P1": ("2007-04", "2026-09"), "P0": ("2000-10", "2007-03"),
           "Pold": ("2011-02", "2026-05"), "Pall": ("2000-10", "2026-09")}
CLASSIFIERS = ["rt_raw", "rt_smooth3_persist3", "revised_lag2"]

rf = macro.tbill_monthly()
labels = pd.read_csv(RESULTS / "s1_regimes.csv", index_col=0)
labels.index = pd.PeriodIndex(labels.index, freq="M")
rets = returns_panel()

out = {"proxy_check": {}, "periods": PERIODS, "results": {}, "attribution": {}, "regime_months": {}}

# Proxy check on the overlap, as specified.
for etf, (p, add_rf) in PROXY.items():
    e = mret(etf).iloc[1:]
    pr = mret(p) + (rf.reindex(mret(p).index) if add_rf else 0)
    j = pd.concat([e, pr], axis=1, keys=["e", "p"]).dropna().loc["2007-05":]
    d = j.e - j.p
    out["proxy_check"][etf] = {"proxy": p, "plus_tbill": add_rf, "corr": round(float(j.e.corr(j.p)), 3),
                               "te_pct": round(float(100 * d.std() * np.sqrt(12)), 2),
                               "ann_mean_diff_pct": round(float(1200 * d.mean()), 2)}

monthly = {}
for cl in CLASSIFIERS:
    for per, (s, e) in PERIODS.items():
        res, W = build(labels[cl], rets, s, e)
        key = f"{cl}|{per}"
        out["results"][key] = {}
        for name, bt in res.items():
            m = metrics(bt.net, rf)
            m["turnover_per_year"] = round(float(bt.turnover.mean() * 12), 3)
            m["cost_drag_bps_per_year"] = round(float(bt.cost.mean() * 12 * 1e4), 2)
            m["avg_fund_weight"] = round(float(W[name]["FUND"].mean()), 3)
            out["results"][key][name] = m
            monthly[(key, name)] = bt.net
        # Attribution: K - Fund = (S-K - Fund) + (K - S-K), in arithmetic annualised excess return
        # and in Sharpe and drawdown.
        mean = {n: float(res[n].net.mean() * 1200) for n in ("K", "Fund", "S-K")}

        def _sh(x):
            ex = res[x].net - rf.reindex(res[x].net.index)
            return float(ex.mean() / ex.std() * np.sqrt(12))
        k, f, sk = ({"sharpe": _sh(x), "maxdd_pct": out["results"][key][x]["maxdd_pct"]} for x in ("K", "Fund", "S-K"))
        out["attribution"][key] = {
            "ret_total_pp": round(mean["K"] - mean["Fund"], 2),
            "ret_static_pp": round(mean["S-K"] - mean["Fund"], 2),
            "ret_timing_pp": round(mean["K"] - mean["S-K"], 2),
            "sharpe_total": round(k["sharpe"] - f["sharpe"], 3),
            "sharpe_static": round(sk["sharpe"] - f["sharpe"], 3),
            "sharpe_timing": round(k["sharpe"] - sk["sharpe"], 3),
            "maxdd_total_pp": round(k["maxdd_pct"] - f["maxdd_pct"], 2),
            "maxdd_static_pp": round(sk["maxdd_pct"] - f["maxdd_pct"], 2),
            "maxdd_timing_pp": round(k["maxdd_pct"] - sk["maxdd_pct"], 2),
            "static_weights": {a: round(float(v), 3) for a, v in W["S-K"].iloc[0].items() if v > 0},
        }
        dec = pd.period_range(pd.Period(s, "M") - 1, pd.Period(e, "M") - 1, freq="M")
        out["regime_months"][key] = labels[cl].reindex(dec).value_counts().to_dict()

pd.DataFrame(monthly).to_csv(RESULTS / "s3_monthly.csv")
(RESULTS / "s3_backtest.json").write_text(json.dumps(out, indent=1))

for key, block in out["results"].items():
    print(f"== {key}  regimes={out['regime_months'][key]}")
    print(pd.DataFrame(block).T[["cagr_pct", "vol_pct", "sharpe", "maxdd_pct", "worst12_pct", "turnover_per_year", "avg_fund_weight"]].to_string())
    print("   attribution:", {k: v for k, v in out["attribution"][key].items() if k != "static_weights"})
