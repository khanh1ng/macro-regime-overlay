"""Rebuild every result and both papers from the frozen raw data in data/."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STEPS = [
    "scripts/s0_verify.py",
    "scripts/s1_regimes.py",
    "tests/test_s1_lookahead.py",
    "scripts/s2_predict.py",
    "scripts/s3_backtest.py",
    "tests/test_backtest.py",
    "scripts/s5_stats.py",
    "scripts/s6_costs.py",
    "scripts/s7_holdouts.py",
    "scripts/s8_model.py",
    "scripts/s9_mechanism.py",
    "scripts/s10_robustness.py",
    "scripts/s11_market_regimes.py",
    "tests/test_regression.py",
    "scripts/make_papers.py",
    "scripts/report_readme.py",
]

for s in STEPS:
    print(f"--- {s}", flush=True)
    r = subprocess.run([sys.executable, str(ROOT / s)], cwd=ROOT, stdout=subprocess.DEVNULL)
    if r.returncode != 0:
        sys.exit(f"FAILED: {s}")
print("all steps passed")
