"""F0 / firing-order detection -> RPM on synthetic harmonic signals.

Inline six, four-stroke: firing order 3, so f_fire = rpm/60*3 = rpm/20 Hz and every
el_analyze estimator must report rpm = 20 * f_fire.
"""

import numpy as np
import pytest
import soundfile as sf

import el_analyze as ea
from synth_helpers import FS, firing_hz, harmonic_engine

RPMS = [600, 900, 1500, 2100]


@pytest.mark.parametrize("rpm", RPMS)
def test_comb_estimate_recovers_rpm(rpm):
    x = harmonic_engine(FS, rpm, dur_s=6.0)
    c = ea.comb_estimate(x, FS)
    f_exp = firing_hz(rpm)
    assert abs(c["comb_f"] - f_exp) / f_exp < 0.015, \
        f"comb_f={c['comb_f']:.2f} Hz, expected {f_exp:.2f} Hz (rpm {rpm}), top={c['comb_top']}"
    assert abs(c["comb_f"] * 20 - rpm) / rpm < 0.015


@pytest.mark.parametrize("rpm", RPMS)
def test_env_estimate_recovers_rpm(rpm):
    x = harmonic_engine(FS, rpm, dur_s=6.0)
    f = ea.env_estimate(x, FS)
    f_exp = firing_hz(rpm)
    assert abs(f - f_exp) / f_exp < 0.03, f"env f={f:.2f} Hz, expected {f_exp:.2f} Hz (rpm {rpm})"


@pytest.mark.parametrize("rpm", [900, 1500, 2100])
def test_yin_f0_recovers_firing_frequency(rpm):
    x = harmonic_engine(FS, rpm, dur_s=6.0)
    f0, aper = ea.yin_f0(x, FS)
    f_exp = firing_hz(rpm)
    assert abs(f0 - f_exp) / f_exp < 0.03, f"yin f0={f0:.2f} Hz, expected {f_exp:.2f} Hz (rpm {rpm})"
    assert aper < 0.35, f"aperiodicity {aper:.3f}"


def test_track_reports_stable_rpm():
    rpm = 1500
    x = harmonic_engine(FS, rpm, dur_s=6.0)
    c = ea.comb_estimate(x, FS)
    t = ea.track(x, FS, c["comb_f"], c["_f"], c["_prom"], force_k=1)
    assert abs(t["rpm_med"] - rpm) / rpm < 0.01, f"rpm_med={t['rpm_med']:.1f}"
    assert t["rpm_std"] < 0.01 * rpm, f"rpm_std={t['rpm_std']:.2f}"
    assert (t["rpm_max"] - t["rpm_min"]) / rpm < 0.03


@pytest.mark.parametrize("snr", [20.0, 10.0])
def test_rpm_stable_under_noise(snr):
    rpm = 1500
    x = harmonic_engine(FS, rpm, dur_s=6.0, snr_db=snr)
    c = ea.comb_estimate(x, FS)
    assert abs(c["comb_f"] * 20 - rpm) / rpm < 0.03, \
        f"SNR {snr} dB: comb rpm {c['comb_f'] * 20:.0f} vs {rpm}"
    f_env = ea.env_estimate(x, FS)
    assert abs(f_env * 20 - rpm) / rpm < 0.05, \
        f"SNR {snr} dB: env rpm {f_env * 20:.0f} vs {rpm}"


def test_analyse_end_to_end_on_synthetic_wav(tmp_path):
    rpm = 1500
    x = harmonic_engine(FS, rpm, dur_s=6.0)
    p = tmp_path / "ENG_EXT_ON_1500 (1).wav"
    sf.write(str(p), x.astype(np.float32), FS)
    r = ea.analyse(p)
    assert r["rpm_nominal"] == rpm
    for key in ("rpm_actual", "env_rpm"):
        assert abs(r[key] - rpm) / rpm < 0.03, f"{key}={r[key]:.1f} vs nominal {rpm}"
    assert r["ladder_n"] >= 3, f"ladder_n={r['ladder_n']}"


@pytest.mark.skip(reason="KNOWN BUG (not fixed per task): el_analyze.py:146-160 comb_estimate computes the octave "
                          "check (comb_half/comb_double) but never applies it, so on a synthetic 1500 rpm "
                          "harmonic ladder (75 Hz firing line) read back from a float32 WAV it returns "
                          "comb_f = 149 Hz -> comb_rpm = 2980 (octave up). Expected comb_rpm = 1500 +- 3 %. "
                          "The same signal in float64 scores 75.0 vs 149.0 only marginally, so the pick "
                          "flips with quantization noise. Listed in the PR description bug list.")
def test_comb_estimate_no_octave_error_on_wav_roundtrip(tmp_path):
    rpm = 1500
    x = harmonic_engine(FS, rpm, dur_s=6.0)
    p = tmp_path / "ENG_EXT_ON_1500 (1).wav"
    sf.write(str(p), x.astype(np.float32), FS)
    r = ea.analyse(p)
    assert abs(r["comb_rpm"] - rpm) / rpm < 0.03, f"comb_rpm={r['comb_rpm']:.1f} vs nominal {rpm}"
