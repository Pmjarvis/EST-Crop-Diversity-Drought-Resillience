
import numpy as np


def decompose(values, resid):
    
    values, resid = np.asarray(values, dtype=float), np.asarray(resid, dtype=float)
    assert values.shape == resid.shape and values.ndim == 2, "values and resid must be (years, crops)"
    assert np.isfinite(values).all() and np.isfinite(resid).all(), "decompose needs a balanced panel without NaN"
    sd = resid.std(axis=0, ddof=1)
    mean = values.mean(axis=0)
    total_resid = resid.sum(axis=1)
    phi_sync = total_resid.var(ddof=1) / sd.sum() ** 2
    w = mean / mean.sum()
    mean_crop_cv = (w * sd / mean).sum()
    cv_total = total_resid.std(ddof=1) / values.sum(axis=1).mean()
    assert abs(cv_total - np.sqrt(phi_sync) * mean_crop_cv) < 1e-9, "portfolio identity violated"
    return {"phi_sync": float(phi_sync), "mean_crop_cv": float(mean_crop_cv), "cv_total": float(cv_total)}
