
import numpy as np


def hill1(mean_area):
    
    a = np.asarray(mean_area, dtype=float)
    a = a[np.isfinite(a) & (a > 0)]
    if a.size == 0:
        return np.nan
    p = a / a.sum()
    return float(np.exp(-(p * np.log(p)).sum()))
