# macro-regime-overlay

**Can a growth–inflation regime overlay protect a concentrated growth fund?**

*Original backtest spring 2026; re-tested with real-time data and a frozen specification, October
2026.*

**Why it is worth testing.** Many investors hold one concentrated growth fund, here the JPMorgan
Large Cap Growth Fund, whose returns are excellent in most years and whose drawdowns are deep when
growth stocks fall together (−47.6% in 2008). Sorting months into four regimes by the direction of
growth and inflation, and holding the assets that did best in each, is common practice: equities
should do well when growth rises and inflation falls, bonds when inflation falls, gold and
commodities when inflation rises. Such backtests usually fail for three reasons: macro data are
revised after the fact, predictability from macro variables is fragile, and allocation tables are
chosen after many trials. This project tests the overlay with all three removed.

**What the research concludes.**

* **The overlay works where it matters most.** In 2007–2026 it keeps the fund's return (14.3% vs
  14.1% a year), raises the Sharpe ratio from 0.75 to 1.07, and cuts the worst drawdown from
  −47.6% to −18.2%; the Sharpe gain is significant (+0.32, 90% interval [+0.06, +0.55]). This period overlaps the
  2011–2026 data the allocation table was designed on, so it is partly in sample.
* **Diversification is the robust part.** Holding the overlay's average weights, without any timing,
  raises the Sharpe ratio and makes the drawdown shallower in both periods tested, including
  2000–2007, the only period fully out of sample.
* **Regime timing depends on the era.** It adds +0.22 Sharpe after 2007, but lowers it by −0.18 in
  2000–2007, because the growth fund's response to Stagflation changed sign around 2007.
* **Real-time data matter.** A typical backtest's regimes agree with what was knowable in only
  67.3% of months, and revised data flatter the timing result.
* **Regimes are not a forecasting signal.** None of 36 tests of next-month returns survives a
  multiple-testing correction, so the regimes are not a reliable return forecast.

**Is it usable, and what would it need?** Yes, the diversified allocation: about 60% fund with gold,
short Treasuries, high yield and dollars, built from ETFs and rebalanced with low turnover. The
timing layer is a bet that the post-2007 relation continues; it is cheap to run forward because the
classifier needs one monthly update. Strengthening the timing evidence needs more independent
episodes (the eleven equity assets tested behave like 1.2 independent series), for example other
countries, and a mechanism for the 2007 change, which the stock–bond correlation does not explain.

**Paper:** [`paper/paper.pdf`](paper/paper.pdf) (15 pages).
**Every step, with what was fixed before it ran:** [`docs/RESEARCH_LOG.md`](docs/RESEARCH_LOG.md).

## Highlights

**Same return, a third less volatility, a drawdown less than half as deep** (2007-04 to 2026-09,
after costs):

| Strategy | CAGR | Volatility | Sharpe | Max drawdown | Worst 12 months |
|---|---:|---:|---:|---:|---:|
| Regime overlay (K) | 14.3% | 11.9% | **1.07** | **−18.2%** | −17.6% |
| Fund alone | 14.1% | 17.7% | 0.75 | −47.6% | −39.8% |
| 60/40 fund/IEF | 10.0% | 10.8% | 0.80 | −27.0% | −22.3% |
| 10-month trend | 11.4% | 13.7% | 0.76 | −19.7% | −18.4% |

* **The gain is statistically significant.** Sharpe of K minus the fund: +0.32, 90% bootstrap
  interval [+0.06, +0.55]; drawdown 29.4 points shallower [+7.3, +37.0]. Over 2000–2026: +0.23
  [+0.04, +0.43].
* **The diversified allocation helps in every period tested.** Holding the overlay's average weights
  (about 60% fund with gold, short Treasuries, high yield and dollars) raises the Sharpe ratio by
  +0.09 in 2007–2026 and +0.22 in 2000–2007, and makes the drawdown shallower in both (+16.5 and
  +18.7 points).
* **Regime timing adds on top of that after 2007:** +0.22 Sharpe [+0.03, +0.41], and the same
  sign for all six hold-out growth funds and indices.
* **It beats a 10-month trend rule after 2007:** +0.31 Sharpe [+0.04, +0.60].

## What the research adds

* **Real-time regimes.** Built from the industrial-production data actually published each month.
  Revisions matter: real-time and revised regimes agree in only 81.8% of months, and the usual
  backtest construction agrees with what was knowable in 67.3%.
* **Verified data.** Fund returns match its annual report to the SEC to within 0.07 percentage
  points a year.
* **Static allocation separated from timing**, so each part of the gain is measured on its own.
* **Tested out of sample** (2000–2007, a period not used in the design) and on ten other equity
  funds and indices of different styles and regions.

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
