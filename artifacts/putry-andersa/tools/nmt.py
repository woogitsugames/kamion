"""NMT 1 m sampler in local E,N (ADR 0146)."""
import numpy as np
from pathlib import Path
REPO = Path(__file__).resolve().parents[3]
Z = np.fromfile(REPO / 'Data/raw/derived/bialystok-industrial-c/heightmap_2049.r16', dtype='<u2').reshape(2049, 2049)
OX, OY = 777995.0, 596223.0
def z(e, n):
    i = int(round(e + OX - 776971.0)); j = int(round(597247.0 - (n + OY)))
    return 120.0 + Z[j, i] * 0.000686655985351339
