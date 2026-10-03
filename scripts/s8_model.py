"""Step 11: continuous macro signals in a predictive regression, and the allocation built on it.
Writes results/s8_model.json."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mo.config import RESULTS  # noqa: E402
from mo import macro  # noqa: E402
from mo.backtest import returns_panel, run, metrics, ASSETS  # noqa: E402
from mo.stats import ols_hac  # noqa: E402

from mo.boot import boot  # noqa: E402

MIN_OBS, W0, GAMMA, LO, HI = 96, 0.60, 5.0, 0.25, 1.00
HEDGE = {"HYG": 0.075, "GLD": 0.1625, "DBC": 0.0125, "SHY": 0.075, "UUP": 0.05}  # K table, equal regime weights
hs = sum(HEDGE.values())
HEDGE = {k: v / hs for k, v in HEDGE.items()}
PERIODS = {"P1": ("2007-04", "2026-09"), "P0": ("2000-10", "2007-03")}

rf = macro.tbill_monthly()
rets = returns_panel()
fund_ex = (rets["FUND"] - rf.reindex(rets.index)).dropna()
sig = pd.read_csv(RESULTS / "s1_signals_rt.csv", index_col=0)
sig.index = pd.PeriodIndex(sig.index, freq="M")
sig = sig[["g", "i"]].astype(float)

# Data row for decision month t: signals known at t, target = excess return in t+1.
d = pd.concat([sig, fund_ex.shift(-1).rename("y")], axis=1).dropna(subset=["g", "i"])
fc = {}
for t in d.index:
    past = d.loc[:t - 1].dropna()  # targets realised by the end of month t
    if len(past) < MIN_OBS:
        continue
    X = np.c_[np.ones(len(past)), past[["g", "i"]].values]
    b = np.linalg.lstsq(X, past.y.values, rcond=None)[0]
    mu = float(np.r_[1.0, d.loc[t, ["g", "i"]].values] @ b)
    fc[t] = {"mu": mu, "mean": float(past.y.mean()), "var": float(past.y.var()), "y": d.loc[t, "y"]}
fc = pd.DataFrame.from_dict(fc, orient="index")

out = {"first_forecast": str(fc.index[0]), "forecast": {}, "alloc": {}}
for per, (s, e) in PERIODS.items():
    f = fc.loc[pd.Period(s, "M") - 1:pd.Period(e, "M") - 1].dropna()
    e1, e0 = f.y - f.mu, f.y - f["mean"]
    r2 = 1 - (e1 ** 2).sum() / (e0 ** 2).sum()
    cw = e0 ** 2 - (e1 ** 2 - (f["mean"] - f.mu) ** 2)
    b, V = ols_hac(cw.values, np.ones((len(cw), 1)), 6)
    out["forecast"][per] = {"months": int(len(f)), "oos_r2_pct": round(100 * float(r2), 2),
                            "clark_west_t": round(float(b[0] / np.sqrt(V[0, 0])), 2)}

w = (W0 + (fc.mu - fc["mean"]) / (GAMMA * fc["var"])).clip(LO, HI)
WM = pd.DataFrame({a: (1 - w) * HEDGE.get(a, 0.0) for a in ASSETS}, index=fc.index)
WM["FUND"] = w
WS = pd.DataFrame({a: (1 - W0) * HEDGE.get(a, 0.0) for a in ASSETS}, index=fc.index)
WS["FUND"] = W0
for per, (s, e) in PERIODS.items():
    m, sm = run(WM, rets, s, e), run(WS, rets, s, e)
    dec = pd.period_range(pd.Period(s, "M") - 1, pd.Period(e, "M") - 1, freq="M")
    b = boot(pd.DataFrame({"M": m.net, "S-M": sm.net}), [("M", "S-M")])["M - S-M"]
    out["alloc"][per] = {
        "M": metrics(m.net, rf), "S-M": metrics(sm.net, rf),
        "avg_fund_weight_M": round(float(w.reindex(dec).mean()), 3),
        "share_months_at_bounds": round(float(((w.reindex(dec) <= LO) | (w.reindex(dec) >= HI)).mean()), 3),
        "timing_sharpe": b["sharpe_diff"], "timing_ci90": b["sharpe_ci90"], "timing_maxdd_pp": b["maxdd_diff_pp"],
        "turnover_M": round(float(m.turnover.mean() * 12), 2)}
out["hedge_mix"] = {k: round(v, 4) for k, v in HEDGE.items()}
out["timing_adds_value"] = all(out["alloc"][p]["timing_ci90"][0] > 0 for p in PERIODS)
(RESULTS / "s8_model.json").write_text(json.dumps(out, indent=1))
print(json.dumps({k: out[k] for k in ("first_forecast", "forecast", "timing_adds_value", "hedge_mix")}, indent=1))
for p, v in out["alloc"].items():
    print(p, "M", v["M"]["sharpe"], v["M"]["maxdd_pct"], "S-M", v["S-M"]["sharpe"], v["S-M"]["maxdd_pct"],
          "timing", v["timing_sharpe"], v["timing_ci90"], "w", v["avg_fund_weight_M"], "bounds", v["share_months_at_bounds"])
