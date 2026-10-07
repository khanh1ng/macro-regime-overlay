"""Write the top of README.md (summary, hypotheses and verdicts, results, mechanism, threats to
validity) between <!-- TOP:START --> and <!-- TOP:END -->. Every number comes from results/: the
paper values (results/paper_values.json, the same strings the paper prints) and s5_stats.json.
No number in that block is typed by hand."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mo.config import ROOT, RESULTS  # noqa: E402


def neg(s):
    return re.sub(r"(?<![\w.])-(?=\d)", "−", s)


def clean(v):
    s = str(v).replace("\\%", "%").replace("{,}", ",").replace("\\$", "\x00").replace("$", "").replace("\x00", "$")
    s = s.replace("\\ ", " ").replace("--", "–")
    return neg(s).strip()


def ci(x, d=2):
    return neg(f"[{x[0]:+.{d}f}, {x[1]:+.{d}f}]")


def main():
    V = {k: clean(v) for k, v in json.loads((RESULTS / "paper_values.json").read_text()).items()}
    B = json.loads((RESULTS / "s5_stats.json").read_text())["bootstrap"]
    d = lambda per, k: B[per][k]
    kf1, kf0, kfa = d("P1", "K - Fund"), d("P0", "K - Fund"), d("Pall", "K - Fund")
    RB = json.loads((RESULTS / "s10_robustness.json").read_text())
    lw = lambda per, k: RB["periods"][per]["ledoit_wolf"][k]["p"]
    pv = lambda x: f"{x:.3f}" if x < 0.05 else f"{x:.2f}"
    CR, H3 = RB["crisis_removed"], RB["h3_difference"]
    MR = json.loads((RESULTS / "s11_market_regimes.json").read_text())
    mo = {per: RB["periods"][per]["months"] for per in RB["periods"]}

    rows = ["| Strategy | CAGR 2007–26 | Sharpe 2007–26 | Max DD 2007–26 | CAGR 2000–07 | Sharpe 2000–07 | Max DD 2000–07 |",
            "|---|---:|---:|---:|---:|---:|---:|"]
    for code, label in (("k", "Regime overlay (K)"), ("f", "Fund alone"), ("s", "K's average weights, no timing (S-K)"),
                        ("sf", "60/40 fund/IEF"), ("t", "10-month trend rule"), ("vt", "Volatility target 15%")):
        rows.append(f"| {label} | {V[f'P1_{code}_cagr']} | {V[f'P1_{code}_sh']} | {V[f'P1_{code}_dd']} | "
                    f"{V[f'P0_{code}_cagr']} | {V[f'P0_{code}_sh']} | {V[f'P0_{code}_dd']} |")
    table = "\n".join(rows)

    text = f"""# macro-regime-overlay

**Real-time macro regimes and a concentrated growth fund: the overlay's gain is mostly
diversification; the timing gain rests on the 2008 crisis.** One paper; regimes from data
published at the time; specification frozen before the backtest; evaluation 2000–2026.
*Original backtest spring 2026; re-tested with real-time data and a frozen specification, October 2026.*

**Summary.** A growth–inflation regime overlay on the JPMorgan Large Cap Growth Fund, built only from
data available at each date ({V['ip_n']} vintages of industrial production, consumer prices that are never
revised), raised the Sharpe ratio from {V['P1_f_sh']} to {V['P1_k_sh']} and cut the maximum drawdown from {V['P1_f_dd']}
to {V['P1_k_dd']} in 2007–2026 (Sharpe difference {kf1['sharpe_diff']:+.2f}, 90% bootstrap CI {ci(kf1['sharpe_ci90'])}, Ledoit–Wolf
p = {pv(lw('P1', 'K - Fund'))}). That gain rests on one crisis: without October 2007 to March 2009 it is
{CR['K - Fund']['sharpe_diff']:+.2f} (p = {pv(CR['K - Fund']['ledoit_wolf']['p'])}). Splitting the gain shows two parts that behave differently.
Holding the overlay's average weights without timing raises the Sharpe ratio before 2007 (p = {pv(lw('P0', 'S-K - Fund'))})
and over 2000–2026 (p = {pv(lw('Pall', 'S-K - Fund'))}). Regime timing adds {V['P1_ti_sh']} after 2007 (p = {pv(lw('P1', 'K - S-K'))}; {pv(CR['K - S-K']['ledoit_wolf']['p'])}
without the crisis) and {V['P0_ti_sh']} before (not significant). The defensible recommendation is the
diversified allocation; regime timing is a bet that 2008-type episodes, and the post-2007 relation,
recur.

**Paper:** [`paper/paper.pdf`](paper/paper.pdf). **Every step, with what was fixed before it ran:**
[`docs/RESEARCH_LOG.md`](docs/RESEARCH_LOG.md).

## Hypotheses and verdicts

| | Hypothesis | Test | Evidence | Verdict |
|---|---|---|---|---|
| H1 | Revised macro data change the regimes a backtest uses | Same rule on real-time vintages and on today's revised data | Agreement {V['agree_rev1']} of {V['raw_months']} months; the usual construction (revised, two-month lag) agrees with what was knowable in {V['agree_rev2']} | **Supported** |
| H2 | Real-time regimes forecast next month's excess returns | Wald test of equal mean excess returns across the four regimes (Newey–West errors), {V['n_assets']} assets × 3 classifiers = {V['n_tests']} tests; Bonferroni | {V['nbonf_all']} of {V['n_tests']} pass (threshold p < {V['bonf']}; conservative, since the classifiers are correlated). With the main classifier {V['n05_raw']} of {V['n_assets']} has p < 0.05, about what chance gives. Power is low: an effect would need about {V['mde_full']} a year to be detected with 80% probability | **Not supported** |
| H3 | The fund's response to Stagflation is stable | Stagflation-minus-other contrast before and after 2007 (split fixed before any regime result), and the difference | {V['pre_con']} a year (t = {V['pre_cont']}) before 2007; {V['post_con']} (t = {V['post_cont']}) after; change {H3['diff']:.1f} points, z = {H3['z']:.2f}, p = {pv(H3['p'])} | **Rejected**: the response changed sign |
| H4 | The overlay improves on the fund | Sharpe difference: stationary bootstrap (mean blocks 6, 12, 24 months) and Ledoit–Wolf HAC test | 2007–2026 ({mo['P1']} months, partly in sample): {kf1['sharpe_diff']:+.2f} {ci(kf1['sharpe_ci90'])}, p = {pv(lw('P1', 'K - Fund'))}; without Oct 2007–Mar 2009: {CR['K - Fund']['sharpe_diff']:+.2f}, p = {pv(CR['K - Fund']['ledoit_wolf']['p'])}. 2000–2007 ({mo['P0']} months): {kf0['sharpe_diff']:+.2f} {ci(kf0['sharpe_ci90'])}, p = {pv(lw('P0', 'K - Fund'))}. 2000–2026: {kfa['sharpe_diff']:+.2f}, p = {pv(lw('Pall', 'K - Fund'))}. Max drawdown {kf1['maxdd_diff_pp']:+.1f} and {kf0['maxdd_diff_pp']:+.1f} pp shallower (point estimates) | **Supported** after 2007 and overall, **but only through the 2008 crisis**; not before 2007 |
| H5 | The average allocation, without timing, adds value | S-K minus fund, same tests | Sharpe {V['P1_st_sh']} {V['P1_st_ci']} after 2007 (p = {pv(lw('P1', 'S-K - Fund'))}), {V['P0_st_sh']} {V['P0_st_ci']} before (p = {pv(lw('P0', 'S-K - Fund'))}), {V['Pall_st_sh']} {V['Pall_st_ci']} overall (p = {pv(lw('Pall', 'S-K - Fund'))}); drawdown {V['P1_st_dd']} and {V['P0_st_dd']} pp shallower (point estimates) | **Supported** before 2007 (fully out of sample) and overall; not significant after 2007 |
| H6 | Regime timing adds value (criterion fixed in advance: CI above 0 in both periods, same sign in at least 5 of 6 hold-out funds) | K minus S-K, same tests; six hold-out growth funds and indices | {V['P1_ti_sh']} {V['P1_ti_ci']} after 2007 (p = {pv(lw('P1', 'K - S-K'))}; without the crisis {CR['K - S-K']['sharpe_diff']:+.2f}, p = {pv(CR['K - S-K']['ledoit_wolf']['p'])}); {V['P0_ti_sh']} {V['P0_ti_ci']} before (p = {pv(lw('P0', 'K - S-K'))}, interval includes zero); hold-outs positive {V['ho_p1_pos']} after, {V['ho_p0_pos']} before | **Rejected**: positive only after 2007 and only with 2008 |
| H7 | The hold-outs are independent confirmation | Effective number of independent timing series, (Σλ)²/Σλ² | {V['neff11']} for 11 equity assets of different styles and regions | **Not supported**: they move together |
| H8 | A predictive regression on the same signals does better | Regression on the two real-time signals fitted on all earlier data; out-of-sample R², Clark–West | R² {V['m_r2_P1']} after 2007, {V['m_r2_P0']} before; Clark–West t {V['m_cw_P1']} and {V['m_cw_P0']} | **Rejected** |
| H9 | The stock–bond correlation explains the sign change | Stagflation contrast split by the sign of the trailing 36-month fund–Treasury correlation | Difference t = {V['mech_diff_t']} | **Not supported** |
| H10 | Regimes read from market prices, which have no publication delay, time the fund better | SPY − Treasuries and commodities − Treasuries over 6 months, same sign rule; spec fixed before the run; walk-forward variant | Timing over its own static mix {MR['periods']['P1']['tests']['M1 - S-M1']['sharpe_diff']:+.2f} (p = {pv(MR['periods']['P1']['tests']['M1 - S-M1']['ledoit_wolf']['p'])}) after 2007, {MR['periods']['P0']['tests']['M1 - S-M1']['sharpe_diff']:+.2f} (p = {pv(MR['periods']['P0']['tests']['M1 - S-M1']['ledoit_wolf']['p'])}) before; worse than macro K after 2007 ({neg(f"{MR['periods']['P1']['tests']['M1 - K']['sharpe_diff']:+.2f}")}, p = {pv(MR['periods']['P1']['tests']['M1 - K']['ledoit_wolf']['p'])}); labels agree with macro in {100 * MR['agreement_with_macro']['share']:.0f}% of months | **Not supported** |

## Results (after costs)

{table}

Monthly returns after one-way trading costs per sleeve; Sharpe ratios annualised (×√12) from monthly
returns in excess of the 3-month T-bill; max DD on month-end values. 2007-04 to 2026-09 overlaps the 2011–2026 data the allocation table was designed on, so
it is partly in sample; 2000-10 to 2007-03 is fully out of sample. Differences and their bootstrap
intervals are in H4–H6 above.

## Mechanism: where the overlay's gain comes from

* **Diversification lowers volatility at a cost in return.** After 2007 the average allocation
  ({V['sk_w']}) gives up {V['P1_st_ret'].lstrip('−')} points a year of return but raises the Sharpe ratio
  and cuts the drawdown by {V['P1_st_dd'].lstrip('+')} points.
* **The gain after 2007 is one crash.** Real-time data labelled 2008 as Stagflation, so the overlay held
  little of the fund during the crash. Without October 2007 to March 2009, the overlay's advantage falls
  from {kf1['sharpe_diff']:+.2f} to {CR['K - Fund']['sharpe_diff']:+.2f} and timing's from {V['P1_ti_sh']} to {CR['K - S-K']['sharpe_diff']:+.2f}, neither significant.
* **The same rule hurt before 2007** because the fund did well in Stagflation then ({V['pre_con']} a year
  relative to other regimes), and the overlay cut it.

## Threats to validity

| Threat | How it is handled | What remains |
|---|---|---|
| Look-ahead | Real-time vintages; truncation tests at {V['tl_cuts']} cuts with a positive control | None known |
| Small samples and dependent returns | HAC standard errors; Ledoit–Wolf test alongside the bootstrap; block lengths 6–24 months; significance requires both ([spec](docs/RESEARCH_LOG.md)) | {mo['P0']} months before 2007 is short; power is low (H2) |
| One crisis per period | 2007–2026 re-tested without October 2007 to March 2009 | The later gains do not survive it; drawdowns are reported as point estimates, not tested |
| Data errors | Fund returns checked against its annual report to the SEC (within {V['v1_max']} points a year) | Proxies before ETF inception |
| Specification search | Allocation table frozen before this study; {V['dsr_n']} configurations counted | The table was designed on 2011–2026, so 2007–2026 is partly in sample; only 2000–2007 is fully out of sample |
| Few independent assets | Ten more equity assets of different styles and regions | They behave like {V['neff11']} series |
| Costs | One-way costs per sleeve, doubled and ×5 | {V['cost_k_x5']} bps a year at ×5: immaterial |

## Implications

* **For an allocator:** hold the diversified mix; it improved risk-adjusted return in the period not
  used to design it and rebalances with low turnover ({V['s_turn']} a year). The timing layer earned its
  gain in one crisis; adopting it is a bet that such episodes recur with the same regime signature.
* **For research:** build regimes from real-time vintages, separate timing from average allocation,
  and judge timing in a period not used to design it. Stronger evidence needs independent episodes,
  for example other countries.
"""
    path = ROOT / "README.md"
    s = path.read_text()
    pat = re.compile(r"<!-- TOP:START -->\n.*?<!-- TOP:END -->", re.S)
    assert pat.search(s), "TOP markers missing in README.md"
    path.write_text(pat.sub(lambda m: "<!-- TOP:START -->\n" + text + "<!-- TOP:END -->", s))
    print("README.md top section written")


if __name__ == "__main__":
    main()
