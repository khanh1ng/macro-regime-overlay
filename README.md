<!-- TOP:START -->
# macro-regime-overlay

**Real-time macro regimes and a concentrated growth fund: the overlay's gain is mostly
diversification; the timing gain rests on the 2008 crisis.** One paper; regimes from data
published at the time; specification frozen before the backtest; evaluation 2000–2026.
*Original backtest spring 2026; re-tested with real-time data and a frozen specification, October 2026.*

**Summary.** A growth–inflation regime overlay on the JPMorgan Large Cap Growth Fund, built only from
data available at each date (766 vintages of industrial production, consumer prices that are never
revised), raised the Sharpe ratio from 0.75 to 1.07 and cut the maximum drawdown from −47.6%
to −18.2% in 2007–2026 (Sharpe difference +0.32, 90% bootstrap CI [+0.06, +0.55], Ledoit–Wolf
p = 0.028). That gain rests on one crisis: without October 2007 to March 2009 it is
+0.19 (p = 0.14). Splitting the gain shows two parts that behave differently.
Holding the overlay's average weights without timing raises the Sharpe ratio before 2007 (p = 0.007)
and over 2000–2026 (p = 0.005). Regime timing adds +0.22 after 2007 (p = 0.07; 0.21
without the crisis) and −0.18 before (not significant). The defensible recommendation is the
diversified allocation; regime timing is a bet that 2008-type episodes, and the post-2007 relation,
recur.

**Paper:** [`paper/paper.pdf`](paper/paper.pdf). **Every step, with what was fixed before it ran:**
[`docs/RESEARCH_LOG.md`](docs/RESEARCH_LOG.md).

## Hypotheses and verdicts

| | Hypothesis | Test | Evidence | Verdict |
|---|---|---|---|---|
| H1 | Revised macro data change the regimes a backtest uses | Same rule on real-time vintages and on today's revised data | Agreement 81.8% of 440 months; the usual construction (revised, two-month lag) agrees with what was knowable in 67.3% | **Supported** |
| H2 | Real-time regimes forecast next month's excess returns | Wald test of equal mean excess returns across the four regimes (Newey–West errors), 12 assets × 3 classifiers = 36 tests; Bonferroni | 0 of 36 pass (threshold p < 0.0014; conservative, since the classifiers are correlated). With the main classifier 1 of 12 has p < 0.05, about what chance gives. Power is low: an effect would need about 21% a year to be detected with 80% probability | **Not supported** |
| H3 | The fund's response to Stagflation is stable | Stagflation-minus-other contrast before and after 2007 (split fixed before any regime result), and the difference | +14.0% a year (t = +1.36) before 2007; −20.9% (t = −2.21) after; change 34.9 points, z = 2.50, p = 0.013 | **Rejected**: the response changed sign |
| H4 | The overlay improves on the fund | Sharpe difference: stationary bootstrap (mean blocks 6, 12, 24 months) and Ledoit–Wolf HAC test | 2007–2026 (234 months, partly in sample): +0.32 [+0.06, +0.55], p = 0.028; without Oct 2007–Mar 2009: +0.19, p = 0.14. 2000–2007 (78 months): +0.04 [−0.17, +0.40], p = 0.79. 2000–2026: +0.23, p = 0.044. Max drawdown +29.4 and +9.2 pp shallower (point estimates) | **Supported** after 2007 and overall, **but only through the 2008 crisis**; not before 2007 |
| H5 | The average allocation, without timing, adds value | S-K minus fund, same tests | Sharpe +0.09 [−0.01, +0.19] after 2007 (p = 0.13), +0.22 [+0.11, +0.39] before (p = 0.007), +0.14 [+0.05, +0.22] overall (p = 0.005); drawdown +16.5 and +18.7 pp shallower (point estimates) | **Supported** before 2007 (fully out of sample) and overall; not significant after 2007 |
| H6 | Regime timing adds value (criterion fixed in advance: CI above 0 in both periods, same sign in at least 5 of 6 hold-out funds) | K minus S-K, same tests; six hold-out growth funds and indices | +0.22 [+0.03, +0.41] after 2007 (p = 0.07; without the crisis +0.12, p = 0.21); −0.18 [−0.32, +0.05] before (p = 0.09, interval includes zero); hold-outs positive 6/6 after, 0/6 before | **Rejected**: positive only after 2007 and only with 2008 |
| H7 | The hold-outs are independent confirmation | Effective number of independent timing series, (Σλ)²/Σλ² | 1.2 for 11 equity assets of different styles and regions | **Not supported**: they move together |
| H8 | A predictive regression on the same signals does better | Regression on the two real-time signals fitted on all earlier data; out-of-sample R², Clark–West | R² −0.23% after 2007, −3.31% before; Clark–West t 0.80 and −0.53 | **Rejected** |
| H9 | The stock–bond correlation explains the sign change | Stagflation contrast split by the sign of the trailing 36-month fund–Treasury correlation | Difference t = 0.86 | **Not supported** |

## Results (after costs)

| Strategy | CAGR 2007–26 | Sharpe 2007–26 | Max DD 2007–26 | CAGR 2000–07 | Sharpe 2000–07 | Max DD 2000–07 |
|---|---:|---:|---:|---:|---:|---:|
| Regime overlay (K) | 14.3% | 1.07 | −18.2% | −2.2% | −0.35 | −47.5% |
| Fund alone | 14.1% | 0.75 | −47.6% | −5.2% | −0.40 | −56.8% |
| K's average weights, no timing (S-K) | 11.4% | 0.84 | −31.0% | 0.2% | −0.18 | −38.1% |
| 60/40 fund/IEF | 10.0% | 0.80 | −27.0% | −0.1% | −0.26 | −31.3% |
| 10-month trend rule | 11.4% | 0.76 | −19.7% | 7.4% | 0.73 | −7.4% |
| Volatility target 15% | 11.7% | 0.72 | −36.1% | −0.4% | −0.21 | −37.3% |

Monthly returns after one-way trading costs per sleeve; Sharpe ratios annualised (×√12) from monthly
returns in excess of the 3-month T-bill; max DD on month-end values. 2007-04 to 2026-09 overlaps the 2011–2026 data the allocation table was designed on, so
it is partly in sample; 2000-10 to 2007-03 is fully out of sample. Differences and their bootstrap
intervals are in H4–H6 above.

## Mechanism: where the overlay's gain comes from

* **Diversification lowers volatility at a cost in return.** After 2007 the average allocation
  (fund 61%, HYG 8%, GLD 18%, DBC 1%, SHY 7%, UUP 5%) gives up 3.2 points a year of return but raises the Sharpe ratio
  and cuts the drawdown by 16.5 points.
* **The gain after 2007 is one crash.** Real-time data labelled 2008 as Stagflation, so the overlay held
  little of the fund during the crash. Without October 2007 to March 2009, the overlay's advantage falls
  from +0.32 to +0.19 and timing's from +0.22 to +0.12, neither significant.
* **The same rule hurt before 2007** because the fund did well in Stagflation then (+14.0% a year
  relative to other regimes), and the overlay cut it.

## Threats to validity

| Threat | How it is handled | What remains |
|---|---|---|
| Look-ahead | Real-time vintages; truncation tests at 60 cuts with a positive control | None known |
| Small samples and dependent returns | HAC standard errors; Ledoit–Wolf test alongside the bootstrap; block lengths 6–24 months; significance requires both ([spec](docs/RESEARCH_LOG.md)) | 78 months before 2007 is short; power is low (H2) |
| One crisis per period | 2007–2026 re-tested without October 2007 to March 2009 | The later gains do not survive it; drawdowns are reported as point estimates, not tested |
| Data errors | Fund returns checked against its annual report to the SEC (within 0.07 points a year) | Proxies before ETF inception |
| Specification search | Allocation table frozen before this study; 54 configurations counted | The table was designed on 2011–2026, so 2007–2026 is partly in sample; only 2000–2007 is fully out of sample |
| Few independent assets | Ten more equity assets of different styles and regions | They behave like 1.2 series |
| Costs | One-way costs per sleeve, doubled and ×5 | 14.0 bps a year at ×5: immaterial |

## Implications

* **For an allocator:** hold the diversified mix; it improved risk-adjusted return in the period not
  used to design it and rebalances with low turnover (0.32 a year). The timing layer earned its
  gain in one crisis; adopting it is a bet that such episodes recur with the same regime signature.
* **For research:** build regimes from real-time vintages, separate timing from average allocation,
  and judge timing in a period not used to design it. Stronger evidence needs independent episodes,
  for example other countries.
<!-- TOP:END -->

## Layout

```
mo/            data (Yahoo with distributions), macro (real-time IP vintages, unrevised CPI), regime,
               backtest (proxies, drift-aware turnover), strategies, stats (Newey-West, Wald), boot (stationary bootstrap)
scripts/       s0_verify ... s9_mechanism: one script per step; make_papers fills paper/template.tex;
               report_readme writes the top of this README; fetch_data
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
