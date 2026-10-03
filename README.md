# macro-regime-overlay

**Can a growth–inflation regime overlay protect a concentrated growth fund? Real-time evidence,
1990–2026.**

A regime overlay holds less of a growth fund and more gold, Treasuries, high yield and dollars when
growth slows and inflation rises. An earlier backtest of such an overlay on the JPMorgan Large Cap
Growth Fund reported a shallower drawdown, a higher Sharpe ratio and a *higher* return. This project
re-tests it the way it should have been tested:

* returns checked against the fund's annual report to the SEC;
* regimes built from the industrial-production data actually published each month (766 vintages)
  and from consumer prices that are never revised;
* a specification frozen before any backtest;
* the benefit split into static allocation and timing;
* an earlier period the overlay was not designed on;
* ten other equity funds and indices.

**Paper:** [`paper/paper.pdf`](paper/paper.pdf) (15 pages).
**Every step, with what was fixed before it ran:** [`docs/RESEARCH_LOG.md`](docs/RESEARCH_LOG.md).

## Results

| Question | Answer |
|---|---|
| Do revisions change the regimes? | Real-time and revised regimes agree in 81.8% of months; the usual backtest construction agrees with what was knowable in 67.3% |
| Do real-time regimes forecast next month's returns? | 0 of 36 tests pass a Bonferroni correction |
| Is the growth fund's Stagflation effect stable? | +14.0% a year relative to other regimes before 2007, −20.9% after |
| Does the overlay's **timing** add value, 2007–2026? | Sharpe +0.22, 90% bootstrap interval [+0.03, +0.41] |
| … and in 2000–2007, out of sample? | Sharpe −0.18, interval [−0.32, +0.05]; the drawdown is deeper |
| Does its **average allocation** add value? | Sharpe +0.09 (2007–2026) and +0.22 (2000–2007) |
| Same pattern in ten other equity assets? | Yes, but their timing series behave like 1.2 independent series |
| Does a standard predictive regression do better? | No: out-of-sample R² −0.23% and −3.31% |
| Does the stock–bond correlation explain the sign change? | No: within each period both states have the same sign |

**Conclusion:** static diversification is robust. Regime timing is a bet on the post-2007 era, not a
backtested improvement.

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
