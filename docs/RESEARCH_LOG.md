# Research log

Every step of the study, in order: what was fixed before it ran, what it found, and the check it had
to pass before the next step started. Steps 0–7 produced two papers; Step 9 merged them into
`paper/paper.tex`; Steps 10–13 answered the obvious objections and updated the paper.

Requirements (fixed before any analysis):

| # | Requirement |
|---|---|
| M1 | Fund total returns reconcile with the fund's own annual report within 0.5 pp a year |
| M2 | Regimes use only data known at the time (real-time IP vintages, unrevised CPI) |
| M3 | Every design choice fixed before the test period is seen, or taken from published work |
| M4 | Compared with static mixes of the same average weights, 60/40, volatility targeting, a 10-month trend filter, and a constant 10% gold sleeve |
| M5 | Benefit split into static allocation, timing, and asset choice |
| M6 | Block-bootstrap intervals for Sharpe and drawdown differences; deflated Sharpe with every trial counted |
| M7 | The frozen rule applied unchanged to other funds and indices |
| M8 | Trading costs, turnover and rebalancing frequency |
| M9 | Every number interpreted where it appears; motivation; real references |
| M10 | Byte-for-byte reproducible, with regression tests |

---

## Step 0: data (2026-10-01)

**What was done.**
- Daily close, adjusted close and every distribution for 16 tickers from Yahoo, saved in `data/raw/`:
  - JLGMX and SEEGX (Class I of the same fund, from 1992);
  - IWF, QQQ, SPY;
  - hold-out funds FBGRX, TRBCX, AGTHX;
  - sleeves GLD, SHY, IEF, TLT, TIP, HYG, UUP, DBC.
- Real-time industrial production vintages, 1962-11 to 2026-08, from the Philadelphia Fed Real-Time Data Set. ALFRED was not reachable from this machine.
- CPI not seasonally adjusted (CPIAUCNS), which is never revised. Its year-on-year change is therefore real-time once published.
- Also from FRED: CPIAUCSL, TB3MS, and the current INDPRO.
- `scripts/s0_verify.py` writes `results/s0_verify.json`.

**Evaluation.**

| Req. | Check | Result |
|---|---|---|
| M1 | JLGMX 1/5/10-year returns to 2026-06-30 vs N-CSR annual report | 15.53 / 12.60 / 20.29 vs 15.56 / 12.66 / 20.30, max gap 0.06 pp. **PASS** |
| M1 | SEEGX (Class I) vs report | 15.23 / 12.31 / 19.98 vs 15.26 / 12.38 / 19.99. **PASS** |
| M1 | IWF vs Russell 1000 Growth (fee 0.19 pp) | Gaps −0.30 / −0.20 / −0.22 pp. **PASS** |
| M1 | Adjusted close equals raw close plus reinvested distributions | ≥99.5% of days within 1 bp for all 16 tickers. **PASS** |
| M1 | R6 minus Class I, every year 2011–2025 | Between 0.20 and 0.38 pp, matching the fee gap; largest monthly gap 0.07 pp. **PASS** |
| M1 | Fund drop above 4% on a day IWF moved less than 1.5% (sign of a missing distribution) | None in any fund. **PASS** |
| M2 | Each IP vintage ends one month before its date | Yes, except 2025-10 and 2025-11, which end at 2025-08 because the 2025 shutdown delayed the release. This is a real delay, and the classifier uses the latest published month. **PASS** |
| M2 | Last IP vintage vs current FRED INDPRO | Max relative gap 0.33%. **PASS** |
| M2 | CPI NSA vs SA year-on-year | Correlation 0.9992. **PASS** |
| M10 | Two runs of `s0_verify.py` | Identical MD5. **PASS** |

**Findings that change the old write-up.** Recomputed on verified data:

| Claim | Old | Verified |
|---|---|---|
| JLGMX 2018 Q4 | −29.07% | −18.52% |
| JLGMX 2020 Feb–Mar | −14.88% | −14.88% |
| JLGMX 2022 Jan–Oct | −12.56% | −23.37% |
| Max drawdown | −29.07% (2018) | −31.82% daily (2020-03-23); −27.81% month-end (2022-09) |

The old 2018 and 2022 numbers cannot be reproduced. The cause cannot be determined now; likely suspects are how Yahoo handled distributions at the time and the old monthly-interval download. Every later result uses the verified series.

**Decision for later steps.** SEEGX is the same portfolio from 1992, with returns about 0.3 pp a year lower than R6. Using it before JLGMX's inception (2010-11) extends the fund history. With every sleeve available (HYG from 2007-04), the joint sample starts in 2007-04 and includes the 2008 crisis, which the old project did not cover. This is fixed in Step 3, before results are seen.

**Open limitation.** Yahoo is a single vendor. The raw files are frozen in `data/raw/` so results reproduce, but a second vendor would be better.

**Step 0: PASS. Moving to Step 1.**

---

## Step 1: real-time classifier (2026-10-01)

**What was done.** `mo/regime.py` and `scripts/s1_regimes.py`, writing `results/s1_regimes.{csv,json}`; `tests/test_s1_lookahead.py`.
- The decision is taken at the end of month t, for returns in month t+1.
- IP comes from the vintage dated t, which ends at t−1. CPI (NSA) is used through t−1.
- Direction = change over 6 months in year-on-year growth.
- Variants: raw; 3-month smoothing; 3-month persistence filter; extra lags of 1–3 months; and the usual backtest version (today's revised IP, SA CPI, fixed lag).

**Criteria set before running.**
- (a) The truncation test is identical at every cut, and the positive control is flagged at every cut.
- (b) Report what revisions change.
- (c) Report switches and spell lengths for every variant.
- (d) Deterministic.

**Evaluation.**

| Req. | Check | Result |
|---|---|---|
| M2 | 60 random cuts 1992–2026: labels with all later data deleted vs full run | 60/60 identical (raw), 60/60 identical (smoothed + persistent). **PASS** |
| M2 | Positive control (CPI for month t leaks in) | Signal changed at 60/60 cuts; label test flagged 60/60. **PASS** |
| M2 | Real-time vs revised labels, same rules, same one-month lag | Agree in 81.8% of 440 months. Growth signs agree 83.6% (corr 0.957); inflation 97.7% (corr 0.997). Revisions to IP drive the difference. **Reported** |
| M2 | Real-time raw vs the old project's construction (revised, lag 2) | Agree in 67.3% of months: one label in three in a backtest of that kind could not have been known. **Reported** |
| M3 | Spell lengths | Raw: 122 switches in 440 months, mean spell 3.6 months. Smoothed + persistent: 58 switches, mean 7.4 months, at the cost of reacting later (2008: Stagflation held until 2009-01, against 2008-11 for raw). **Reported; the variant is chosen in Step 3 before any return is used** |
| M10 | Two runs | Identical MD5 for json and csv. **PASS** |

**What this means for later steps.**
- Revisions matter for growth, not inflation, so the real-time IP vintages are essential.
- The raw classifier changes regime every 3–4 months, which will cost turnover. Step 6 must charge for it.

**Step 1: PASS. Moving to Step 2.**

---

## Step 2: does the real-time regime predict next month's return? (2026-10-01)

**What was done.** `scripts/s2_predict.py` writes `results/s2_predict.json`; `mo/stats.py` is OLS with Newey–West errors in numpy, because statsmodels is broken on this machine (x86 build on arm64).
- For 12 assets and 3 classifiers: next month's excess return on regime dummies, with Newey–West (6 lags) and a Wald test that all four regime means are equal.
- Contrast: Stagflation minus the average of the other regimes.
- Periods: full sample, before 2007-03, and from 2007-04.

**Criteria set before running (from the plan).**
- Report HAC tests per asset and a Bonferroni count.
- Compare real-time with revised labels.
- Require at least 20 months per regime.

**Code checks.**
- Dummy coefficients equal the group means exactly.
- With 0 lags the errors equal White's.
- Two runs give an identical MD5.

**Evaluation.**

| Req. | Check | Result |
|---|---|---|
| M6 | Full sample, real-time raw: assets with p<0.05 / below Bonferroni (0.05/36) | 1 of 12 (HYG, p=0.029) / 0 of 12 |
| M6 | Same, smoothed + persistent | 0 / 0 |
| M6 | Same, revised lag 2 (the old construction) | 0 / 0 |
| M6 | Fund (SEEGX), Stagflation minus others, full sample | −6.8%/yr, t=−0.89; smallest detectable effect at 80% power is 21%/yr |
| M3 | Fund, before 2007-03 | Stagflation is the **best** regime: +15.8%/yr excess (n=32); contrast +14.0%/yr (t≈+1.4) |
| M3 | Fund, from 2007-04 | Stagflation among the worst: −1.6%/yr (n=58); contrast −20.7%/yr, t=−2.19; Wald p=0.004. Equity assets SPY, IWF, QQQ also p<0.05 |
| M3 | Fund, from 2007-04, smoothed + persistent classifier | Wald p=0.53: the result depends on the classifier |
| — | Regime sizes | Every regime has at least 32 months in every period. **PASS** |

**What this means.**
1. **The necessary condition holds only in part of the sample.** Over 1992–2026, regime labels known in real time do not predict next month's return of any asset at conventional levels after correcting for 36 tests.
2. **The equity–Stagflation relation changed sign around 2007.** The old project's evaluation window (2011–2026) lies entirely in the period where cutting equity in Stagflation looked right.
3. **The tests have little power.** They cannot detect effects smaller than about 20%/yr, so "no evidence" is not "no effect". The paper must say both.
4. **TLT does well in real-time Stagflation** (+12.7%/yr, t=2.0), because 2008 is labelled Stagflation in real time. This contradicts the old project's "no TLT in Stagflation" rule, which came from 2022 alone.

**Consequence for Step 3.** I have now seen regime-conditional returns, so any new rule designed from them is contaminated. Step 3 therefore tests only:
- (a) the old Strategy K table, unchanged, since it was frozen before this work;
- (b) a generic rule fixed now, independent of these results: equity cut by the same amount in every non-Goldilocks regime;
- (c) the baselines in M4.

The period before 2007 is the only genuine out-of-sample period for the K table. Long-history proxies for the sleeves must be added (Step 3a) to test it there.

**Step 2: PASS (procedure). The substantive result is negative for regime timing and is reported as such.**

---

## Step 3: specification, frozen before any backtest is run (2026-10-01)

Written before `s3_backtest.py` exists. Nothing below may change after results are seen. If a bug forces a change, it is logged here with the reason.

**Returns.**
- Monthly total returns.
- The fund is JLGMX from 2010-12; before that, SEEGX (same portfolio, Class I, about 0.26 pp/yr lower).
- Excess returns are over the 3-month T-bill (TB3MS/12).

**Proxies before ETF inception** (chosen on the 2007-05 to 2026-09 overlap by lower tracking error; checked in `s3_proxies`):

| ETF | Proxy | Version | Corr. | TE |
|---|---|---|---|---|
| HYG | VWEHX | raw | 0.906 | 4.5% |
| SHY | VFISX | raw | 0.969 | 0.5% |
| IEF | VFITX | raw | 0.981 | 2.3% |
| TLT | VUSTX | raw | 0.991 | 2.4% |
| GLD | GC=F | raw | 0.992 | 2.3% |
| DBC | ^SPGSCI | + T-bill | 0.956 | 7.3% |
| UUP | DX-Y.NYB | + T-bill | 0.994 | 0.9% |

Each ETF's own return is used from its first full month; the proxy is used only before that.

**Timing.**
- Weights decided at the end of month t, from the regime known at t, are held through month t+1.
- Rebalanced to target every month.
- Cost: one-way cost × |change in weight|, using the old project's figures: fund 0, HYG 2, GLD 1, DBC 5, SHY 1, UUP 3, IEF 1, TLT 1 bps. Doubled and ×5 in Step 6.

**Classifier.** Real-time raw (`rt_raw`); this is the construction K was built on. Sensitivity: `rt_smooth3_persist3`, and `revised_lag2` (the old construction, which is not real-time).

**Strategies tested.**
- **K**: the old table, unchanged.

  | Regime | Fund | HYG | GLD | DBC | SHY | UUP |
  |---|---|---|---|---|---|---|
  | Goldilocks | 90 | 10 | | | | |
  | Reflation | 55 | 10 | 30 | 5 | | |
  | Disinflation | 80 | 10 | 10 | | | |
  | Stagflation | 25 | | 25 | | 30 | 20 |

- **G** (generic de-risking, fixed now): Goldilocks 100% fund; any other regime 70% fund, 15% SHY, 15% GLD.

**Baselines (M4).**
1. 100% fund.
2. **S-K**: static mix at K's average weights over the same period.
3. 60/40 fund/IEF.
4. Volatility target: fund weight = min(1, 15% / trailing 12-month realised vol of monthly fund returns × √12), rest in SHY.
5. 10-month trend: fund if the month-end price is above its 10-month average, else SHY.
6. 90% fund / 10% GLD.

**Periods.**
- **P1**, main: 2007-04 to 2026-09, ETFs except where noted.
- **P0**, out of sample for K's design: 2000-10 to 2007-03, proxies.
- **Pold**: 2011-02 to 2026-05, the old project's window, to reconcile the old claim.
- **Pall**: 2000-10 to 2026-09.

**Metrics.**
- CAGR, volatility, Sharpe (mean excess × 12 / (sd × √12)), maximum drawdown on month-end wealth, worst 12 months, turnover per year, cost drag.

**Attribution (M5).** K minus fund = (S-K minus fund) [static allocation] + (K minus S-K) [timing].

**Statistics (M6).**
- Stationary block bootstrap, 12-month mean blocks, 5,000 draws, seed 0, for:
  - Sharpe(K) − Sharpe(fund) and Sharpe(K) − Sharpe(S-K);
  - MaxDD(K) − MaxDD(fund) and MaxDD(K) − MaxDD(S-K).
- Deflated Sharpe for K, with N = the number of configurations in the old notebook plus every configuration run here.

**Hold-out (M7).** K and S-K applied unchanged with the fund replaced by FBGRX, TRBCX, AGTHX, QQQ, IWF, SPY.

**Success criterion for "regime timing adds value".** In P1 and P0 separately, the 90% bootstrap interval of Sharpe(K) − Sharpe(S-K) lies above 0, and the hold-outs show the same sign in at least 5 of 6.

---

## Step 3: backtest of the frozen specification (2026-10-01)

**What was done.**
- `mo/backtest.py`, `mo/strategies.py` and `scripts/s3_backtest.py` write `results/s3_backtest.json` and `s3_monthly.csv`.
- `tests/test_backtest.py` writes `results/test_backtest.json`.
- No part of the specification was changed after results were seen.

**Engine checks.**

| Check | Result |
|---|---|
| 100% fund strategy reproduces fund returns exactly | PASS |
| Drift-aware turnover and cost match a hand computation | PASS |
| K weights equal the table every month; weights sum to 1 | PASS |
| Vol-target and trend weights unchanged when later returns are deleted | 18/18. PASS |
| Positive control (vol rule peeking at t+1) | Flagged at 8 of 18 cuts, including all 7 where the 100% cap does not bind. PASS |
| Shifting labels by one month changes K | PASS |
| Proxy check on the overlap reproduces the frozen choices | PASS |
| Two runs | Identical MD5. PASS |

**Headline (real-time raw classifier).**

| | P1 2007-04 to 2026-09 | P0 2000-10 to 2007-03 (out of sample for K) |
|---|---|---|
| Sharpe: K / S-K / Fund / Trend | 1.07 / 0.84 / 0.75 / 0.75 | −0.36 / −0.18 / −0.40 / **0.73** |
| Max DD: K / S-K / Fund / Trend | −18.2 / −31.0 / −47.6 / −19.7% | −47.6 / −38.1 / −56.8 / −7.4% |
| CAGR: K / Fund | 14.3 / 14.1% | −2.2 / −5.2% |

**Reconciling the old claim (Pold, 2011-02 to 2026-05).**
- Fund CAGR is 16.81%, matching the old notebook exactly.
- Fund volatility is 16.65%, against 20.73% in the old notebook. The old monthly series had the same compound return but extra volatility, which fits distributions recorded in the wrong month.
- With verified data and the real-time classifier:
  - K: CAGR 14.69%, Sharpe 1.12, max DD −17.6%;
  - Fund: CAGR 16.81%, Sharpe 0.93, max DD −27.8%.
- The old claim that K **raised** the return (16.49→16.81%) does not hold: K gives up 2.1 pp a year.

**Step 3: PASS (procedure).**

---

## Step 4: attribution, K minus fund = static allocation + timing (2026-10-01)

Average K weights in P1: fund 0.61, GLD 0.18, HYG 0.075, SHY 0.074, UUP 0.05, DBC 0.014. These define S-K.

| Classifier, period | Sharpe: total = static + timing | Max DD (pp): total = static + timing | Return (pp/yr): static, timing |
|---|---|---|---|
| rt_raw, P1 | +0.33 = +0.10 + **+0.23** | +29.4 = +16.5 + **+12.9** | −3.2, +2.6 |
| rt_raw, P0 | +0.04 = +0.22 + **−0.18** | +9.2 = +18.7 + **−9.5** | +4.7, −2.3 |
| rt_raw, Pold | +0.19 = +0.06 + +0.14 | +10.2 = +8.1 + +2.2 | −4.3, +1.7 |
| rt_raw, Pall | +0.24 = +0.14 + +0.10 | +9.2 = +20.0 + −10.8 | −1.1, +1.3 |
| smooth+persist, P1 | +0.29 = +0.09 + +0.20 | +34.3 = +15.2 + +19.1 | −2.9, +1.6 |
| smooth+persist, P0 | +0.22 = +0.24 + −0.01 | +12.3 = +19.3 + −7.0 | +4.9, −0.4 |
| revised lag 2, P1 | +0.41 = +0.10 + +0.31 | +30.6 = +16.5 + +14.1 | −3.2, +3.2 |

| Req. | Check | Result |
|---|---|---|
| M5 | Decomposition adds up exactly (by construction) and is reported for every period and classifier | **PASS** |
| M4 | All six baselines in every period | **PASS** |

**What this means.**
- In 2007–2026, timing is the larger part of K's gain. This is mostly 2008: real-time Stagflation runs through 2008-10, so K holds 25% fund during the crash.
- In 2000–2007, the only period out of sample for K's design, timing **hurts**: Sharpe −0.18 and max DD 9.5 pp worse than the static mix. The static part helps in both periods.
- The revised, not-real-time construction gives the best P1 result (timing +0.31 Sharpe). Using revised data flatters the backtest.
- A simple 10-month trend filter beats K in P0 by a wide margin and ties on drawdown in P1.

**Step 4: PASS (procedure). Significance comes in Step 5.**

---

## Bug fix logged during Step 5 (2026-10-01)

TB3MS ends at 2026-08, so the excess return for 2026-09 was missing and the Sharpe ratios in Step 5 came out as NaN. Fix: `macro.tbill_monthly` carries the last published rate forward to 2026-09.
- This is not a change to the specification.
- Steps 2, 3 and 5 were rerun.
- Step 2 numbers move in the second decimal (fund Stagflation contrast −6.81 → −6.89%/yr). Conclusions are unchanged.

---

## Step 5: statistics, deflated Sharpe, hold-outs (2026-10-01)

**What was done.** `scripts/s5_stats.py` writes `results/s5_stats.json`. Stationary bootstrap with 12-month mean blocks, 5,000 draws, seed 0.

| Req. | Check | Result |
|---|---|---|
| M6 | Timing, Sharpe(K) − Sharpe(S-K), P1 | +0.224, 90% CI [+0.026, +0.415], P(≤0)=0.03 |
| M6 | Timing, P0 | −0.176, 90% CI [−0.316, +0.051], P(≤0)=0.91 |
| M6 | Timing, Pall | +0.093, 90% CI [−0.070, +0.276] |
| M6 | Static, Sharpe(S-K) − Sharpe(fund) | P1 +0.092 [−0.014, +0.194]; P0 +0.216 [+0.107, +0.388]; Pall +0.136 [+0.050, +0.220] |
| M6 | Max DD, K − fund (pp, positive = shallower) | P1 +29.4 [7.3, 37.0]; P0 +9.2 [3.9, 15.6] |
| M6 | Max DD, K − S-K (timing) | P1 +12.9 [−1.0, 18.0]; P0 −9.5 [−14.6, −1.1] |
| M6 | K vs 10-month trend | P1 Sharpe +0.31 [0.04, 0.60]; P0 −1.09 [−2.25, 0.30]; Pall −0.03 [−0.45, 0.38] |
| M6 | Deflated Sharpe, N = 40 old + 14 here = 54 | K 1.00, S-K 0.99, Trend 0.97, Fund 0.97. Every configuration holds the same equity premium, so the deflated Sharpe only says the Sharpe ratios are above zero. It cannot separate timing from holding equity. The bootstrap of differences answers the timing question. |
| M7 | Hold-outs (FBGRX, TRBCX, AGTHX, QQQ, IWF, SPY), timing Sharpe in P1 | Positive in 6/6 (+0.17 to +0.26); 90% CI above 0 in 4/6 |
| M7 | Hold-outs, P0 | Negative in 6/6 (−0.14 to −0.19); max DD worse by 9–11 pp in 6/6 |

**Frozen success criterion:** both periods' timing CI above 0 **and** at least 5/6 hold-outs with the same sign in both periods. **FAIL.**

The timing effect is real and consistent across funds within a period, but its sign depends on the period. Together with Step 2, this points to a relation between regimes and equity that changed, not to fund-specific noise.

**Step 5: PASS (procedure). Substantive result: the frozen criterion for "regime timing adds value" is not met.**

---

## Step 6: costs and turnover, plus exploratory timing by year (2026-10-01)

**What was done.** `scripts/s6_costs.py` writes `results/s6_costs.json`.

| Req. | Check | Result |
|---|---|---|
| M8 | K turnover / cost drag at base costs | 2.94 per year / 2.8 bps per year (P1); 4.03 / 4.0 bps (P0) |
| M8 | Sharpe of K at costs ×1 / ×2 / ×5 | P1 1.069 / 1.066 / 1.059; P0 −0.355 / −0.359 / −0.369. ETF costs do not decide anything. |
| M8 | Implementation limit not captured by costs | Moving 30–75% of the portfolio in and out of a mutual fund several times a year runs into funds' frequent-trading policies, and in a taxable account it realises gains. Noted as a limitation. |

**Exploratory, not pre-specified.**
- K minus static-mix return by calendar year (pp): 2008 **+17.2**, 2020 +12.4, 2019 +9.6, 2025 +8.2, 2023 +5.6; 2000 −3.8, 2001 −5.1, 2002 −6.0, 2003 −2.8, 2014 −7.0.
- P1 with 2007-10 to 2009-03 removed: Sharpe K 1.22, S-K 1.10, fund 1.03. Timing shrinks from +0.22 to +0.12.

The gain in P1 is concentrated in a few crises.

**M10 determinism.** Two full runs of Steps 3, 5 and 6 give identical MD5 for every output. **PASS**

**Step 6: PASS.**

---

## Note on Step 2 numbers after the T-bill fix

After the 2026-09 T-bill fix, Step 2 includes one more month.

| Number | Before | After |
|---|---|---|
| HYG Wald p (full sample, raw) | 0.029 | 0.021 |
| Fund Wald p | 0.488 | 0.501 |
| Fund Stagflation contrast | −6.81%/yr | −6.89%/yr |
| Post-2007 contrast | −20.73%/yr | −20.88%/yr |

All conclusions are unchanged. The papers use the regenerated values.

---

## Step 7: papers (2026-10-01)

**What was done.**
- `scripts/make_papers.py` fills `paper/pA_template.tex` and `paper/pB_template.tex`, giving `paperA.tex` (7 pages) and `paperB.tex` (10 pages).
- Every number, table and figure comes from `results/`. References are inlined only when cited, and the build stops on an unknown key.
- `run_all.py` rebuilds everything. Two full runs give identical MD5 for both papers and every result file.

**Corrections caught while proofreading the rendered PDFs, before release.**
1. "Stagflation months before 2007 were mostly 1999–2000 and 2005" was wrong: they are spread over 14 years. Replaced by generated counts.
2. "The 2022 shock is in Stagflation" was wrong: only 3 months of 2022 are labelled Stagflation in real time, because IP growth was still rising from March to August. Now stated with the reason, which was checked against the signals.
3. "Long Treasuries do well in Stagflation because of 2008" was wrong: without 2008 the figure is still +11.6%/yr; 2011, 2016 and 2020 matter more. Rewritten with generated per-year numbers.
4. "K's 2000–2007 loss comes from cutting the fund in Stagflation" was wrong. The by-regime attribution (exploratory, added to `s6_costs.py`) shows the loss came from holding 80–90% in Goldilocks and Disinflation months, in which the fund fell. The P1 gain has the same source. Paper B's explanation, abstract and recommendation were rewritten.
5. The 2000–2007 timing figure was −0.17 in one place and −0.18 in another, because Sharpe ratios were rounded before subtracting. The attribution now uses unrounded Sharpe ratios.
6. Hand-typed numbers (0.07 pp, 0.3 pp fee, "four points", 0.19% fee, "two thirds") were replaced with generated values.
7. A limitation was added: the success criterion was written after Step 2 had shown the sign change.

**Evaluation against the paper requirements.**

| # | Requirement | Paper A | Paper B |
|---|---|---|---|
| P1 | Abstract states question, method, main numbers | PASS | PASS |
| P2 | Motivation and related work in the introduction | PASS (Croushore–Stark, Orphanides, Welch–Goyal, Ang–Bekaert, Ilmanen) | PASS (Faber, Moskowitz et al., Moreira–Muir, Harvey et al., Bailey–López de Prado) |
| P3 | Every design choice explained | PASS (timing, signals, variants, NSA CPI) | PASS (proxies, baselines, attribution, criterion) |
| P4 | Every table followed by its reading | PASS | PASS |
| P5 | No hand-typed result numbers | PASS after correction 6 | PASS |
| P6 | Limitations, including what the design cannot show | PASS | PASS (including the criterion-timing caveat) |
| P7 | Only real, cited references | PASS (7) | PASS (8); publication details should still be checked before submission |
| P8 | Under 15 pages, compiles with 0 errors, 0 overfull boxes, 0 undefined references | PASS (7 pages) | PASS (10 pages) |
| P9 | Each paper reads on its own | PASS | PASS |
| M9 | Every number interpreted | PASS | PASS |
| M10 | Reproducible | PASS | PASS |

**Step 7: PASS.**

---

## Step 9: single standalone paper (2026-10-01)

**Goal.** One self-contained paper of at most 20 pages, reviewed against the objections an experienced quant researcher would raise.

**What was done.**
- `paper/template.tex` → `paper/paper.tex`, 14 pages. It merges Papers A and B into one.
- The overlay's origin is stated as the author's earlier backtest on 2011–2026 data (about 40 configurations tried).
- Added a "main results at a glance" table and a "why verification matters" subsection that uses the earlier vendor-data backtest.
- The proxy table moved to an appendix.

**Reviewer-style fixes.**
1. The abstract claimed every return series was checked against the annual report. Only the fund (and IWF against its index) has an external check, so the claim was narrowed.
2. S-K uses each period's average weights, which is hindsight. It is now described as an attribution benchmark, not an investable strategy. The fund weight is reported in both periods (61% and 64%) to show that a static mix fixed in advance would have been close.

**Checks.**
- Compiles with 0 errors, 0 overfull boxes and 0 undefined references.
- Two full `run_all.py` runs give identical MD5.

**Step 9: PASS.**

---

## Step 10: how independent are the hold-outs? (specification written before running, 2026-10-01)

**Reason.** A reviewer will note that the six hold-out funds are all U.S. growth or broad U.S. equity, highly correlated with the fund, so "6/6" may be close to one observation.

**Plan.**
1. Correlation of monthly returns, 2000-10 to 2026-09, among the fund, the six hold-outs, and four new assets of different style or region: VIVAX (U.S. large value), NAESX (U.S. small cap), VGTSX (international), VEIEX (emerging markets). All are index mutual funds with history before 2000.
2. Correlation of the *timing series* (monthly K minus S-K) across all eleven. Effective number of independent series from the eigenvalues: N_eff = (Σλ)² / Σλ².
3. K and S-K on the four new assets, with rules unchanged, for P1 and P0, with bootstrap timing intervals.

**Reading fixed in advance.**
- If at least 3 of 4 new assets show the pattern "timing positive in P1, negative in P0", the explanation that the period, not the fund, drives the result is strengthened.
- If 2 of 4 or fewer, the timing result is specific to U.S. growth equity, and the paper must say so.

**Step 10 results.**

| Check | Result |
|---|---|
| Return correlation with the fund: 6 original hold-outs | 0.92–0.97 |
| Return correlation with the fund: 4 new assets | 0.70–0.80 |
| Timing-series correlation with the fund: original 6 | 0.94–0.98 (mean pairwise among the 7: 0.958) |
| Timing-series correlation with the fund: new 4 | 0.79–0.88 |
| Effective number of independent timing series | 1.08 for the original 7; 1.20 for all 11 |
| New assets with "P1 > 0, P0 < 0" | **4/4**. Timing Sharpe P1 +0.12 to +0.21; P0 −0.11 to −0.23; EM P0 interval [−0.32, −0.05] |

**Evaluation.**
- Per the fixed reading, the period explanation is strengthened: the pattern holds for value, small cap, international and EM.
- But the hold-outs add almost no independent evidence. The timing series of all eleven assets behave like 1.2 independent series, because the hedge legs are identical and equity markets fall together in the same crises.
- The paper must replace "6/6" with this.

**Step 10: PASS.**

---

## Steps 11–12: specification written before running (2026-10-01)

**Step 11: a principled alternative (continuous macro signals, predictive regression).**
- Forecast: the fund's excess return in month t+1 on [1, g_t, π_t], the real-time signals of Step 1, fitted on an expanding window with data through t only, from 1992. The first forecast needs 96 months.
- Forecast check:
  - out-of-sample R² against the expanding historical mean (Campbell–Thompson);
  - Clark–West MSFE-adjusted t-statistic (HAC, 6 lags);
  - over 2000-10 to 2007-03 and 2007-04 to 2026-09.
- Allocation M:
  - fund weight w_t = clip(0.60 + (μ̂_t − r̄_t)/(5 σ̂_t²), 0.25, 1.00), with σ̂_t² the expanding variance of the fund's excess return;
  - the rest in a fixed hedge mix: K's table averaged equally over the four regimes, which uses no data. Normalised, that is HYG 20%, GLD 43.3%, DBC 3.3%, SHY 20%, UUP 13.3%.
- Static comparison S-M: fund 0.60 and the same hedge mix every month. Timing = M − S-M; bootstrap as in Step 5.
- Reading: timing adds value only if the 90% interval of Sharpe(M) − Sharpe(S-M) is above 0 in both periods.

**Step 12: mechanism (real-time stock–bond correlation).**
- State at t: sign of the correlation of the fund's and VFITX's monthly returns over the previous 36 months, both known at t.
- Regression: fund excess return in t+1 on regime dummies × state, with HAC (6 lags).
- Reported:
  - Stagflation-minus-others contrast in each state, and their difference;
  - share of months with positive correlation before and after 2007;
  - the same within each subperiod, where cells have at least 12 Stagflation months.
- Supported only if the contrast is positive when the correlation is positive and negative when it is negative, with |t| > 2 for the difference, and the pattern holds within at least one subperiod. Otherwise "not supported / not identifiable".

**Step 11 results (continuous signals).**

| Check | 2007–2026 | 2000–2007 |
|---|---|---|
| Out-of-sample R² | −0.23% | −3.31% |
| Clark–West t | 0.80 | −0.53 |
| Sharpe M / S-M | 0.89 / 0.85 | −0.30 / −0.16 |
| Timing | +0.05, 90% CI [−0.09, +0.20] | −0.14, [−0.37, +0.01] |
| Months with the fund weight at a bound (0.25 or 1.00) | 44% | 56% |

**Evaluation.**
- The forecast has no out-of-sample skill, and timing does not add value in either period. **The criterion fails.**
- So the negative result is not specific to the hand-made table K: a standard predictive regression on the same real-time signals fails too.
- That the weights sit at a bound about half the time shows the forecasts are noisy relative to the γ=5 scaling. This was fixed in advance and not tuned.

**Step 12 results (stock–bond correlation, 36-month window, decisions from 1995-02).**
- Share of months with positive correlation: 47.6% before 2007, 29.1% after. The same shares among Stagflation months: 42.9% and 24.1%.

| Sample | Stagflation contrast, correlation positive | Correlation negative | Difference |
|---|---|---|---|
| Full | +2.2%/yr (t 0.16) | −12.0%/yr (t −1.25) | +14.2, t 0.86 |
| Before 2007 | +20.5 | +12.0 | t 0.36 |
| After 2007 | −10.9 | −24.4 | t 0.79 |

**Evaluation.**
- The full-sample direction matches the hypothesis, but the difference is far from significant.
- Within each subperiod both states have the *same* sign: positive before 2007, negative after.
- The sign change follows the calendar, not the correlation state. **Verdict: not supported.** The paper says the stock–bond correlation does not explain it.

**Steps 11–12: PASS (procedure). Both substantive results are negative and are reported as such.**

---

## Step 13: paper updated with Steps 10–12 (2026-10-02)

**Changes to `paper.tex` (15 pages).**
- Abstract, at-a-glance table, contributions and conclusion now report:
  - ten other equity assets, which behave like about 1.2 independent series;
  - the failed predictive-regression alternative;
  - the unsupported mechanism.
- New paragraphs: "Testing that mechanism" and "How independent is this evidence?".
- New subsection "A standard alternative: continuous signals", with Table `tab:model`.
- The hold-out table gains four rows (value, small cap, international, EM).
- The "Few episodes" limitation now cites N_eff.

**Checks.**
- 21/21 regression checks pass.
- Compiles with 0 errors and 0 overfull boxes.
- Two full runs give identical MD5.
- Refactor check: moving the bootstrap into `mo/boot.py` left `s5`, `s7` and `s8` outputs byte-identical.

**Step 13: PASS.**
