
import numpy as np

MIN_YEARS = 20       
MIN_SHARE = 0.01     


def resp_beta(yield_anom, spei):
    
    a, s = np.asarray(yield_anom, dtype=float), np.asarray(spei, dtype=float)
    ok = np.isfinite(a) & np.isfinite(s)
    if ok.sum() < MIN_YEARS or np.ptp(s[ok]) == 0:
        return np.nan
    return float(np.polyfit(s[ok], a[ok], 1)[0])


def resp_div(betas, weights):
    
    b, w = np.asarray(betas, dtype=float), np.asarray(weights, dtype=float)
    ok = np.isfinite(b) & np.isfinite(w) & (w > 0)
    if ok.sum() < 2:
        return np.nan
    b, w = b[ok], w[ok] / w[ok].sum()
    return float(np.sqrt((w * (b - (w * b).sum()) ** 2).sum()))


def resp_divergence(betas):
    
    b = np.asarray(betas, dtype=float)
    b = b[np.isfinite(b)]
    if b.size < 2:
        return np.nan
    hi, lo = b.max(), b.min()
    if hi == lo:
        return 0.0
    return float((hi - lo - abs(abs(hi) - abs(lo))) / (hi - lo))
