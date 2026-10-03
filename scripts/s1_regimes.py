"""Step 1: the real-time regime classifier, what revisions change, and sensitivity.
Writes results/s1_regimes.csv and results/s1_regimes.json."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mo.config import RESULTS  # noqa: E402
from mo import regime as R  # noqa: E402

MONTHS = pd.period_range("1990-01", "2026-09", freq="M")

sig_rt = R.realtime_signals(MONTHS)
variants = {
    "rt_raw": R.classify(sig_rt),
    "rt_smooth3": R.classify(R.smooth(sig_rt)),
}
variants["rt_smooth3_persist3"] = R.persist(variants["rt_smooth3"])
variants["rt_raw_persist3"] = R.persist(variants["rt_raw"])
for lag in (1, 2, 3):
    variants[f"rt_raw_extralag{lag}"] = R.classify(R.realtime_signals(MONTHS, extra_lag=lag))
for lag in (1, 2):
    variants[f"revised_lag{lag}"] = R.classify(R.revised_signals(MONTHS, lag=lag))
variants["revised_lag2_smooth3_persist3"] = R.persist(R.classify(R.smooth(R.revised_signals(MONTHS, lag=2))))

lab = pd.DataFrame(variants).reindex(MONTHS)
lab.index = lab.index.astype(str)
RESULTS.mkdir(exist_ok=True)
lab.to_csv(RESULTS / "s1_regimes.csv")
sig_rt.assign(ip_obs=sig_rt.ip_obs.astype(str), cpi_obs=sig_rt.cpi_obs.astype(str)).to_csv(RESULTS / "s1_signals_rt.csv")


def summary(s):
    s = s.dropna()
    sp = R.spells(s)
    return {"months": int(len(s)), "first": s.index[0], "switches": int(len(sp) - 1),
            "mean_spell": round(float(sp.months.mean()), 2), "median_spell": float(sp.months.median()),
            "share": {k: round(float((s == k).mean()), 3) for k in R.REGIMES}}


def agree(a, b):
    j = pd.concat([a, b], axis=1).dropna()
    return round(float((j.iloc[:, 0] == j.iloc[:, 1]).mean()), 3), int(len(j))


out = {"summary": {k: summary(lab[k]) for k in lab.columns}}
base = lab["rt_raw"]
out["agreement_with_rt_raw"] = {k: dict(zip(("share", "months"), agree(base, lab[k]))) for k in lab.columns}
out["agreement_rt_vs_revised_same_rules"] = {
    "raw, revised lag 1": dict(zip(("share", "months"), agree(lab["rt_raw"], lab["revised_lag1"]))),
    "smooth+persist, revised lag 2": dict(zip(("share", "months"), agree(lab["rt_smooth3_persist3"], lab["revised_lag2_smooth3_persist3"]))),
}

# Which component do revisions change? Compare real-time signals with revised ones at the same lag.
rev1 = R.revised_signals(MONTHS, lag=1)
j = pd.concat([sig_rt[["g", "i"]], rev1.add_suffix("_rev")], axis=1).dropna()
out["sign_agreement_by_component_lag1"] = {
    "growth": round(float((np.sign(j.g) == np.sign(j.g_rev)).mean()), 3),
    "inflation": round(float((np.sign(j.i) == np.sign(j.i_rev)).mean()), 3),
    "growth_corr": round(float(j.g.corr(j.g_rev)), 3),
    "inflation_corr": round(float(j.i.corr(j.i_rev)), 3),
}

# Transition matrix of the real-time raw classifier (monthly).
s = base.dropna()
tm = pd.crosstab(s.shift().dropna(), s.iloc[1:], normalize="index").reindex(index=R.REGIMES, columns=R.REGIMES)
out["transition_rt_raw"] = tm.round(3).to_dict()

# Named episodes under the real-time smoothed + persistent classifier.
ep = R.spells(lab["rt_smooth3_persist3"].dropna())
ep["start"] = [lab["rt_smooth3_persist3"].dropna().index[i] for i in np.r_[0, ep.months.cumsum().values[:-1]]]
out["longest_spells_rt_smooth3_persist3"] = (ep.sort_values("months", ascending=False).head(10)
                                             [["regime", "start", "months"]].to_dict("records"))

(RESULTS / "s1_regimes.json").write_text(json.dumps(out, indent=1, default=str))
print(json.dumps(out, indent=1, default=str))
