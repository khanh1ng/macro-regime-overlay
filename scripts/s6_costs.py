"""Step 6: trading costs and turnover (specified), and timing by calendar year (exploratory, labelled).
Writes results/s6_costs.json."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mo.config import RESULTS  # noqa: E402
from mo import macro, backtest as B  # noqa: E402
from mo.strategies import build  # noqa: E402

rf = macro.tbill_monthly()
labels = pd.read_csv(RESULTS / "s1_regimes.csv", index_col=0)
labels.index = pd.PeriodIndex(labels.index, freq="M")
rets = B.returns_panel()
PERIODS = {"P1": ("2007-04", "2026-09"), "P0": ("2000-10", "2007-03")}
out = {"costs": {}, "exploratory_timing_by_year": {}, "exploratory_p1_without_2008": {}}

base = dict(B.COST_BPS)
for mult in (1, 2, 5):
    B.COST_BPS.update({k: v * mult for k, v in base.items()})
    for per, (s, e) in PERIODS.items():
        res, _ = build(labels["rt_raw"], rets, s, e)
        out["costs"][f"x{mult}|{per}"] = {
            n: {"sharpe": B.metrics(res[n].net, rf)["sharpe"],
                "cost_bps_per_year": round(float(res[n].cost.mean() * 12 * 1e4), 2),
                "turnover_per_year": round(float(res[n].turnover.mean() * 12), 3)}
            for n in ("K", "S-K", "Fund", "Trend", "G")}
B.COST_BPS.update(base)

# Exploratory: where does the timing gain come from? Annual K minus static-mix return.
res, _ = build(labels["rt_raw"], rets, "2000-10", "2026-09")
d = res["K"].net - res["S-K"].net
yr = d.groupby(d.index.year).apply(lambda x: float(np.prod(1 + res["K"].net.loc[x.index]) - np.prod(1 + res["S-K"].net.loc[x.index])))
out["exploratory_timing_by_year"] = {str(k): round(100 * v, 2) for k, v in yr.items()}

# Exploratory: P1 with the 2007-10..2009-03 crash removed from both series.
res1, _ = build(labels["rt_raw"], rets, "2007-04", "2026-09")
keep = (res1["K"].index < pd.Period("2007-10", "M")) | (res1["K"].index > pd.Period("2009-03", "M"))
for n in ("K", "S-K", "Fund"):
    out["exploratory_p1_without_2008"][n] = B.metrics(res1[n].net[keep], rf)["sharpe"]

# Exploratory: timing contribution by regime (sum of monthly K minus S-K returns, pp) and the fund's return
# in each regime, per period.
out["exploratory_timing_by_regime"] = {}
for per, (s0, e0) in PERIODS.items():
    rr, ww = build(labels["rt_raw"], rets, s0, e0)
    dd_ = rr["K"].net - rr["S-K"].net
    reg = labels["rt_raw"].shift(1).reindex(dd_.index)
    f = rets["FUND"].reindex(dd_.index)
    out["exploratory_timing_by_regime"][per] = {
        g: {"months": int((reg == g).sum()), "timing_pp": round(float(100 * dd_[reg == g].sum()), 1),
            "fund_ann_pct": round(float(1200 * f[reg == g].mean()), 1),
            "k_fund_weight": round(float(ww["K"]["FUND"].shift(1).reindex(dd_.index)[reg == g].mean()), 2)}
        for g in ("Goldilocks", "Reflation", "Disinflation", "Stagflation")}
    out["exploratory_timing_by_regime"][per]["sk_fund_weight"] = round(float(ww["S-K"]["FUND"].iloc[0]), 3)
tw = build(labels["rt_raw"], rets, "2000-10", "2007-03")[1]["Trend"]["FUND"]
out["exploratory_trend_fund_weight_2000_2002"] = round(float(tw.loc["2000-09":"2002-12"].mean()), 2)

(RESULTS / "s6_costs.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
