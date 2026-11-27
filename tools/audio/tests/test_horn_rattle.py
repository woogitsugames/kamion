"""Tests for procedural pneumatic air horn and trailer rattle WAV synthesis."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import dsp  # noqa: E402
import horn_rattle as hr  # noqa: E402


def test_horn_rattle_clips_determinism_and_headroom():
    first = list(hr.clips())
    second = list(hr.clips())
    assert [c[0] for c in first] == [
        "horn_air_loop",
        "horn_air_cab_loop",
        "trailer_rattle_chain_a",
        "trailer_rattle_chain_a_cab",
        "trailer_rattle_chain_b",
        "trailer_rattle_chain_b_cab",
        "trailer_rattle_tarp_a",
        "trailer_rattle_tarp_a_cab",
        "trailer_rattle_kingpin",
        "trailer_rattle_kingpin_cab",
    ]
    for (n1, x1, p1, l1), (n2, x2, p2, l2) in zip(first, second):
        assert n1 == n2 and p1 == p2 and l1 == l2
        assert np.array_equal(x1, x2), f"{n1} must be deterministic"
        peak_db = dsp.db(float(np.max(np.abs(x1))))
        assert peak_db <= -1.5, f"{n1} peak {peak_db:.2f} dBFS exceeds -1.5 dBFS"
        assert dsp.rms(x1) > 1e-4, f"{n1} is silent"


def test_horn_loop_seam_and_cab_attenuation():
    by_name = {name: x for name, x, _, _ in hr.clips()}
    for name in ("horn_air_loop", "horn_air_cab_loop"):
        x = by_name[name]
        assert len(x) == dsp.FS
        jump = abs(float(x[0] - x[-1]))
        p99 = float(np.percentile(np.abs(np.diff(x)), 99.9))
        assert jump / max(p99, 1e-12) < 0.3, f"{name} seam discontinuous"
    assert dsp.rms(by_name["horn_air_cab_loop"]) < dsp.rms(by_name["horn_air_loop"])


def test_rattle_cab_quieter_than_exterior():
    by_name = {name: x for name, x, _, _ in hr.clips()}
    for base in ("trailer_rattle_chain_a", "trailer_rattle_chain_b", "trailer_rattle_tarp_a", "trailer_rattle_kingpin"):
        assert dsp.rms(by_name[base + "_cab"]) < dsp.rms(by_name[base])
