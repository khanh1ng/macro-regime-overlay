"""Step 10: independence of the hold-outs and four hold-outs of different style and region.
Writes results/s7_holdouts.json."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mo.config import RESULTS, HOLDOUT_FUNDS  # noqa: E402
from mo import macro  # noqa: E402
from mo.backtest import returns_panel, metrics  # noqa: E402
from mo.strategies import build  # noqa: E402

from mo.boot import boot  # noqa: E402

NEW = {"VIVAX": "U.S. large value", "NAESX": "U.S. small cap", "VGTSX": "International", "VEIEX": "Emerging markets"}
OLD = HOLDOUT_FUNDS + ["QQQ", "IWF", "SPY"]
ALL = ["JLGMX"] + OLD + list(NEW)
PERIODS = {"P1": ("2007-04", "2026-09"), "P0": ("2000-10", "2007-03")}
S, E = "2000-10", "2026-09"

rf = macro.tbill_monthly()
labels = pd.read_csv(RESULTS / "s1_regimes.csv", index_col=0)
labels.index = pd.PeriodIndex(labels.index, freq="M")


def neff(c):
    lam = np.linalg.eigvalsh(np.asarray(c))
    return float(lam.sum() ** 2 / (lam ** 2).sum())


panels = {f: returns_panel(f) for f in ALL}
ret = pd.DataFrame({f: panels[f]["FUND"].loc[S:E] for f in ALL})
timing = {}
for f in ALL:
    res, _ = build(labels["rt_raw"], panels[f], S, E)
    timing[f] = res["K"].net - res["S-K"].net
timing = pd.DataFrame(timing)

out = {"return_corr_with_fund": {f: round(float(ret[f].corr(ret["JLGMX"])), 3) for f in ALL[1:]},
       "timing_corr_with_fund": {f: round(float(timing[f].corr(timing["JLGMX"])), 3) for f in ALL[1:]}}
grp_old = ["JLGMX"] + OLD
out["mean_pairwise_return_corr_old"] = round(float(ret[grp_old].corr().values[np.triu_indices(7, 1)].mean()), 3)
out["mean_pairwise_timing_corr_old"] = round(float(timing[grp_old].corr().values[np.triu_indices(7, 1)].mean()), 3)
out["neff_returns_old7"] = round(neff(ret[grp_old].corr()), 2)
out["neff_timing_old7"] = round(neff(timing[grp_old].corr()), 2)
out["neff_timing_all11"] = round(neff(timing[ALL].corr()), 2)
out["neff_returns_all11"] = round(neff(ret[ALL].corr()), 2)

out["new"] = {}
for f, name in NEW.items():
    out["new"][f] = {"name": name}
    for per, (s, e) in PERIODS.items():
        res, _ = build(labels["rt_raw"], panels[f], s, e)
        b = boot(pd.DataFrame({n: res[n].net for n in ("K", "S-K")}), [("K", "S-K")])["K - S-K"]
        m = {n: metrics(res[n].net, rf) for n in ("K", "S-K", "Fund")}
        out["new"][f][per] = {"sharpe": {n: m[n]["sharpe"] for n in m}, "maxdd": {n: m[n]["maxdd_pct"] for n in m},
                              "timing_sharpe": b["sharpe_diff"], "timing_ci90": b["sharpe_ci90"],
                              "timing_maxdd_pp": b["maxdd_diff_pp"]}
pattern = [out["new"][f]["P1"]["timing_sharpe"] > 0 and out["new"][f]["P0"]["timing_sharpe"] < 0 for f in NEW]
out["new_with_pattern"] = f"{sum(pattern)}/{len(NEW)}"
out["reading"] = ("period explanation strengthened" if sum(pattern) >= 3 else
                  "timing result specific to U.S. growth equity")
(RESULTS / "s7_holdouts.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
