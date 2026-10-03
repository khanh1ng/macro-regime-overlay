"""Regression checks: the headline numbers the papers rely on. Writes results/test_regression.json."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mo.config import RESULTS  # noqa: E402

L = lambda f: json.loads((RESULTS / f).read_text())  # noqa: E731
s0, s1, s2, s3, s5, s6 = (L(f) for f in ("s0_verify.json", "s1_regimes.json", "s2_predict.json",
                                         "s3_backtest.json", "s5_stats.json", "s6_costs.json"))
s7, s8, s9 = (L(f) for f in ("s7_holdouts.json", "s8_model.json", "s9_mechanism.json"))
r = s3["results"]
checks = {
    "s0 all data checks pass": s0["all_pass"],
    "s0 JLGMX 10y within 0.1pp of report": abs(s0["V1_vs_annual_report"]["JLGMX_10y"]["diff"]) < 0.1,
    "s0 old 2018Q4 claim not reproduced": s0["V7_old_claims_recomputed"]["2018Q4 (Oct-Dec) old -29.07"] == -18.52,
    "s1 lookahead test passed": L("test_s1_lookahead.json")["pass"],
    "s1 rt vs revised agreement 0.818": s1["agreement_rt_vs_revised_same_rules"]["raw, revised lag 1"]["share"] == 0.818,
    "s2 no asset below Bonferroni (rt_raw)": s2["summary"]["rt_raw"]["n_p_below_bonferroni"] == 0,
    "s2 fund Stagflation positive before 2007": s2["pre_2007_03"]["rt_raw"]["SEEGX"]["stagflation_minus_others_ann_pct"] > 0,
    "s2 fund Stagflation negative after 2007": s2["from_2007_04"]["rt_raw"]["SEEGX"]["stagflation_minus_others_ann_pct"] < 0,
    "s3 backtest tests passed": L("test_backtest.json")["pass"],
    "s3 P1 K Sharpe 1.069": r["rt_raw|P1"]["K"]["sharpe"] == 1.069,
    "s3 P0 K Sharpe -0.355": r["rt_raw|P0"]["K"]["sharpe"] == -0.355,
    "s3 Pold fund CAGR equals old notebook 16.81": r["rt_raw|Pold"]["Fund"]["cagr_pct"] == 16.81,
    "s5 criterion fails": s5["criterion"]["timing_adds_value"] is False,
    "s5 P1 timing CI above 0": s5["bootstrap"]["P1"]["K - S-K"]["sharpe_ci90"][0] > 0,
    "s5 P0 timing negative": s5["bootstrap"]["P0"]["K - S-K"]["sharpe_diff"] < 0,
    "s5 hold-outs P1 6/6, P0 0/6": (s5["criterion"]["summary"]["P1"]["holdouts_timing_positive"] == "6/6"
                                    and s5["criterion"]["summary"]["P0"]["holdouts_timing_positive"] == "0/6"),
    "s7 hold-out timing series behave like ~1 series": s7["neff_timing_old7"] < 1.5,
    "s7 new assets 4/4 same pattern": s7["new_with_pattern"] == "4/4",
    "s8 continuous model fails": s8["timing_adds_value"] is False and s8["forecast"]["P0"]["oos_r2_pct"] < 0,
    "s9 mechanism not supported": s9["supported"] is False,
    "s6 2008 largest timing year": max(s6["exploratory_timing_by_year"], key=s6["exploratory_timing_by_year"].get) == "2008",
}
out = {"checks": checks, "n": len(checks), "passed": sum(bool(v) for v in checks.values())}
(RESULTS / "test_regression.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
assert out["passed"] == out["n"]
