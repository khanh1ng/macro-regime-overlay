"""Strategy weights: the frozen regime tables and the baselines of EVAL_LOG Step 3."""
import numpy as np
import pandas as pd

from .backtest import ASSETS, K_TABLE, G_TABLE, table_weights, run

VOL_TARGET = 0.15
TREND_MONTHS = 10


def const(weights, index):
    return pd.DataFrame([weights] * len(index), index=index).reindex(columns=ASSETS).fillna(0.0)


def vol_target(fund_ret, index):
    vol = fund_ret.rolling(12).std() * np.sqrt(12)
    w = (VOL_TARGET / vol).clip(upper=1.0).reindex(index)
    return pd.DataFrame({"FUND": w, "SHY": 1 - w}, index=index).reindex(columns=ASSETS).fillna(0.0)


def trend(fund_ret, index):
    level = (1 + fund_ret).cumprod()
    on = (level > level.rolling(TREND_MONTHS).mean()).astype(float).reindex(index)
    return pd.DataFrame({"FUND": on, "SHY": 1 - on}, index=index).reindex(columns=ASSETS).fillna(0.0)


def build(labels, rets, start, end):
    """All strategies for one period. Weights are indexed by decision month (one month before
    each return month). Returns {name: backtest frame}, plus K's weights for attribution."""
    dec = pd.period_range(pd.Period(start, "M") - 1, pd.Period(end, "M") - 1, freq="M")
    lab = labels.reindex(dec)
    if lab.isna().any():
        raise ValueError("regime label missing in the decision window")
    wK = table_weights(lab, K_TABLE)
    wG = table_weights(lab, G_TABLE)
    fund = rets["FUND"]
    W = {
        "K": wK,
        "G": wG,
        "Fund": const({"FUND": 1.0}, dec),
        "S-K": const(wK.mean().to_dict(), dec),
        "60/40": const({"FUND": 0.6, "IEF": 0.4}, dec),
        "VolTarget": vol_target(fund, dec),
        "Trend": trend(fund, dec),
        "90/10 GLD": const({"FUND": 0.9, "GLD": 0.1}, dec),
    }
    out = {k: run(w, rets, start, end) for k, w in W.items()}
    return out, W
