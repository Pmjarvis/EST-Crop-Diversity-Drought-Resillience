
import numpy as np
import pandas as pd
from statsmodels.nonparametric.smoothers_lowess import lowess

FRAC = 0.5
MIN_POINTS = 10


def lowess_trend(y, x=None, frac=FRAC):
    
    y = np.asarray(y, dtype=float)
    x = np.arange(len(y), dtype=float) if x is None else np.asarray(x, dtype=float)
    trend = np.full(len(y), np.nan)
    ok = np.isfinite(y)
    if ok.sum() < MIN_POINTS:
        return trend
    trend[ok] = lowess(y[ok], x[ok], frac=frac, return_sorted=False)
    return trend


def detrend(y, x=None, frac=FRAC):
    
    y = np.asarray(y, dtype=float)
    trend = lowess_trend(y, x, frac)
    trend = np.where(trend > 0, trend, np.nan)  
    return pd.DataFrame({
        "y": y, "trend": trend, "resid": y - trend,
        "anom": (y - trend) / trend, "index": y / trend,
    })
