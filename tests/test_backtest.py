"""Checks of the backtest engine. Writes results/test_backtest.json."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mo.config import RESULTS  # noqa: E402
from mo.backtest import returns_panel, run, ASSETS, K_TABLE, table_weights  # noqa: E402
from mo.strategies import build, vol_target, trend  # noqa: E402

rets = returns_panel()
labels = pd.read_csv(RESULTS / "s1_regimes.csv", index_col=0)
labels.index = pd.PeriodIndex(labels.index, freq="M")
res = {}

# 1. A 100% fund strategy returns exactly the fund's returns, with no cost after the first month.
dec = pd.period_range("2007-03", "2026-08", freq="M")
w = pd.DataFrame({"FUND": 1.0}, index=dec).reindex(columns=ASSETS).fillna(0.0)
bt = run(w, rets, "2007-04", "2026-09")
res["fund_equals_fund"] = bool(np.allclose(bt.net.values, rets.loc["2007-04":"2026-09", "FUND"].values))

# 2. Hand computation for two months of a two-asset mix with drift.
w2 = pd.DataFrame({"FUND": [0.5, 0.5], "SHY": [0.5, 0.5]}, index=pd.period_range("2010-01", "2010-02", freq="M"))
w2 = w2.reindex(columns=ASSETS).fillna(0.0)
bt2 = run(w2, rets, "2010-02", "2010-03")
rf_, rs_ = rets.loc["2010-02", "FUND"], rets.loc["2010-02", "SHY"]
drift_f = 0.5 * (1 + rf_) / (0.5 * (1 + rf_) + 0.5 * (1 + rs_))
turn2 = 2 * abs(0.5 - drift_f)
cost2 = abs(0.5 - drift_f) * (0 + 1) / 1e4
res["drift_turnover_hand"] = bool(np.isclose(bt2.turnover.iloc[1], turn2) and np.isclose(bt2.cost.iloc[1], cost2))

# 3. K weights follow the table for every month.
wK = table_weights(labels["rt_raw"].reindex(dec), K_TABLE)
ok = all(np.isclose(wK.loc[t, a], K_TABLE[labels["rt_raw"][t]].get(a, 0.0)) for t in dec for a in ASSETS)
res["k_weights_follow_table"] = bool(ok)
res["weights_sum_to_one"] = bool(np.allclose(wK.sum(axis=1), 1.0))

# 4. Look-ahead: weights at decision month t are unchanged when fund returns after t are deleted.
fund = rets["FUND"]
cuts = pd.period_range("2001-06", "2026-06", freq="M")[::17]
same = 0
for t in cuts:
    f_t = fund[fund.index <= t]
    same += int(np.isclose(vol_target(f_t, [t]).loc[t, "FUND"], vol_target(fund, [t]).loc[t, "FUND"])
                and trend(f_t, [t]).loc[t, "FUND"] == trend(fund, [t]).loc[t, "FUND"])
res["baseline_weights_truncation"] = f"{same}/{len(cuts)}"

# Positive control through the same truncation mechanism: a volatility rule that uses month t+1
# must give a different weight when data after t are deleted.
def vol_peek(fr, idx):
    return vol_target(fr.shift(-1).fillna(0.0), idx)
diff = sum(int(not np.isclose(vol_peek(fund[fund.index <= t], [t]).loc[t, "FUND"],
                              vol_peek(fund, [t]).loc[t, "FUND"])) for t in cuts)
# Weights capped at 1 in calm periods cannot reveal the leak, so count only cuts where the cap does not bind.
binding = sum(int(vol_peek(fund, [t]).loc[t, "FUND"] < 1) for t in cuts)
res["positive_control_flagged"] = f"{diff} of {len(cuts)} flagged; {binding} cuts where the cap does not bind"

# 5. Returns of month m use weights decided at m-1: shifting the label by one month must change K.
res_a, _ = build(labels["rt_raw"], rets, "2007-04", "2026-09")
res_b, _ = build(labels["rt_raw"].shift(1), rets, "2007-04", "2026-09")
res["label_shift_changes_K"] = bool(not np.allclose(res_a["K"].net, res_b["K"].net))

res["pass"] = (res["fund_equals_fund"] and res["drift_turnover_hand"] and res["k_weights_follow_table"]
               and res["weights_sum_to_one"] and res["baseline_weights_truncation"] == f"{len(cuts)}/{len(cuts)}"
               and diff >= binding and binding > 0 and res["label_shift_changes_K"])
(RESULTS / "test_backtest.json").write_text(json.dumps(res, indent=1))
print(json.dumps(res, indent=1))
assert res["pass"]
