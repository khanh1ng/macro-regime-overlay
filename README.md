<!-- TOP:START -->
# macro-regime-overlay

**Real-time macro regimes and a concentrated growth fund: the overlay's gain is mostly
diversification; regime timing worked only after 2007.** One paper (15 pages); regimes from data
published at the time; specification frozen before the backtest; evaluation 2000–2026.

**Summary.** A growth–inflation regime overlay on the JPMorgan Large Cap Growth Fund, built only from
data available at each date (766 vintages of industrial production, consumer prices that are never
revised), raised the Sharpe ratio from 0.75 to 1.07 and cut the maximum drawdown from −47.6%
to −18.2% in 2007–2026 (difference +0.32, 90% bootstrap CI [+0.06, +0.55]). Splitting the gain shows two
parts that behave differently. Holding the overlay's average weights without timing improves the
Sharpe ratio over 2000–2026 (+0.14, [+0.05, +0.22]) and makes the drawdown shallower in both
periods. Regime timing adds +0.22 [+0.03, +0.41] after 2007 but −0.18 [−0.32, +0.05] before, where it also
deepens the drawdown. The robust recommendation is the diversified allocation; regime timing is a
bet that the post-2007 relation continues.

**Paper:** [`paper/paper.pdf`](paper/paper.pdf). **Every step, with what was fixed before it ran:**
[`docs/RESEARCH_LOG.md`](docs/RESEARCH_LOG.md).

## Hypotheses and verdicts

| | Hypothesis | Test | Evidence | Verdict |
|---|---|---|---|---|
| H1 | Revised macro data change the regimes a backtest uses | Same rule on real-time vintages and on today's revised data | Agreement 81.8% of 440 months; the usual construction (revised, two-month lag) agrees with what was knowable in 67.3% | **Supported** |
| H2 | Real-time regimes forecast next month's excess returns | 36 regime-contrast tests on 12 assets, Newey–West errors, Bonferroni | 0 of 36 pass (threshold p < 0.0014). Power is low: an effect would need about 21% a year to be detected with 80% probability | **Not supported** |
| H3 | The fund's response to Stagflation is stable | Stagflation-minus-other contrast before and after 2007 | +14.0% a year (t = +1.36) before 2007; −20.9% (t = −2.21) after | **Rejected**: the sign reverses |
| H4 | The overlay improves on the fund | Stationary bootstrap of Sharpe and drawdown differences | 2007–2026: +0.32 [+0.06, +0.55], drawdown +29.4 pp [+7.3, +37.0], partly in sample. 2000–2007: +0.04 [−0.17, +0.40], drawdown +9.2 pp [+3.9, +15.6]. 2000–2026: +0.23 [+0.04, +0.43] | **Supported** for drawdown in both periods; Sharpe significant after 2007 and overall |
| H5 | The average allocation, without timing, adds value | S-K minus fund | Sharpe +0.09 [−0.01, +0.19] after 2007, +0.22 [+0.11, +0.39] before, +0.14 [+0.05, +0.22] overall; drawdown +16.5 and +18.7 pp shallower | **Supported** overall and before 2007; positive but not significant after 2007 |
| H6 | Regime timing adds value (criterion fixed in advance: CI above 0 in both periods, same sign in at least 5 of 6 hold-out funds) | K minus S-K; six hold-out growth funds and indices | +0.22 [+0.03, +0.41] after 2007, −0.18 [−0.32, +0.05] before; hold-outs positive 6/6 after, 0/6 before | **Rejected** (era-dependent) |
| H7 | The hold-outs are independent confirmation | Effective number of independent timing series, (Σλ)²/Σλ² | 1.2 for 11 equity assets of different styles and regions | **Not supported**: they move together |
| H8 | A predictive regression on the same signals does better | Regression on the two real-time signals fitted on all earlier data; out-of-sample R², Clark–West | R² −0.23% after 2007, −3.31% before | **Rejected** |
| H9 | The stock–bond correlation explains the sign change | Stagflation contrast split by the sign of the trailing 36-month fund–Treasury correlation | Difference t = 0.86 | **Not supported** |

## Results (after costs)

| Strategy | 2007–2026 CAGR | Sharpe | Max drawdown | 2000–2007 CAGR | Sharpe | Max drawdown |
|---|---:|---:|---:|---:|---:|---:|
| Regime overlay (K) | 14.3% | 1.07 | −18.2% | −2.2% | −0.35 | −47.5% |
| Fund alone | 14.1% | 0.75 | −47.6% | −5.2% | −0.40 | −56.8% |
| K's average weights, no timing (S-K) | 11.4% | 0.84 | −31.0% | 0.2% | −0.18 | −38.1% |
| 60/40 fund/IEF | 10.0% | 0.80 | −27.0% | −0.1% | −0.26 | −31.3% |
| 10-month trend rule | 11.4% | 0.76 | −19.7% | 7.4% | 0.73 | −7.4% |
| Volatility target 15% | 11.7% | 0.72 | −36.1% | −0.4% | −0.21 | −37.3% |

## Mechanism: where the overlay's gain comes from

* **Diversification lowers volatility at a cost in return.** After 2007 the average allocation
  (fund 61%, HYG 8%, GLD 18%, DBC 1%, SHY 7%, UUP 5%) gives up 3.2 points a year of return but raises the Sharpe ratio
  and cuts the drawdown by 16.5 points.
* **The timing gain after 2007 is concentrated in one crash.** Real-time data labelled 2008 as
  Stagflation, so the overlay held little of the fund during the crash. Excluding October 2007 to March
  2009, the timing gain falls from +0.22 to +0.11.
* **The same rule hurt before 2007** because the fund did well in Stagflation then (+14.0% a year
  relative to other regimes), and the overlay cut it.

## Threats to validity

| Threat | How it is handled | What remains |
|---|---|---|
| Look-ahead | Real-time vintages; truncation tests at 60 cuts with a positive control | None known |
| Data errors | Fund returns checked against its annual report to the SEC (within 0.07 points a year) | Proxies before ETF inception |
| Specification search | Allocation table frozen before this study; 54 configurations counted | The table was designed on 2011–2026, so 2007–2026 is partly in sample; only 2000–2007 is fully out of sample |
| Few episodes | Bootstrap intervals; ten more equity assets | Each period is dominated by one crash; the assets behave like 1.2 series |
| Costs | One-way costs per sleeve, doubled and ×5 | 14.0 bps a year at ×5: immaterial |

## Implications

* **For an allocator:** hold the diversified mix; it improved risk-adjusted return out of sample and
  rebalances with low turnover (0.32 a year). Adopting the timing layer is a bet that the
  post-2007 relation between regimes and growth equities persists.
* **For research:** build regimes from real-time vintages, separate timing from average allocation,
  and judge timing in a period not used to design it. Stronger evidence needs independent episodes,
  for example other countries.
<!-- TOP:END -->

## Layout

```
mo/            data (Yahoo with distributions), macro (real-time IP vintages, unrevised CPI), regime,
               backtest (proxies, drift-aware turnover), strategies, stats (Newey-West, Wald), boot (stationary bootstrap)
scripts/       s0_verify ... s9_mechanism: one script per step; make_papers fills paper/template.tex; fetch_data
tests/         look-ahead tests with positive controls, engine checks, regression checks
paper/         template.tex (with @@placeholders@@), generated paper.tex, paper.pdf
results/       every number in the paper, as JSON/CSV
docs/          research log
data/          reference_returns.json (from the SEC filing), old_claims.json; downloaded data is not tracked
```

## Reproducing

```bash
pip install numpy pandas scipy requests pyarrow openpyxl pandas-datareader
python scripts/fetch_data.py   # Yahoo, FRED, Philadelphia Fed; no key needed
python run_all.py              # every step, every test, and the paper (about 1–2 minutes)
latexmk -pdf -cd paper/paper.tex
```

On the data snapshot used for the paper (fetched 2026-09-30), two full runs produce byte-identical
results and paper source. A later download can differ slightly if vendors revise history;
`scripts/s0_verify.py` checks the fund's returns against its annual report before anything else runs.

## License

MIT
