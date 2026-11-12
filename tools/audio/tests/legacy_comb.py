"""Pre-fix comb_estimate (octave bug), verbatim from git b54a33bd~1:tools/audio/el_analyze.py.

The octave-fix commit b54a33bd changed only comb_estimate in el_analyze.py;
welch_db / prominence_db / comb_score are identical before and after, so they are
imported from the current el_analyze. Use via KAMION_COMB_IMPL=legacy (see
test_comb_octave_regression.py) to prove the regression tests fail on the old code.
"""

from __future__ import annotations

import numpy as np
from scipy import signal

from el_analyze import comb_score, prominence_db, welch_db


def comb_estimate(x: np.ndarray, fs: int) -> dict:
    f, pdb = welch_db(x, fs)
    prom = prominence_db(f, pdb)
    cands = np.arange(12.0, 160.0, 0.05)
    sc = np.array([comb_score(f, prom, c) for c in cands])
    # local maxima, top 4
    pk, _ = signal.find_peaks(sc, distance=int(2.0 / 0.05))
    pk = pk[np.argsort(sc[pk])[::-1]][:4]
    tops = [(float(cands[i]), float(sc[i])) for i in pk]
    best = tops[0][0]
    # octave correction: prefer f/2 if its comb is nearly as good (half orders present), else 2f if better
    s_half = comb_score(f, prom, best / 2)
    s_dbl = comb_score(f, prom, best * 2)
    return {"comb_f": best, "comb_score": tops[0][1], "comb_top": tops, "comb_half": s_half, "comb_double": s_dbl,
            "_f": f, "_prom": prom}
