
import numpy as np

from .events import PAD

LOSS_THR = 0.9  


def cv_resid(y, resid):
    
    return float(np.nanstd(resid, ddof=1) / np.nanmean(y))


def stability(y, resid):
    
    return 1.0 / cv_resid(y, resid)


def _event_ratios(index, event_years):
    
    out = []
    for t in event_years:
        win = index.reindex(range(t - PAD, t + PAD + 1))
        if win.isna().any():
            continue
        before, at, after = win.iloc[:PAD].mean(), win.iloc[PAD], win.iloc[PAD + 1:].mean()
        out.append((at / before, after / at))
    return out


def resistance(index, event_years):
    
    r = _event_ratios(index, event_years)
    return float(np.median([a for a, _ in r])) if r else np.nan


def recovery(index, event_years):
    
    r = _event_ratios(index, event_years)
    return float(np.median([b for _, b in r])) if r else np.nan


def n_usable_events(index, event_years):
    return len(_event_ratios(index, event_years))


def vulnerability(index, years=None):
    
    s = index.dropna()
    if years is not None:
        s = s[s.index.isin(list(years))]
    return float((s < LOSS_THR).mean()) if len(s) else np.nan
