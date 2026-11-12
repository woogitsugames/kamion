"""ADR 0156: before/after of the ElevenLabs cab engine without load (REGEN-04), through the runtime mirror.

    uv run --project tools/audio python tools/audio/el_regen04_ab.py [--before <repo root>]

Before = el_manifest.json + clips of --before (default: the main checkout), after = this checkout.
Engine only (runtime_sim.LayerGrid, ElevenLabs crossfade = equal power, XFADE_COHERENCE 0, bank gain elCabEngineScale
0.7 as in idle_ab.py), cab perspective, load 0 (throttle released), pool 6:
  A) fixed points 600, 750, ..., 1500 rpm, 4 s each (first 0.5 s skipped): line_db = prominence of rpm/20 over the
     +-25 Hz running median (same measure as el_regen04.cell_line_db), RMS dBFS, AM CV of the 60-130 Hz envelope
  B) coast 1500 -> 900 rpm in 12 s (linear, coasting in gear; ADR 0148 owner video: 1500 -> 900 in ~12 s) with
     1 s holds at both ends: 0.5 s windows -> line_db at the momentary rpm/20, RMS; level smoothness = max |step| of the
     100 ms RMS (dB) and of the 0.5 s RMS between neighbours.
Outputs artifacts/audio-regen04/ab/: coast_1500_900_{before,after}.wav, fixed_<rpm>_{before,after}.wav (one common gain
per pair, 16-bit), ab.json, ab_coast.png (spectrograms + line/level curves).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402
from scipy import signal  # noqa: E402

import el_demo as ed  # noqa: E402
import runtime_sim as rs  # noqa: E402
from el_analyze import MAIN, db, prominence_db, welch_db  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "audio-regen04" / "ab"
FS = 48000
EL_CAB_SCALE = 0.7
FIXED = [600, 750, 900, 1050, 1200, 1350, 1500]


def grid(root: Path) -> rs.LayerGrid:
    man = json.loads((root / "game/Assets/_Project/Audio/ElevenLabs/el_manifest.json").read_text(encoding="utf-8"))
    ed.CLIP_ROOT = root
    rs.XFADE_COHERENCE = 0.0
    return ed.load_grid_el(man, "engine", "cab", 6)


def render(g: rs.LayerGrid, rpm_of_t, dur: float) -> np.ndarray:
    n = int(FS / rs.FRAME_HZ)
    out = []
    for i in range(int(dur * rs.FRAME_HZ)):
        g.update(rpm_of_t(i / rs.FRAME_HZ), 0.0, EL_CAB_SCALE)
        out.append(g.render(n, FS))
    return np.concatenate(out)


def line_db(x: np.ndarray, f_line: float, nper: int = 1 << 15) -> float:
    f, p = welch_db(x, FS, nper)
    pr = prominence_db(f, p)
    k = (f > f_line * 0.97) & (f < f_line * 1.03)
    return float(pr[k].max())


def am_cv(x: np.ndarray) -> float:
    env = np.abs(signal.hilbert(signal.sosfiltfilt(signal.butter(4, (60, 130), "bp", fs=FS, output="sos"), x)))
    return float(env.std() / env.mean())


def rms_db(x: np.ndarray) -> float:
    return db(float(np.sqrt(np.mean(x ** 2))))


def coast_rpm(t: float) -> float:
    return 1500.0 if t < 1.0 else (900.0 if t > 13.0 else 1500.0 - 600.0 * (t - 1.0) / 12.0)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", default=str(MAIN))
    a = ap.parse_args()
    roots = {"before": Path(a.before), "after": ROOT}
    OUT.mkdir(parents=True, exist_ok=True)
    res: dict = {"fixed": {}, "coast": {}}
    sigs: dict = {}
    for tag, root in roots.items():
        for rpm in FIXED:
            x = render(grid(root), lambda t, r=rpm: float(r), 4.0)
            sigs[(rpm, tag)] = x
            y = x[FS // 2:]
            res["fixed"].setdefault(str(rpm), {})[tag] = {"line_db": round(line_db(y, rpm / 20), 1), "rms_dbfs": round(rms_db(y), 1),
                                                          "am_cv_60_130": round(am_cv(y), 2)}
        x = render(grid(root), coast_rpm, 14.0)
        sigs[("coast", tag)] = x
        w = FS // 2
        ts, ld, lv = [], [], []
        for i0 in range(0, len(x) - w + 1, w // 2):
            tc = (i0 + w / 2) / FS
            ts.append(tc)
            ld.append(line_db(x[i0:i0 + w], coast_rpm(tc) / 20, nper=w))
            lv.append(rms_db(x[i0:i0 + w]))
        h = FS // 10
        l100 = np.array([rms_db(x[i:i + h]) for i in range(0, len(x) - h + 1, h)])
        ramp = (np.array(ts) >= 1.0) & (np.array(ts) <= 13.0)
        res["coast"][tag] = {"t": [round(v, 2) for v in ts], "line_db": [round(v, 1) for v in ld], "rms_db": [round(v, 1) for v in lv],
                             "line_db_median_ramp": round(float(np.median(np.array(ld)[ramp])), 1),
                             "line_db_min_ramp": round(float(np.min(np.array(ld)[ramp])), 1),
                             "rms_db_ramp_range": round(float(np.ptp(np.array(lv)[ramp])), 1),
                             "max_step_100ms_db": round(float(np.max(np.abs(np.diff(l100[10:-1])))), 2),
                             "max_step_500ms_db": round(float(np.max(np.abs(np.diff(np.array(lv)[ramp])))), 2),
                             "rms_dbfs": round(rms_db(x[FS:13 * FS]), 1), "am_cv_60_130": round(am_cv(x[FS:13 * FS]), 2)}
    # wavs, one gain per pair
    for key in [("coast",)] + [(r,) for r in FIXED]:
        b, af = sigs[(key[0], "before")], sigs[(key[0], "after")]
        g = 0.5 / max(np.abs(b).max(), np.abs(af).max())
        k = int(0.02 * FS)
        for tag, y in (("before", b), ("after", af)):
            z = y * g
            z[:k] *= np.linspace(0, 1, k)
            z[-k:] *= np.linspace(1, 0, k)
            name = "coast_1500_900" if key[0] == "coast" else f"fixed_{key[0]:04d}"
            sf.write(OUT / f"{name}_{tag}.wav", z.astype(np.float32), FS, subtype="PCM_16")
    fig, axs = plt.subplots(3, 2, figsize=(16, 11), gridspec_kw={"height_ratios": [3, 1.2, 1.2]})
    for j, tag in enumerate(("before", "after")):
        x = sigs[("coast", tag)]
        f, t, S = signal.spectrogram(x, FS, nperseg=1 << 14, noverlap=(1 << 14) * 7 // 8)
        k = f <= 400
        L = 10 * np.log10(S[k] + 1e-20)
        axs[0, j].pcolormesh(t, f[k], L, shading="auto", cmap="magma", vmin=L.max() - 60)
        tt = np.linspace(0, 14, 200)
        for hk in (1, 2, 3):
            axs[0, j].plot(tt, [hk * coast_rpm(v) / 20 for v in tt], "c:", lw=0.6)
        axs[0, j].set_title(f"{tag}: ElevenLabs cab, load 0, coast 1500 -> 900 rpm (dotted: k x rpm/20)", fontsize=9)
        c = res["coast"][tag]
        axs[1, j].plot(c["t"], c["line_db"], "o-", ms=2)
        axs[1, j].set_ylabel("line rpm/20 dB over floor", fontsize=8)
        axs[1, j].set_ylim(0, 35)
        axs[1, j].grid(alpha=0.3)
        axs[2, j].plot(c["t"], c["rms_db"], "o-", ms=2)
        axs[2, j].set_ylabel("RMS 0.5 s dBFS", fontsize=8)
        axs[2, j].set_xlabel("s", fontsize=8)
        axs[2, j].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "ab_coast.png", dpi=60)
    (OUT / "ab.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    for rpm in FIXED:
        print(rpm, res["fixed"][str(rpm)])
    for tag in roots:
        print(tag, {k: v for k, v in res["coast"][tag].items() if k not in ("t", "line_db", "rms_db")})


if __name__ == "__main__":
    main()
