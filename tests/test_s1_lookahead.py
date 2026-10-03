"""Look-ahead test for the real-time classifier, with a positive control.

For a decision month t, the label must not change when every input published after t is deleted:
IP vintages dated after t, and CPI observations after t-1. The positive control lets CPI for month t
leak in; the test must then detect differences."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mo.config import RESULTS  # noqa: E402
from mo import macro, regime as R  # noqa: E402

MONTHS = pd.period_range("1990-01", "2026-09", freq="M")
rng = np.random.default_rng(0)
cuts = sorted(rng.choice(MONTHS[24:], size=60, replace=False))

ipv, cpi = macro.ip_vintages(), macro.cpi_nsa()
full_sig = R.realtime_signals(MONTHS, ipv, cpi)
full = {"raw": R.classify(full_sig), "smooth_persist": R.persist(R.classify(R.smooth(full_sig)))}

res = {"cuts": len(cuts), "identical_raw": 0, "identical_smooth_persist": 0}
leak_diff = 0
for t in cuts:
    ipv_t = ipv[[c for c in ipv.columns if c <= t]]
    cpi_t = cpi[cpi.index <= t - 1]
    sig_t = R.realtime_signals(MONTHS[MONTHS <= t], ipv_t, cpi_t)
    raw_t = R.classify(sig_t)
    sp_t = R.persist(R.classify(R.smooth(sig_t)))
    # Every label up to and including t must match the full-data run.
    res["identical_raw"] += int(raw_t.equals(full["raw"].loc[raw_t.index]))
    res["identical_smooth_persist"] += int(sp_t.equals(full["smooth_persist"].loc[sp_t.index]))

    # Positive control: CPI for month t leaks into the decision at t.
    cpi_leak = cpi[cpi.index <= t]
    leak_sig = R.realtime_signals([t], ipv_t, cpi_leak.rename(index=lambda p: p - 1))
    if len(leak_sig) and not np.isclose(leak_sig.i.iloc[0], full_sig.loc[t, "i"]):
        leak_diff += 1

res["positive_control_cuts_with_changed_signal"] = leak_diff

# Same comparison as the real test, but with CPI one month ahead throughout: labels must differ.
leak_label_diff = 0
cpi_ahead = cpi.rename(index=lambda p: p - 1)
for t in cuts:
    ipv_t = ipv[[c for c in ipv.columns if c <= t]]
    raw_leak = R.classify(R.realtime_signals(MONTHS[MONTHS <= t], ipv_t, cpi_ahead))
    leak_label_diff += int(not raw_leak.equals(full["raw"].loc[raw_leak.index]))
res["positive_control_cuts_flagged_by_label_test"] = leak_label_diff
res["pass"] = (res["identical_raw"] == len(cuts) and res["identical_smooth_persist"] == len(cuts)
               and leak_diff > 0.9 * len(cuts) and leak_label_diff == len(cuts))
(RESULTS / "test_s1_lookahead.json").write_text(json.dumps(res, indent=1))
print(json.dumps(res, indent=1))
assert res["pass"]
