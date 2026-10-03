"""Step 5: bootstrap intervals, deflated Sharpe, and hold-out funds. Writes results/s5_stats.json."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mo.config import RESULTS, HOLDOUT_FUNDS  # noqa: E402
from mo import macro  # noqa: E402
from mo.backtest import returns_panel, metrics  # noqa: E402
from mo.strategies import build  # noqa: E402
from mo.boot import boot  # noqa: E402

PERIODS = {"P1": ("2007-04", "2026-09"), "P0": ("2000-10", "2007-03"), "Pall": ("2000-10", "2026-09")}

rf = macro.tbill_monthly()
labels = pd.read_csv(RESULTS / "s1_regimes.csv", index_col=0)
labels.index = pd.PeriodIndex(labels.index, freq="M")


def deflated_sharpe(ex, sr_trials, n_trials):
    """Bailey and Lopez de Prado (2014). Monthly Sharpe ratios; returns the probability that the
    true Sharpe exceeds the expected maximum of n_trials unskilled trials."""
    ex = np.asarray(ex)
    T = len(ex)
    sr = ex.mean() / ex.std(ddof=1)
    g3 = st.skew(ex)
    g4 = st.kurtosis(ex, fisher=False)
    v = np.var(sr_trials, ddof=1)
    gamma = 0.5772156649
    sr0 = np.sqrt(v) * ((1 - gamma) * st.norm.ppf(1 - 1 / n_trials) + gamma * st.norm.ppf(1 - 1 / (n_trials * np.e)))
    z = (sr - sr0) * np.sqrt(T - 1) / np.sqrt(1 - g3 * sr + (g4 - 1) / 4 * sr ** 2)
    return {"sr_monthly": round(float(sr), 4), "sr0_monthly": round(float(sr0), 4),
            "n_trials": int(n_trials), "var_sr_trials": round(float(v), 6), "dsr": round(float(st.norm.cdf(z)), 3)}


out = {"bootstrap": {}, "deflated": {}, "holdout": {}}
rets = returns_panel()
monthly = pd.read_csv(RESULTS / "s3_monthly.csv", header=[0, 1], index_col=0)
monthly.index = pd.PeriodIndex(monthly.index, freq="M")

# Bootstrap on the main classifier.
for per, (s, e) in PERIODS.items():
    res, _ = build(labels["rt_raw"], rets, s, e)
    frame = pd.DataFrame({k: v.net for k, v in res.items()})
    out["bootstrap"][per] = boot(frame, [("K", "Fund"), ("K", "S-K"), ("K", "Trend"), ("S-K", "Fund")])

# Deflated Sharpe for K in P1. Trials: the configurations in the old notebook (counted in the log)
# plus every distinct configuration run on these data in Step 3.
OLD_TRIALS = 40
p1 = monthly.loc["2007-04":"2026-09"]
cfg = {}
for (key, name), col in p1.items():
    cl, per = key.split("|")
    if per != "P1":
        continue
    tag = name if name in ("Fund", "60/40", "VolTarget", "Trend", "90/10 GLD") else f"{name}|{cl}"
    cfg[tag] = col.dropna()
ex_cfg = {k: v - rf.reindex(v.index) for k, v in cfg.items()}
sr_trials = [v.mean() / v.std(ddof=1) for v in ex_cfg.values()]
n_trials = OLD_TRIALS + len(cfg)
out["deflated"]["K_rt_raw_P1"] = deflated_sharpe(ex_cfg["K|rt_raw"], sr_trials, n_trials)
out["deflated"]["K_rt_raw_P1"]["configs_here"] = len(cfg)
for tag in ("S-K|rt_raw", "Trend", "Fund"):
    out["deflated"][tag] = deflated_sharpe(ex_cfg[tag], sr_trials, n_trials)

# Hold-out: the frozen K and its static mix with the fund replaced by other growth funds and indices.
for f in HOLDOUT_FUNDS + ["QQQ", "IWF", "SPY"]:
    rp = returns_panel(f)
    out["holdout"][f] = {}
    for per in ("P1", "P0"):
        s, e = PERIODS[per]
        res, _ = build(labels["rt_raw"], rp, s, e)
        mk = {n: metrics(res[n].net, rf) for n in ("K", "S-K", "Fund", "Trend")}
        b = boot(pd.DataFrame({n: res[n].net for n in ("K", "S-K")}), [("K", "S-K")])["K - S-K"]
        out["holdout"][f][per] = {
            "sharpe": {n: mk[n]["sharpe"] for n in mk}, "maxdd": {n: mk[n]["maxdd_pct"] for n in mk},
            "timing_sharpe": b["sharpe_diff"], "timing_sharpe_ci90": b["sharpe_ci90"],
            "timing_maxdd_pp": b["maxdd_diff_pp"],
        }

summ = {}
for per in ("P1", "P0"):
    signs = [out["holdout"][f][per]["timing_sharpe"] > 0 for f in out["holdout"]]
    summ[per] = {"holdouts_timing_positive": f"{sum(signs)}/{len(signs)}",
                 "fund_timing_ci90": out["bootstrap"][per]["K - S-K"]["sharpe_ci90"]}
crit = all(out["bootstrap"][p]["K - S-K"]["sharpe_ci90"][0] > 0 for p in ("P1", "P0"))
crit_hold = all(sum(out["holdout"][f][p]["timing_sharpe"] > 0 for f in out["holdout"]) >= 5 for p in ("P1", "P0"))
out["criterion"] = {"summary": summ, "timing_ci_above_zero_both_periods": crit,
                    "holdouts_same_sign_5_of_6_both_periods": crit_hold,
                    "timing_adds_value": bool(crit and crit_hold)}
(RESULTS / "s5_stats.json").write_text(json.dumps(out, indent=1))
print(json.dumps({"bootstrap": out["bootstrap"], "deflated": out["deflated"], "criterion": out["criterion"]}, indent=1))
for f, v in out["holdout"].items():
    print(f, {p: (v[p]["sharpe"], v[p]["timing_sharpe"], v[p]["timing_sharpe_ci90"], v[p]["timing_maxdd_pp"]) for p in v})
