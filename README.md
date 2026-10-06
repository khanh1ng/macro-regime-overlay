# macro-regime-overlay

**A real-time macro regime overlay that kept a concentrated growth fund's return and cut its 2008
drawdown from −47.6% to −18.2%.**

The overlay holds less of the JPMorgan Large Cap Growth Fund and more gold, Treasuries, high yield and
dollars when growth slows and inflation rises. Every regime uses only data published at the time
(766 vintages of industrial production, consumer prices that are never revised), and the
specification was frozen before any backtest.

*Original backtest spring 2026; re-tested with real-time data and a frozen specification, October
2026.*

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

## Scope

Regime timing is strongest after 2007. In 2000–2007 the static allocation still helps, but timing
lowers the Sharpe ratio (−0.18, interval [−0.32, +0.05]), because the growth fund's response to
Stagflation reversed around 2007. The robust recommendation is the diversified allocation; regime
timing paid off after 2007, and adopting it is a bet that the post-2007 relation continues. Full results, including predictability tests and a
predictive-regression alternative, are in the paper.

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
