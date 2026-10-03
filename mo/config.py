from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
ALFRED = ROOT / "data" / "alfred"
RESULTS = ROOT / "results"

# Fund under study and its older share class (same portfolio, different fee).
FUND = "JLGMX"
FUND_OLD = "SEEGX"

# Equity references and the hold-out funds the frozen rule is applied to unchanged.
EQUITY_REF = ["IWF", "QQQ", "SPY"]
HOLDOUT_FUNDS = ["FBGRX", "TRBCX", "AGTHX"]

# Candidate non-equity sleeves.
SLEEVES = ["GLD", "SHY", "IEF", "TLT", "TIP", "HYG", "UUP", "DBC"]

TICKERS = [FUND, FUND_OLD] + EQUITY_REF + HOLDOUT_FUNDS + SLEEVES

START = "1990-01-01"
END = "2026-09-30"

# Macro series for the regime classifier, and the risk-free rate.
MACRO_SERIES = ["INDPRO", "CPIAUCSL"]
RF_SERIES = "TB3MS"
