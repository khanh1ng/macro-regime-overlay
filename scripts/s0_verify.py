"""Step 0: verify every input series before any analysis. Writes results/s0_verify.json."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mo.config import ROOT, RESULTS, TICKERS, FUND, FUND_OLD  # noqa: E402
from mo.data import load, rebuilt_total_return  # noqa: E402
from mo import macro  # noqa: E402

AS_OF = pd.Timestamp("2026-06-30")
out, checks = {}, {}


def annualised(ticker, years):
    px, _ = load(ticker)
    a = px["adjclose"]
    end = a[:AS_OF].iloc[-1]
    start_date = AS_OF - pd.DateOffset(years=years)
    start = a[:start_date].iloc[-1]
    return 100 * ((end / start) ** (1 / years) - 1)


# V1: annualised returns against the fund's own annual report.
ref = json.loads((ROOT / "data" / "reference_returns.json").read_text())
v1 = {}
for t, r in ref["funds"].items():
    for k, yrs in (("1y", 1), ("5y", 5), ("10y", 10)):
        mine = annualised(t, yrs)
        v1[f"{t}_{k}"] = {"yahoo": round(mine, 2), "report": r[k], "diff": round(mine - r[k], 2)}
idx = ref["index"]["Russell 1000 Growth"]
for k, yrs in (("1y", 1), ("5y", 5), ("10y", 10)):
    mine = annualised("IWF", yrs)
    v1[f"IWF_vs_R1000G_{k}"] = {"yahoo": round(mine, 2), "index": idx[k], "diff": round(mine - idx[k], 2)}
out["V1_vs_annual_report"] = v1
checks["V1 fund returns within 0.5pp of report"] = all(abs(v["diff"]) < 0.5 for k, v in v1.items() if not k.startswith("IWF"))
checks["V1 IWF within 0.5pp of index (fee 0.19pp)"] = all(abs(v["diff"]) < 0.5 for k, v in v1.items() if k.startswith("IWF"))

# V2: Yahoo adjusted close equals raw close plus reinvested distributions.
v2 = {}
for t in TICKERS:
    px, ev = load(t)
    d = (px["adjclose"].pct_change() - rebuilt_total_return(px, ev)).abs().dropna()
    v2[t] = {"days": int(len(d)), "share_within_1bp": round(float((d < 1e-4).mean()), 5),
             "max_abs_diff": round(float(d.max()), 5)}
out["V2_adjclose_vs_rebuilt"] = v2
checks["V2 >=99.5% of days within 1bp for every ticker"] = all(v["share_within_1bp"] >= 0.995 for v in v2.values())

# V3: the two share classes hold the same portfolio; yearly gaps should be small and steady.
a = load(FUND)[0]["adjclose"]
b = load(FUND_OLD)[0]["adjclose"]
ya = a.resample("Y").last().pct_change()
yb = b.resample("Y").last().pct_change()
gap = (100 * (ya - yb)).dropna().loc["2011":"2025"]
out["V3_share_class_gap_pp"] = {str(k.year): round(v, 3) for k, v in gap.items()}
md = (a.resample("M").last().pct_change() - b.resample("M").last().pct_change()).dropna()
out["V3_monthly_gap_max_abs_pp"] = round(100 * float(md.abs().max()), 3)
checks["V3 yearly R6-minus-I gap in [-0.1, 0.6] pp every year"] = bool(gap.between(-0.1, 0.6).all())

# V4: no unexplained one-day drops (a missing distribution shows up as a fund drop on a calm day).
iwf = load("IWF")[0]["adjclose"].pct_change()
v4 = {}
for t in [FUND, FUND_OLD, "FBGRX", "TRBCX", "AGTHX"]:
    r = load(t)[0]["adjclose"].pct_change()
    j = pd.concat([r.rename("f"), iwf.rename("i")], axis=1).dropna()
    bad = j[(j.f < -0.04) & (j.i > -0.015)]
    v4[t] = [d.date().isoformat() for d in bad.index]
out["V4_unexplained_drops"] = v4
checks["V4 no unexplained drops in fund series"] = all(len(v) == 0 for v in v4.values())

# V5: coverage and stale prices.
v5 = {}
for t in TICKERS:
    px, _ = load(t)
    r = px["adjclose"].pct_change().dropna()
    runs = (r == 0).astype(int)
    longest = int(runs.groupby((runs == 0).cumsum()).sum().max())
    v5[t] = {"first": px.index[0].date().isoformat(), "last": px.index[-1].date().isoformat(),
             "days": int(len(px)), "zero_return_share": round(float((r == 0).mean()), 4),
             "longest_zero_run": longest}
out["V5_coverage"] = v5
checks["V5 every series ends on or after 2026-09-25"] = all(v["last"] >= "2026-09-25" for v in v5.values())
checks["V5 no run of 5+ unchanged days"] = all(v["longest_zero_run"] < 5 for v in v5.values())

# V6: macro inputs.
iv = macro.ip_vintages()
last_obs = {v: iv[v].last_valid_index() for v in iv.columns}
lags = pd.Series({v: (v - o).n for v, o in last_obs.items() if o is not None})
out["V6_ip_vintages"] = {"first_vintage": str(iv.columns[0]), "last_vintage": str(iv.columns[-1]),
                         "n_vintages": int(iv.shape[1]),
                         "lag_last_obs_months_counts": {str(k): int(v) for k, v in lags.value_counts().sort_index().items()}}
latest = macro.ip_latest()
common = iv.index.intersection(latest.index)
lv = iv[iv.columns[-1]].reindex(common)
rel = (lv / latest.reindex(common)).dropna()
out["V6_ip_last_vintage_vs_fred"] = {"months": int(len(rel)), "max_abs_rel_diff": round(float((rel - 1).abs().max()), 5)}
cn, cs = macro.cpi_nsa(), macro.cpi_sa()
yoy_n, yoy_s = 100 * cn.pct_change(12), 100 * cs.pct_change(12)
j = pd.concat([yoy_n, yoy_s], axis=1).dropna().loc["1990":]
out["V6_cpi"] = {"nsa_last": str(cn.index[-1]), "corr_yoy_nsa_sa": round(float(j.corr().iloc[0, 1]), 4),
                 "max_abs_gap_pp": round(float((j.iloc[:, 0] - j.iloc[:, 1]).abs().max()), 3)}
rf = macro.tbill_monthly()
out["V6_rf"] = {"first": str(rf.index[0]), "last": str(rf.index[-1])}
late = {str(v): str(last_obs[v]) for v in lags.index if lags[v] != 1}
out["V6_ip_late_vintages"] = late
# A one-month lag is normal; the October and November 2025 vintages are late because the 2025
# federal shutdown delayed the release. The classifier uses the latest published month, so this is real-time.
checks["V6 every IP vintage ends 1 month before its date, except the 2025 shutdown delay"] = set(late) <= {"2025-10", "2025-11"} and int(lags.max()) <= 3
checks["V6 last IP vintage matches current FRED INDPRO within 0.5%"] = out["V6_ip_last_vintage_vs_fred"]["max_abs_rel_diff"] < 0.005
checks["V6 CPI NSA and SA year-on-year agree (corr > 0.99)"] = out["V6_cpi"]["corr_yoy_nsa_sa"] > 0.99

# V7: the numbers reported in the earlier backtest, recomputed on verified data.
m = a.resample("M").last().pct_change()


def window(s, e):
    return round(100 * float((1 + m.loc[s:e]).prod() - 1), 2)


dd = a / a.cummax() - 1
mdd = a.resample("M").last()
mdd = mdd / mdd.cummax() - 1
out["V7_old_claims_recomputed"] = {
    "2018Q4 (Oct-Dec) old -29.07": window("2018-10", "2018-12"),
    "2020 Feb-Mar old -14.88": window("2020-02", "2020-03"),
    "2022 Jan-Oct old -12.56": window("2022-01", "2022-10"),
    "max drawdown daily": round(100 * float(dd.min()), 2),
    "max drawdown daily date": dd.idxmin().date().isoformat(),
    "max drawdown month-end": round(100 * float(mdd.min()), 2),
    "max drawdown month-end date": mdd.idxmin().date().isoformat(),
}

out["checks"] = checks
out["all_pass"] = all(checks.values())
RESULTS.mkdir(exist_ok=True)
(RESULTS / "s0_verify.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
