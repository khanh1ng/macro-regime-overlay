"""Fill paper/template.tex with numbers and tables from results/.
No number in the paper is typed by hand. Writes paper/paper.tex."""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mo.config import ROOT, RESULTS  # noqa: E402
from mo import macro  # noqa: E402
from mo.data import monthly_returns  # noqa: E402

P = ROOT / "paper"
L = lambda f: json.loads((RESULTS / f).read_text())  # noqa: E731
s0, s1, s2, s3, s5, s6 = (L(f) for f in ("s0_verify.json", "s1_regimes.json", "s2_predict.json",
                                         "s3_backtest.json", "s5_stats.json", "s6_costs.json"))
s7, s8, s9 = (L(f) for f in ("s7_holdouts.json", "s8_model.json", "s9_mechanism.json"))
tl, tb, treg = L("test_s1_lookahead.json"), L("test_backtest.json"), L("test_regression.json")
old = json.loads((ROOT / "data" / "old_claims.json").read_text())
ref = json.loads((ROOT / "data" / "reference_returns.json").read_text())
V = {}
REG = ["Goldilocks", "Reflation", "Disinflation", "Stagflation"]


def n(x, d=2, sign=False):
    s = f"{x:+.{d}f}" if sign else f"{x:.{d}f}"
    return f"${s}$"


def pc(x, d=1, sign=False):
    return n(x, d, sign)[:-1] + "\\%$"


def share(x, d=1):
    return pc(100 * x, d)


def rows(lines):
    return " \\\\\n".join(lines) + " \\\\"


# ---------------------------------------------------------------- shared numbers
V["n_assets"] = "12"
V["n_tests"] = str(s2["n_tests"])
V["bonf"] = n(s2["bonferroni_level"], 4)

# ---------------------------------------------------------------- Paper A
v1 = s0["V1_vs_annual_report"]
V["TAB_A_DATA"] = rows([
    f"JLGMX (Class R6) & {n(v1['JLGMX_1y']['yahoo'])} & {n(v1['JLGMX_1y']['report'])} & {n(v1['JLGMX_5y']['yahoo'])} & "
    f"{n(v1['JLGMX_5y']['report'])} & {n(v1['JLGMX_10y']['yahoo'])} & {n(v1['JLGMX_10y']['report'])}",
    f"SEEGX (Class I) & {n(v1['SEEGX_1y']['yahoo'])} & {n(v1['SEEGX_1y']['report'])} & {n(v1['SEEGX_5y']['yahoo'])} & "
    f"{n(v1['SEEGX_5y']['report'])} & {n(v1['SEEGX_10y']['yahoo'])} & {n(v1['SEEGX_10y']['report'])}",
    f"IWF vs.\\ Russell 1000 Growth & {n(v1['IWF_vs_R1000G_1y']['yahoo'])} & {n(v1['IWF_vs_R1000G_1y']['index'])} & "
    f"{n(v1['IWF_vs_R1000G_5y']['yahoo'])} & {n(v1['IWF_vs_R1000G_5y']['index'])} & {n(v1['IWF_vs_R1000G_10y']['yahoo'])} & "
    f"{n(v1['IWF_vs_R1000G_10y']['index'])}"])
V["v1_max"] = n(max(abs(v["diff"]) for k, v in v1.items() if not k.startswith("IWF")), 2)
V["iwf_fee"] = pc(ref["index"]["Russell 1000 Growth"]["iwf_expense_ratio_pct"], 2)
gap = s0["V3_share_class_gap_pp"]
V["gap_min"], V["gap_max"] = n(min(gap.values())), n(max(gap.values()))
V["gap_month_max"] = n(s0["V3_monthly_gap_max_abs_pp"])
V["v2_min"] = share(min(v["share_within_1bp"] for v in s0["V2_adjclose_vs_rebuilt"].values()), 1)
V["ip_first"], V["ip_last"] = s0["V6_ip_vintages"]["first_vintage"], s0["V6_ip_vintages"]["last_vintage"]
V["ip_n"] = str(s0["V6_ip_vintages"]["n_vintages"])
V["ip_fred_gap"] = pc(100 * s0["V6_ip_last_vintage_vs_fred"]["max_abs_rel_diff"], 2)
V["cpi_corr"] = n(s0["V6_cpi"]["corr_yoy_nsa_sa"], 4)
V["cpi_gap"] = n(s0["V6_cpi"]["max_abs_gap_pp"])

names = {"rt_raw": "Real time, raw", "rt_smooth3": "Real time, smoothed",
         "rt_smooth3_persist3": "Real time, smoothed + persistent",
         "revised_lag1": "Revised, lag 1", "revised_lag2": "Revised, lag 2",
         "revised_lag2_smooth3_persist3": "Revised, lag 2, smoothed + persistent"}
V["TAB_A_SPELLS"] = rows([
    f"{lab} & {s1['summary'][k]['months']} & {s1['summary'][k]['switches']} & {n(s1['summary'][k]['mean_spell'],1)} & "
    + " & ".join(share(s1['summary'][k]['share'][r], 0) for r in REG) for k, lab in names.items()])
sm = s1["summary"]
V["raw_switch"], V["raw_spell"] = str(sm["rt_raw"]["switches"]), n(sm["rt_raw"]["mean_spell"], 1)
V["sp_switch"], V["sp_spell"] = str(sm["rt_smooth3_persist3"]["switches"]), n(sm["rt_smooth3_persist3"]["mean_spell"], 1)
V["raw_months"] = str(sm["rt_raw"]["months"])
ag = s1["agreement_with_rt_raw"]
V["agree_rev1"] = share(s1["agreement_rt_vs_revised_same_rules"]["raw, revised lag 1"]["share"])
V["agree_rev2"] = share(ag["revised_lag2"]["share"])
V["agree_sp"] = share(s1["agreement_rt_vs_revised_same_rules"]["smooth+persist, revised lag 2"]["share"])
V["agree_l1"], V["agree_l2"], V["agree_l3"] = (share(ag[f"rt_raw_extralag{i}"]["share"]) for i in (1, 2, 3))
sc = s1["sign_agreement_by_component_lag1"]
V["sign_g"], V["sign_i"] = share(sc["growth"]), share(sc["inflation"])
V["corr_g"], V["corr_i"] = n(sc["growth_corr"], 3), n(sc["inflation_corr"], 3)
V["disagree_third"] = share(1 - ag["revised_lag2"]["share"], 0)

lab = pd.read_csv(RESULTS / "s1_regimes.csv", index_col=0)
ex = lab.loc["2007-10":"2009-03", ["rt_raw", "rt_smooth3_persist3", "revised_lag2"]]
sig = pd.read_csv(RESULTS / "s1_signals_rt.csv", index_col=0)
V["TAB_A_2008"] = rows([f"{i} & {sig.loc[i,'ip_obs']} & {n(sig.loc[i,'g'],2,True)} & {n(sig.loc[i,'i'],2,True)} & "
                        f"{r.rt_raw} & {r.rt_smooth3_persist3} & {r.revised_lag2}" for i, r in ex.iterrows()])
V["tl_cuts"] = str(tl["cuts"])
V["tl_id"] = str(tl["identical_raw"])
V["tl_pc"] = str(tl["positive_control_cuts_flagged_by_label_test"])

AS = ["SEEGX", "SPY", "IWF", "QQQ", "IEF", "TLT", "SHY", "TIP", "GLD", "HYG", "UUP", "DBC"]
ASN = {"SEEGX": "Large Cap Growth (SEEGX)", "SPY": "S\\&P 500 (SPY)", "IWF": "Russell 1000 Growth (IWF)",
       "QQQ": "Nasdaq-100 (QQQ)", "IEF": "7--10y Treasuries (IEF)", "TLT": "20y+ Treasuries (TLT)",
       "SHY": "1--3y Treasuries (SHY)", "TIP": "TIPS (TIP)", "GLD": "Gold (GLD)", "HYG": "High yield (HYG)",
       "UUP": "US dollar (UUP)", "DBC": "Commodities (DBC)"}
fl = s2["full"]
V["TAB_A_WALD"] = rows([
    f"{ASN[a]} & {fl['rt_raw'][a]['start']} & {n(fl['rt_raw'][a]['wald_equal_means_p'],3)} & "
    f"{n(fl['rt_smooth3_persist3'][a]['wald_equal_means_p'],3)} & {n(fl['revised_lag2'][a]['wald_equal_means_p'],3)} & "
    f"{n(fl['rt_raw'][a]['stagflation_minus_others_ann_pct'],1,True)} & {n(fl['rt_raw'][a]['stagflation_minus_others_t'],2,True)}"
    for a in AS])
sumr = s2["summary"]
V["n05_raw"] = str(sumr["rt_raw"]["n_p_below_0.05"])
V["nbonf_all"] = str(sum(sumr[c]["n_p_below_bonferroni"] for c in sumr))
V["hyg_p"] = n(fl["rt_raw"]["HYG"]["wald_equal_means_p"], 3)


def fundrow(r):
    return " & ".join(f"{d['n']} & {n(d['ann_excess_pct'],1,True)} & {n(d['sharpe'],2,True)}" for d in r)


F = {per: s2[per]["rt_raw"]["SEEGX"] if per != "full" else fl["rt_raw"]["SEEGX"] for per in ("full", "pre_2007_03", "from_2007_04")}
V["TAB_A_FUND"] = rows([f"{r} & " + fundrow([F[p]["by_regime"][r] for p in ("full", "pre_2007_03", "from_2007_04")]) for r in REG]
                       + ["\\midrule Wald $p$ (equal means) & \\multicolumn{3}{c}{" + n(F["full"]["wald_equal_means_p"], 3) + "} & "
                          "\\multicolumn{3}{c}{" + n(F["pre_2007_03"]["wald_equal_means_p"], 3) + "} & \\multicolumn{3}{c}{"
                          + n(F["from_2007_04"]["wald_equal_means_p"], 3) + "}",
                          "Stagflation $-$ others (\\%/yr) & \\multicolumn{3}{c}{" + n(F["full"]["stagflation_minus_others_ann_pct"], 1, True)
                          + " ($t=" + f"{F['full']['stagflation_minus_others_t']:.2f}" + "$)} & \\multicolumn{3}{c}{"
                          + n(F["pre_2007_03"]["stagflation_minus_others_ann_pct"], 1, True) + " ($t=" + f"{F['pre_2007_03']['stagflation_minus_others_t']:.2f}"
                          + "$)} & \\multicolumn{3}{c}{" + n(F["from_2007_04"]["stagflation_minus_others_ann_pct"], 1, True)
                          + " ($t=" + f"{F['from_2007_04']['stagflation_minus_others_t']:.2f}" + "$)}"])
for p, k in (("full", "f"), ("pre_2007_03", "pre"), ("from_2007_04", "post")):
    V[f"{k}_stag"] = pc(F[p]["by_regime"]["Stagflation"]["ann_excess_pct"], 1, True)
    V[f"{k}_gold"] = pc(F[p]["by_regime"]["Goldilocks"]["ann_excess_pct"], 1, True)
    V[f"{k}_con"] = pc(F[p]["stagflation_minus_others_ann_pct"], 1, True)
    V[f"{k}_cont"] = n(F[p]["stagflation_minus_others_t"], 2, True)
    V[f"{k}_p"] = n(F[p]["wald_equal_means_p"], 3)
    V[f"{k}_nstag"] = str(F[p]["by_regime"]["Stagflation"]["n"])
mde = s2["fund_stagflation_mde_rt_raw"]
V["mde_full"], V["mde_pre"], V["mde_post"] = (pc(mde[k]["min_detectable_ann_pct"], 0) for k in ("full", "pre_2007_03", "from_2007_04"))
V["se_full"] = pc(mde["full"]["se"], 1)
post_sig = [a for a, r in s2["from_2007_04"]["rt_raw"].items() if r["wald_equal_means_p"] < 0.05]
pre_sig = [a for a, r in s2["pre_2007_03"]["rt_raw"].items() if r["wald_equal_means_p"] < 0.05]
V["post_sig"] = ", ".join(post_sig) if post_sig else "none"
V["n_post_sig"], V["n_pre_sig"] = str(len(post_sig)), str(len(pre_sig))
V["n_pre_assets"] = str(len(s2["pre_2007_03"]["rt_raw"]))
V["sp_post_p"] = n(s2["from_2007_04"]["rt_smooth3_persist3"]["SEEGX"]["wald_equal_means_p"], 2)
tlt = fl["rt_raw"]["TLT"]
V["tlt_stag"], V["tlt_stag_t"] = pc(tlt["by_regime"]["Stagflation"]["ann_excess_pct"], 1, True), n(tlt["by_regime"]["Stagflation"]["t_hac"], 2)
gld = fl["rt_raw"]["GLD"]
V["gld_stag"], V["gld_gold"] = pc(gld["by_regime"]["Stagflation"]["ann_excess_pct"], 1, True), pc(gld["by_regime"]["Goldilocks"]["ann_excess_pct"], 1, True)
stg = lab["rt_raw"][lab["rt_raw"] == "Stagflation"]
yrs = stg.groupby(stg.index.str[:4]).size()
pre_y = yrs[yrs.index < "2007"].sort_values(ascending=False)
post_y = yrs[yrs.index >= "2007"].sort_values(ascending=False)
V["stag_pre_top"] = ", ".join(f"{y} ({c})" for y, c in pre_y.head(4).items())
V["stag_post_top"] = ", ".join(f"{y} ({c})" for y, c in post_y.head(4).items())
V["stag_pre_nyears"], V["stag_post_nyears"] = str(len(pre_y)), str(len(post_y))
V["stag_2022"] = str(int(yrs.get("2022", 0)))
V["stag_0708"] = str(int(yrs.get("2007", 0) + yrs.get("2008", 0)))
_rfm = macro.tbill_monthly()
_t = monthly_returns("TLT"); _t.index = _t.index.to_period("M")
_l = lab["rt_raw"].copy(); _l.index = pd.PeriodIndex(_l.index, freq="M")
_d = pd.concat([(_t - _rfm.reindex(_t.index)).rename("y"), _l.shift(1).rename("g")], axis=1).dropna()
_s = _d[_d.g == "Stagflation"]
_by = _s.groupby(_s.index.year).y.agg(["size", "mean"])
V["tlt_ex2008"] = pc(1200 * _s[_s.index.year != 2008].y.mean(), 1, True)
V["tlt_2022"] = pc(1200 * _by.loc[2022, "mean"], 0, True)
V["tlt_2022_n"] = str(int(_by.loc[2022, "size"]))
_top = _by[_by["size"] >= 4].sort_values("mean", ascending=False).head(4)
V["tlt_top"] = ", ".join(f"{y} ({int(r['size'])} months, {pc(1200*r['mean'],0,True)})" for y, r in _top.iterrows())
V["FIG_A_PRE"] = " ".join(f"({r},{F['pre_2007_03']['by_regime'][r]['ann_excess_pct']:.2f})" for r in REG)
V["FIG_A_POST"] = " ".join(f"({r},{F['from_2007_04']['by_regime'][r]['ann_excess_pct']:.2f})" for r in REG)

# ---------------------------------------------------------------- Paper B
R = s3["results"]
oc = old["fund"]
V8 = s0["V7_old_claims_recomputed"]
rf = macro.tbill_monthly()
mon = pd.read_csv(RESULTS / "s3_monthly.csv", header=[0, 1], index_col=0)
mon.index = pd.PeriodIndex(mon.index, freq="M")


def geo_sharpe(r):
    r = r.dropna()
    yrs = len(r) / 12
    cagr = np.prod(1 + r) ** (1 / yrs) - 1
    rfa = np.prod(1 + rf.reindex(r.index)) ** (1 / yrs) - 1
    return (cagr - rfa) / (r.std() * np.sqrt(12))


po = R["rt_raw|Pold"]
V["TAB_B_OLD"] = rows([
    f"Fund, Oct--Dec 2018 & {pc(oc['q4_2018_pct'],2)} & {pc(V8['2018Q4 (Oct-Dec) old -29.07'],2)}",
    f"Fund, Feb--Mar 2020 & {pc(oc['covid_feb_mar_2020_pct'],2)} & {pc(V8['2020 Feb-Mar old -14.88'],2)}",
    f"Fund, Jan--Oct 2022 & {pc(oc['jan_oct_2022_pct'],2)} & {pc(V8['2022 Jan-Oct old -12.56'],2)}",
    f"Fund, CAGR 2011-02 to 2026-05 & {pc(oc['cagr_pct'],2)} & {pc(po['Fund']['cagr_pct'],2)}",
    f"Fund, volatility & {pc(oc['vol_pct'],2)} & {pc(po['Fund']['vol_pct'],2)}",
    f"Fund, Sharpe (old convention) & {n(oc['sharpe_geo'],2)} & {n(geo_sharpe(mon[('rt_raw|Pold','Fund')]),2)}",
    f"Fund, maximum drawdown & {pc(oc['maxdd_pct'],2)} & {pc(po['Fund']['maxdd_pct'],2)}",
    "\\midrule",
    f"K, CAGR & {pc(old['K_walkforward']['cagr_pct'],2)} & {pc(po['K']['cagr_pct'],2)}",
    f"K, volatility & {pc(old['K_walkforward']['vol_pct'],2)} & {pc(po['K']['vol_pct'],2)}",
    f"K, Sharpe (old convention) & {n(old['K_walkforward']['sharpe_geo'],2)} & {n(geo_sharpe(mon[('rt_raw|Pold','K')]),2)}",
    f"K, maximum drawdown & {pc(old['K_walkforward']['maxdd_pct'],2)} & {pc(po['K']['maxdd_pct'],2)}"]).replace("\\midrule \\\\", "\\midrule")
V["old_fund_cagr"], V["old_k_cagr"] = pc(old["write_up_headline"]["fund_cagr_pct"], 2), pc(old["write_up_headline"]["K_cagr_pct"], 2)
V["pold_k_cagr"], V["pold_f_cagr"] = pc(po["K"]["cagr_pct"], 2), pc(po["Fund"]["cagr_pct"], 2)
V["pold_giveup"] = n(po["Fund"]["cagr_pct"] - po["K"]["cagr_pct"], 1)
V["old_trials"] = str(old["configurations_tried"])
V["dd_daily"], V["dd_daily_date"] = pc(V8["max drawdown daily"], 2), V8["max drawdown daily date"]
V["dd_me"], V["dd_me_date"] = pc(V8["max drawdown month-end"], 2), V8["max drawdown month-end date"]

pxn = {"HYG": "High yield", "SHY": "1--3y Treasuries", "IEF": "7--10y Treasuries", "TLT": "20y+ Treasuries",
       "GLD": "Gold", "DBC": "Commodities", "UUP": "US dollar"}
TEXP = {k: v["proxy"].replace("^", "\\^{}") + (" + T-bill" if v["plus_tbill"] else "") for k, v in s3["proxy_check"].items()}
V["TAB_B_PROXY"] = rows([f"{e} ({pxn[e]}) & {TEXP[e]} & "
                         f"{n(v['corr'],3)} & {pc(v['te_pct'],1)} & {pc(v['ann_mean_diff_pct'],2,True)}"
                         for e, v in s3["proxy_check"].items()])

SN = {"K": "K (regime table)", "G": "G (generic de-risking)", "Fund": "Fund", "S-K": "S-K (static K weights)",
      "60/40": "60/40 fund/IEF", "VolTarget": "Volatility target 15\\%", "Trend": "10-month trend", "90/10 GLD": "90/10 fund/GLD"}


def maintab(key):
    b = R[key]
    return rows([f"{SN[k]} & {pc(b[k]['cagr_pct'],1)} & {pc(b[k]['vol_pct'],1)} & {n(b[k]['sharpe'],2)} & "
                 f"{pc(b[k]['maxdd_pct'],1)} & {pc(b[k]['worst12_pct'],1)} & {n(b[k]['avg_fund_weight'],2)} & {n(b[k]['turnover_per_year'],2)}"
                 for k in SN])


V["TAB_B_P1"], V["TAB_B_P0"] = maintab("rt_raw|P1"), maintab("rt_raw|P0")
for per in ("P1", "P0", "Pall", "Pold"):
    b = R[f"rt_raw|{per}"]
    for k, t in (("K", "k"), ("Fund", "f"), ("S-K", "s"), ("Trend", "t"), ("G", "g"), ("60/40", "sf"), ("VolTarget", "vt"), ("90/10 GLD", "gl")):
        V[f"{per}_{t}_sh"] = n(b[k]["sharpe"], 2)
        V[f"{per}_{t}_dd"] = pc(b[k]["maxdd_pct"], 1)
        V[f"{per}_{t}_cagr"] = pc(b[k]["cagr_pct"], 1)
        V[f"{per}_{t}_vol"] = pc(b[k]["vol_pct"], 1)
sw = s3["attribution"]["rt_raw|P1"]["static_weights"]
V["sk_w"] = ", ".join(f"{a.replace('FUND','fund')} {100*w:.0f}\\%" for a, w in sw.items())
V["k_turn"] = n(R["rt_raw|P1"]["K"]["turnover_per_year"], 2)

AN = {"rt_raw": "Real time, raw", "rt_smooth3_persist3": "Real time, smoothed + persistent", "revised_lag2": "Revised, lag 2"}
attr_rows = []
for cl, cn in AN.items():
    for per, pn in (("P1", "2007--2026"), ("P0", "2000--2007"), ("Pall", "2000--2026")):
        a = s3["attribution"][f"{cl}|{per}"]
        attr_rows.append(f"{cn} & {pn} & {n(a['sharpe_static'],2,True)} & {n(a['sharpe_timing'],2,True)} & "
                         f"{n(a['maxdd_static_pp'],1,True)} & {n(a['maxdd_timing_pp'],1,True)} & {n(a['ret_static_pp'],1,True)} & {n(a['ret_timing_pp'],1,True)}")
    attr_rows.append("\\midrule")
V["TAB_B_ATTR"] = rows(attr_rows[:-1]).replace("\\midrule \\\\", "\\midrule")
for per in ("P1", "P0", "Pall"):
    a = s3["attribution"][f"rt_raw|{per}"]
    V[f"{per}_st_sh"], V[f"{per}_ti_sh"] = n(a["sharpe_static"], 2, True), n(a["sharpe_timing"], 2, True)
    V[f"{per}_st_dd"], V[f"{per}_ti_dd"] = n(a["maxdd_static_pp"], 1, True), n(a["maxdd_timing_pp"], 1, True)
    V[f"{per}_st_ret"], V[f"{per}_ti_ret"] = n(a["ret_static_pp"], 1, True), n(a["ret_timing_pp"], 1, True)
V["rev_ti_sh"] = n(s3["attribution"]["revised_lag2|P1"]["sharpe_timing"], 2, True)

BN = {"K - Fund": "K $-$ fund", "S-K - Fund": "S-K $-$ fund (static)", "K - S-K": "K $-$ S-K (timing)", "K - Trend": "K $-$ trend"}
bt_rows = []
for per, pn in (("P1", "2007--2026"), ("P0", "2000--2007"), ("Pall", "2000--2026")):
    for k, kn in BN.items():
        b = s5["bootstrap"][per][k]
        bt_rows.append(f"{pn} & {kn} & {n(b['sharpe_diff'],2,True)} & $[{b['sharpe_ci90'][0]:+.2f},\\ {b['sharpe_ci90'][1]:+.2f}]$ & "
                       f"{n(b['sharpe_share_le0'],2)} & {n(b['maxdd_diff_pp'],1,True)} & $[{b['maxdd_ci90'][0]:+.1f},\\ {b['maxdd_ci90'][1]:+.1f}]$")
    bt_rows.append("\\midrule")
V["TAB_B_BOOT"] = rows(bt_rows[:-1]).replace("\\midrule \\\\", "\\midrule")
for per in ("P1", "P0", "Pall"):
    b = s5["bootstrap"][per]["K - S-K"]
    V[f"{per}_ti_ci"] = f"$[{b['sharpe_ci90'][0]:+.2f},\\ {b['sharpe_ci90'][1]:+.2f}]$"
    V[f"{per}_ti_le0"] = n(b["sharpe_share_le0"], 2)
    s = s5["bootstrap"][per]["S-K - Fund"]
    V[f"{per}_st_ci"] = f"$[{s['sharpe_ci90'][0]:+.2f},\\ {s['sharpe_ci90'][1]:+.2f}]$"
    d = s5["bootstrap"][per]["K - Fund"]
    V[f"{per}_kf_ddci"] = f"$[{d['maxdd_ci90'][0]:+.1f},\\ {d['maxdd_ci90'][1]:+.1f}]$"
V["P0_tr_ci"] = "$[{:+.2f},\\ {:+.2f}]$".format(*s5["bootstrap"]["P0"]["K - Trend"]["sharpe_ci90"])
V["P1_tr_ci"] = "$[{:+.2f},\\ {:+.2f}]$".format(*s5["bootstrap"]["P1"]["K - Trend"]["sharpe_ci90"])
V["P0_ti_ddci"] = "$[{:+.1f},\\ {:+.1f}]$".format(*s5["bootstrap"]["P0"]["K - S-K"]["maxdd_ci90"])
de = s5["deflated"]
V["dsr_n"], V["dsr_k"], V["dsr_f"] = str(de["K_rt_raw_P1"]["n_trials"]), n(de["K_rt_raw_P1"]["dsr"], 2), n(de["Fund"]["dsr"], 2)
V["dsr_here"] = str(de["K_rt_raw_P1"]["configs_here"])

HN = {"FBGRX": "Fidelity Blue Chip Growth", "TRBCX": "T. Rowe Price Blue Chip Growth", "AGTHX": "American Funds Growth Fund of America",
      "QQQ": "Nasdaq-100 (QQQ)", "IWF": "Russell 1000 Growth (IWF)", "SPY": "S\\&P 500 (SPY)"}
ho = s5["holdout"]
V["TAB_B_HOLD"] = rows([f"{HN[f]} & {n(ho[f]['P1']['sharpe']['K'],2)} & {n(ho[f]['P1']['sharpe']['S-K'],2)} & {n(ho[f]['P1']['timing_sharpe'],2,True)} & "
                        f"{n(ho[f]['P1']['timing_maxdd_pp'],1,True)} & {n(ho[f]['P0']['sharpe']['K'],2)} & {n(ho[f]['P0']['sharpe']['S-K'],2)} & "
                        f"{n(ho[f]['P0']['timing_sharpe'],2,True)} & {n(ho[f]['P0']['timing_maxdd_pp'],1,True)}" for f in HN])
p1t = [ho[f]["P1"]["timing_sharpe"] for f in HN]
p0t = [ho[f]["P0"]["timing_sharpe"] for f in HN]
V["ho_p1_rng"] = f"${min(p1t):+.2f}$ to ${max(p1t):+.2f}$"
V["ho_p0_rng"] = f"${min(p0t):+.2f}$ to ${max(p0t):+.2f}$"
V["ho_p1_ci"] = str(sum(ho[f]["P1"]["timing_sharpe_ci90"][0] > 0 for f in HN))
V["ho_p1_pos"] = s5["criterion"]["summary"]["P1"]["holdouts_timing_positive"]
V["ho_p0_pos"] = s5["criterion"]["summary"]["P0"]["holdouts_timing_positive"]
p0dd = [ho[f]["P0"]["timing_maxdd_pp"] for f in HN]
V["ho_p0_dd"] = f"${min(p0dd):+.1f}$ to ${max(p0dd):+.1f}$"

co = s6["costs"]
V["TAB_B_COST"] = rows([f"$\\times{m}$ & " + " & ".join(f"{n(co[f'x{m}|{p}'][k]['sharpe'],3)} & {n(co[f'x{m}|{p}'][k]['cost_bps_per_year'],1)}"
                                                         for p in ("P1", "P0") for k in ("K",)) + " & "
                        + " & ".join(n(co[f"x{m}|{p}"]["S-K"]["sharpe"], 3) for p in ("P1", "P0")) for m in (1, 2, 5)])
V["cost_k_p1"] = n(co["x1|P1"]["K"]["cost_bps_per_year"], 1)
V["cost_k_x5"] = n(co["x5|P1"]["K"]["cost_bps_per_year"], 1)
yr = s6["exploratory_timing_by_year"]
V["FIG_B_YEAR"] = " ".join(f"({y},{v:.2f})" for y, v in yr.items())
top = sorted(yr.items(), key=lambda x: -x[1])[:4]
bot = sorted(yr.items(), key=lambda x: x[1])[:4]
V["yr_top"] = ", ".join(f"{y} ({n(v,1,True)})" for y, v in top)
V["yr_bot"] = ", ".join(f"{y} ({n(v,1,True)})" for y, v in bot)
V["yr_2008"] = n(yr["2008"], 1, True)
V["yr_0003"] = n(sum(yr[str(y)] for y in range(2000, 2004)), 1, True)
w8 = s6["exploratory_p1_without_2008"]
V["wo8_k"], V["wo8_s"], V["wo8_f"] = n(w8["K"], 2), n(w8["S-K"], 2), n(w8["Fund"], 2)
V["wo8_ti"] = n(w8["K"] - w8["S-K"], 2, True)

tr = s6["exploratory_timing_by_regime"]
for per in ("P1", "P0"):
    for g, k in (("Goldilocks", "go"), ("Reflation", "re"), ("Disinflation", "di"), ("Stagflation", "st")):
        V[f"tr_{per}_{k}"] = n(tr[per][g]["timing_pp"], 1, True)
        V[f"tf_{per}_{k}"] = pc(tr[per][g]["fund_ann_pct"], 1, True)
    V[f"tr_{per}_sk"] = pc(100 * tr[per]["sk_fund_weight"], 0)
V["trend_0002"] = pc(100 * s6["exploratory_trend_fund_weight_2000_2002"], 0)
V["gap_mean"] = n(float(np.mean(list(gap.values()))), 2)
V["vol_gap_old"] = n(oc["vol_pct"] - po["Fund"]["vol_pct"], 1)
V["vol_ratio"] = n(R["rt_raw|P1"]["K"]["vol_pct"] / R["rt_raw|P1"]["Fund"]["vol_pct"], 2)
V["V_q4"] = pc(V8["2018Q4 (Oct-Dec) old -29.07"], 1)
V["V_22"] = pc(V8["2022 Jan-Oct old -12.56"], 1)
V["n_p0"] = str(R["rt_raw|P0"]["K"]["months"])
V["s_turn"] = n(R["rt_raw|P1"]["S-K"]["turnover_per_year"], 2)
# Step 10: independence of hold-outs, and four assets of different style and region.
V["TAB_B_HOLD"] = V["TAB_B_HOLD"] + "\n\\midrule\n" + rows([
    f"{v['name']} ({f}) & {n(v['P1']['sharpe']['K'],2)} & {n(v['P1']['sharpe']['S-K'],2)} & {n(v['P1']['timing_sharpe'],2,True)} & "
    f"{n(v['P1']['timing_maxdd_pp'],1,True)} & {n(v['P0']['sharpe']['K'],2)} & {n(v['P0']['sharpe']['S-K'],2)} & "
    f"{n(v['P0']['timing_sharpe'],2,True)} & {n(v['P0']['timing_maxdd_pp'],1,True)}" for f, v in s7["new"].items()])
rc_old = [s7["return_corr_with_fund"][f] for f in HN]
rc_new = [s7["return_corr_with_fund"][f] for f in s7["new"]]
tc_new = [s7["timing_corr_with_fund"][f] for f in s7["new"]]
V["rc_old"] = f"${min(rc_old):.2f}$--${max(rc_old):.2f}$"
V["rc_new"] = f"${min(rc_new):.2f}$--${max(rc_new):.2f}$"
V["tc_old_mean"] = n(s7["mean_pairwise_timing_corr_old"], 2)
V["tc_new"] = f"${min(tc_new):.2f}$--${max(tc_new):.2f}$"
V["neff7"], V["neff11"] = n(s7["neff_timing_old7"], 1), n(s7["neff_timing_all11"], 1)
V["new_pat"] = s7["new_with_pattern"]
p1n = [v["P1"]["timing_sharpe"] for v in s7["new"].values()]
p0n = [v["P0"]["timing_sharpe"] for v in s7["new"].values()]
V["new_p1_rng"] = f"${min(p1n):+.2f}$ to ${max(p1n):+.2f}$"
V["new_p0_rng"] = f"${min(p0n):+.2f}$ to ${max(p0n):+.2f}$"
# Step 11: continuous-signal model.
fm, al = s8["forecast"], s8["alloc"]
for per in ("P1", "P0"):
    V[f"m_r2_{per}"] = pc(fm[per]["oos_r2_pct"], 2, True)
    V[f"m_cw_{per}"] = n(fm[per]["clark_west_t"], 2)
    V[f"m_sh_{per}"], V[f"sm_sh_{per}"] = n(al[per]["M"]["sharpe"], 2), n(al[per]["S-M"]["sharpe"], 2)
    V[f"m_dd_{per}"], V[f"sm_dd_{per}"] = pc(al[per]["M"]["maxdd_pct"], 1), pc(al[per]["S-M"]["maxdd_pct"], 1)
    V[f"m_ti_{per}"] = n(al[per]["timing_sharpe"], 2, True)
    V[f"m_ci_{per}"] = "$[{:+.2f},\\ {:+.2f}]$".format(*al[per]["timing_ci90"])
    V[f"m_bd_{per}"] = pc(100 * al[per]["share_months_at_bounds"], 0)
V["m_first"] = s8["first_forecast"]
V["m_hedge"] = ", ".join(f"{k} {100*v:.0f}\\%" for k, v in s8["hedge_mix"].items())
# Step 12: mechanism.
mf = s9["full"]
V["mech_pos"], V["mech_pos_t"] = pc(mf["pos"]["stag_minus_others_ann_pct"], 1, True), n(mf["pos"]["t"], 2)
V["mech_neg"], V["mech_neg_t"] = pc(mf["neg"]["stag_minus_others_ann_pct"], 1, True), n(mf["neg"]["t"], 2)
V["mech_diff_t"] = n(mf["pos_minus_neg"]["t"], 2)
for sub, k in (("pre_2007", "pre"), ("post_2007", "post")):
    V[f"mech_{k}_pos"] = pc(s9[sub]["pos"]["stag_minus_others_ann_pct"], 1, True)
    V[f"mech_{k}_neg"] = pc(s9[sub]["neg"]["stag_minus_others_ann_pct"], 1, True)
V["mech_share_pre"], V["mech_share_post"] = pc(100 * s9["share_pos"]["pre_2007"], 0), pc(100 * s9["share_pos"]["post_2007"], 0)
V["mech_first"] = s9["first_decision"]

# Wealth curves over 2000-10..2026-09 (month-end, log scale).
wl = {}
for k in ("K", "S-K", "Fund", "Trend"):
    r = mon[("rt_raw|Pall", k)].dropna()
    w = np.r_[1.0, np.cumprod(1 + r.values)]
    xs = np.r_[2000 + 9 / 12, [p.year + (p.month) / 12 for p in r.index]]
    keep = sorted(set(range(0, len(w), 3)) | {len(w) - 1})  # quarter-ends and the last month
    wl[k] = " ".join(f"({xs[i]:.2f},{w[i]:.3f})" for i in keep)
V["FIG_B_K"], V["FIG_B_S"], V["FIG_B_F"], V["FIG_B_T"] = wl["K"], wl["S-K"], wl["Fund"], wl["Trend"]
V["reg_n"], V["reg_pass"] = str(treg["n"]), str(treg["passed"])
V["tb_ctrl"] = tb["positive_control_flagged"].split(" ")[0]

# ---------------------------------------------------------------- references
REFS = {
    "ang2002": "Ang, A. and Bekaert, G. (2002). International asset allocation with regime shifts. \\emph{Review of Financial Studies}, 15(4), 1137--1187.",
    "bailey2014": "Bailey, D.~H. and L\\'opez de Prado, M. (2014). The deflated Sharpe ratio: correcting for selection bias, backtest overfitting, and non-normality. \\emph{Journal of Portfolio Management}, 40(5), 94--107.",
    "campbell2020": "Campbell, J.~Y., Pflueger, C. and Viceira, L.~M. (2020). Macroeconomic drivers of bond and equity risks. \\emph{Journal of Political Economy}, 128(8), 3148--3185.",
    "croushore2001": "Croushore, D. and Stark, T. (2001). A real-time data set for macroeconomists. \\emph{Journal of Econometrics}, 105(1), 111--130.",
    "erb2013": "Erb, C.~B. and Harvey, C.~R. (2013). The golden dilemma. \\emph{Financial Analysts Journal}, 69(4), 10--42.",
    "faber2007": "Faber, M.~T. (2007). A quantitative approach to tactical asset allocation. \\emph{Journal of Wealth Management}, 9(4), 69--79.",
    "harvey2016": "Harvey, C.~R., Liu, Y. and Zhu, H. (2016). \\ldots and the cross-section of expected returns. \\emph{Review of Financial Studies}, 29(1), 5--68.",
    "ilmanen2011": "Ilmanen, A. (2011). \\emph{Expected Returns: An Investor's Guide to Harvesting Market Rewards}. Wiley.",
    "ledoit2008": "Ledoit, O. and Wolf, M. (2008). Robust performance hypothesis testing with the Sharpe ratio. \\emph{Journal of Empirical Finance}, 15(5), 850--859.",
    "moreira2017": "Moreira, A. and Muir, T. (2017). Volatility-managed portfolios. \\emph{Journal of Finance}, 72(4), 1611--1644.",
    "moskowitz2012": "Moskowitz, T.~J., Ooi, Y.~H. and Pedersen, L.~H. (2012). Time series momentum. \\emph{Journal of Financial Economics}, 104(2), 228--250.",
    "newey1987": "Newey, W.~K. and West, K.~D. (1987). A simple, positive semi-definite, heteroskedasticity and autocorrelation consistent covariance matrix. \\emph{Econometrica}, 55(3), 703--708.",
    "orphanides2001": "Orphanides, A. (2001). Monetary policy rules based on real-time data. \\emph{American Economic Review}, 91(4), 964--985.",
    "politis1994": "Politis, D.~N. and Romano, J.~P. (1994). The stationary bootstrap. \\emph{Journal of the American Statistical Association}, 89(428), 1303--1313.",
    "welch2008": "Welch, I. and Goyal, A. (2008). A comprehensive look at the empirical performance of equity premium prediction. \\emph{Review of Financial Studies}, 21(4), 1455--1508.",
}
LABEL = {"ang2002": "Ang and Bekaert(2002)", "bailey2014": "Bailey and L\\'opez de Prado(2014)",
         "campbell2020": "Campbell et al.(2020)", "croushore2001": "Croushore and Stark(2001)",
         "erb2013": "Erb and Harvey(2013)", "faber2007": "Faber(2007)", "harvey2016": "Harvey et al.(2016)",
         "ilmanen2011": "Ilmanen(2011)", "ledoit2008": "Ledoit and Wolf(2008)", "moreira2017": "Moreira and Muir(2017)",
         "moskowitz2012": "Moskowitz et al.(2012)", "newey1987": "Newey and West(1987)", "orphanides2001": "Orphanides(2001)",
         "politis1994": "Politis and Romano(1994)", "welch2008": "Welch and Goyal(2008)"}


# Step 11: robustness of the inference
RB = json.loads((RESULTS / "s10_robustness.json").read_text())
_p = lambda x: f"${x:.3f}$" if x < 0.01 else f"${x:.2f}$"
for per, tag in (("P1", "P1"), ("P0", "P0"), ("Pall", "Pall")):
    lw = RB["periods"][per]["ledoit_wolf"]
    V[f"lw_{tag}_kf"], V[f"lw_{tag}_st"], V[f"lw_{tag}_ti"] = (_p(lw[k]["p"]) for k in ("K - Fund", "S-K - Fund", "K - S-K"))
CR = RB["crisis_removed"]
V["cr_kf"] = f"${CR['K - Fund']['sharpe_diff']:+.2f}$"; V["cr_kf_p"] = _p(CR["K - Fund"]["ledoit_wolf"]["p"])
V["cr_kf_ci"] = "$[{:+.2f},\\ {:+.2f}]$".format(*CR["K - Fund"]["ci90"])
V["cr_ti"] = f"${CR['K - S-K']['sharpe_diff']:+.2f}$"; V["cr_ti_p"] = _p(CR["K - S-K"]["ledoit_wolf"]["p"])
V["cr_ti_ci"] = "$[{:+.2f},\\ {:+.2f}]$".format(*CR["K - S-K"]["ci90"])
H3 = RB["h3_difference"]
V["h3_diff"], V["h3_z"], V["h3_p"] = f"${H3['diff']:.1f}$", f"${H3['z']:.2f}$", _p(H3["p"])
V["rb_blocks"] = "6, 12 and 24"


def fill(template, outname):
    t = (P / template).read_text()
    missing = sorted(set(re.findall(r"@@(\w+)@@", t)) - set(V))
    assert not missing, f"{template}: missing {missing}"
    for k, v in V.items():
        t = t.replace(f"@@{k}@@", v)
    cited = sorted(set(sum((c.split(",") for c in re.findall(r"\\cite[pt]?\{([^}]+)\}", t)), [])))
    cited = [c.strip() for c in cited]
    unknown = [c for c in cited if c not in REFS]
    assert not unknown, f"{template}: unknown references {unknown}"
    bib = "\n".join(f"\\bibitem[{LABEL[c]}]{{{c}}} {REFS[c]}" for c in sorted(cited))
    t = t.replace("%%BIB%%", bib)
    (P / outname).write_text(t)
    return len(cited)


if __name__ == "__main__":
    json.dump({k: v for k, v in V.items() if len(str(v)) < 200}, open(ROOT / "results" / "paper_values.json", "w"),
              indent=0, sort_keys=True)
    c = fill("template.tex", "paper.tex")
    print(f"paper.tex ({c} references)")
