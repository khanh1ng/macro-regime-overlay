"""Step 12: regimes read from market prices (specification in docs/RESEARCH_LOG.md, Step 12).
Writes results/s11_market_regimes.json and results/s11_market_labels.csv."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mo.config import RESULTS  # noqa: E402
from mo import macro  # noqa: E402
from mo.backtest import returns_panel, run, metrics, mret, ASSETS  # noqa: E402
from mo.regime import _label  # noqa: E402
from mo.strategies import build  # noqa: E402
from mo.infer import compare  # noqa: E402

WINDOW = 6
MIN_OBS, W0, GAMMA, LO, HI = 60, 0.60, 5.0, 0.25, 1.00
HEDGE = {"HYG": 0.075, "GLD": 0.1625, "DBC": 0.0125, "SHY": 0.075, "UUP": 0.05}   # as in Step 9
hs = sum(HEDGE.values())
HEDGE = {k: v / hs for k, v in HEDGE.items()}
PERIODS = {"P1": ("2007-04", "2026-09"), "P0": ("2000-10", "2007-03"), "Pall": ("2000-10", "2026-09"),
           "JLGMX": ("2011-01", "2026-09")}
CRISIS = ("2007-10", "2009-03")

rf = macro.tbill_monthly()
rets = returns_panel()
spy = mret("SPY")


def market_labels(spy, ief, dbc, upto=None, leak=False):
    """Regime at the end of each month t from returns through month t (through t+1 if leak=True,
    the positive control). upto truncates the data at month upto."""
    df = pd.concat({"SPY": spy, "IEF": ief, "DBC": dbc}, axis=1).dropna()
    if upto is not None:
        df = df[df.index <= upto]
    cum = (1 + df).rolling(WINDOW).apply(np.prod, raw=True) - 1
    if leak:
        cum = cum.shift(-1)
    g, i = cum["SPY"] - cum["IEF"], cum["DBC"] - cum["IEF"]
    return _label(g, i).dropna()


labels = market_labels(spy, rets["IEF"], rets["DBC"])
labels.to_csv(RESULTS / "s11_market_labels.csv", header=["regime"])

# Look-ahead test with a positive control.
cuts = [pd.Period(x, "M") for x in ("2001-06", "2008-09", "2015-03", "2020-03", "2022-06")]
la = []
for c in cuts:
    tr = market_labels(spy, rets["IEF"], rets["DBC"], upto=c)
    full_same = bool((labels.loc[:c] == tr).all())
    leak_full = market_labels(spy, rets["IEF"], rets["DBC"], leak=True)
    leak_tr = market_labels(spy, rets["IEF"], rets["DBC"], upto=c, leak=True)
    common = leak_tr.index.intersection(leak_full.index)
    caught = not (len(leak_tr) == len(leak_full.loc[:c]) and (leak_full.loc[common] == leak_tr.loc[common]).all())
    la.append({"cut": str(c), "identical": full_same, "control_caught": bool(caught)})
assert all(x["identical"] for x in la), "look-ahead test failed"
assert all(x["control_caught"] for x in la), "positive control not caught"

macro_labels = pd.read_csv(RESULTS / "s1_regimes.csv", index_col=0)["rt_raw"]
macro_labels.index = pd.PeriodIndex(macro_labels.index, freq="M")

# M2: walk-forward fund weight from the past mean return after the current market regime.
fund_ex = (rets["FUND"] - rf.reindex(rets.index)).dropna()
d = pd.concat([labels.rename("lab"), fund_ex.shift(-1).rename("y")], axis=1).dropna(subset=["lab"])
wts = {}
for t in d.index:
    past = d.loc[:t - 1].dropna()
    if len(past) < MIN_OBS:
        continue
    same = past[past.lab == d.loc[t, "lab"]].y
    mu = float(same.mean()) if len(same) else float(past.y.mean())
    wts[t] = min(HI, max(LO, W0 + (mu - past.y.mean()) / (GAMMA * past.y.var())))
w2 = pd.Series(wts)
W2 = pd.DataFrame({a: (1 - w2) * HEDGE.get(a, 0.0) for a in ASSETS}, index=w2.index)
W2["FUND"] = w2
WS = pd.DataFrame({a: (1 - W0) * HEDGE.get(a, 0.0) for a in ASSETS}, index=w2.index)
WS["FUND"] = W0


def frames(per, drop=None):
    s, e = PERIODS[per]
    mk, _ = build(labels, rets, s, e)
    mc, _ = build(macro_labels, rets, s, e)
    f = pd.DataFrame({"M1": mk["K"].net, "S-M1": mk["S-K"].net, "Fund": mk["Fund"].net, "Trend": mk["Trend"].net,
                      "K": mc["K"].net, "M2": run(W2, rets, s, e).net, "S-M2": run(WS, rets, s, e).net})
    if drop:
        f = f[(f.index < pd.Period(drop[0], "M")) | (f.index > pd.Period(drop[1], "M"))]
    return f


PAIRS = [("M1", "S-M1"), ("M1", "Fund"), ("M1", "K"), ("M1", "Trend"), ("M2", "S-M2"), ("M2", "Fund")]
out = {"spec": "docs/RESEARCH_LOG.md, Step 12", "lookahead": la, "first_label": str(labels.index[0]),
       "m2_first": str(w2.index[0]), "agreement_with_macro": {}, "periods": {}}
common = labels.index.intersection(macro_labels.dropna().index)
out["agreement_with_macro"] = {"months": len(common), "share": round(float((labels[common] == macro_labels[common]).mean()), 3),
                               "regime_shares": labels.value_counts(normalize=True).round(3).to_dict()}
for per in PERIODS:
    f = frames(per)
    out["periods"][per] = {"months": len(f), "metrics": {k: metrics(f[k], rf) for k in f.columns},
                           "tests": compare(f, PAIRS, rf),
                           "switches_per_year_M1": round(float((labels.reindex(f.index - 1) !=
                                                                labels.reindex(f.index - 1).shift()).mean() * 12), 1)}
f = frames("P1", CRISIS)
out["crisis_removed"] = {"months": len(f), "tests": compare(f, PAIRS, rf)}
t = out["periods"]
out["market_timing_adds_value"] = bool(all(t[p]["tests"]["M1 - S-M1"]["significant"] and
                                           t[p]["tests"]["M1 - S-M1"]["sharpe_diff"] > 0 for p in ("P1", "P0")))
(RESULTS / "s11_market_regimes.json").write_text(json.dumps(out, indent=1, default=str))

for per, v in t.items():
    print(f"\n{per} ({v['months']} months)")
    for k in ("M1", "S-M1", "M2", "S-M2", "K", "Trend", "Fund"):
        m = v["metrics"][k]
        print(f"  {k:6s} CAGR {m['cagr_pct']:6.2f}  Sharpe {m['sharpe']:5.2f}  MaxDD {m['maxdd_pct']:7.2f}")
    for k, r in v["tests"].items():
        print(f"  {k:12s} {r['sharpe_diff']:+.3f}  LW p {r['ledoit_wolf']['p']:.3f}  CI12 {r['ci90']['12']}  sig {r['significant']}")
print("\ncrisis removed:", {k: (r["sharpe_diff"], r["ledoit_wolf"]["p"], r["significant"]) for k, r in out["crisis_removed"]["tests"].items()})
print("agreement with macro:", out["agreement_with_macro"], "lookahead:", la[0])
print("market timing adds value:", out["market_timing_adds_value"])
