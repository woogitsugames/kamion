"""ADR 0176: checks, spectrograms (before / after / reference) and owner A/B scenes for synth0176.

    uv run python synth0176_ab.py            # everything -> artifacts/audio-synth-0176/
    uv run python synth0176_ab.py --no-refs  # skip the reference spectrograms (research files absent)

* ``checks.json``  -- loop seam metrics (analyze.seam_metrics), one-shot edges, peak, LUFS, HF-transient
  count, runtime law tables (retarder gain vs speed, engine-brake release level vs rpm).
* ``spec/*.png``   -- before (bank on main) vs after spectrograms per layer, reference spectrograms
  (CC0 / CC BY research files: comparison only, never shipped).
* ``ab/*.wav``     -- short scenes, A = current synthesis set (main), B = ADR 0176 layers, both through the
  same mini runtime mirror (variable-rate loop playback, same volumes as TruckAudioController / DrivelineSfx).

The runtime laws below mirror LayerMath.cs (ADR 0176 section); change both together.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402
from scipy import signal  # noqa: E402

import dsp  # noqa: E402
import sfx_layers as sl  # noqa: E402
import synth0176 as s76  # noqa: E402
from analyze import seam_metrics  # noqa: E402
from dsp import FS, save_png_small  # noqa: E402
from el_analyze import lufs  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CLIPS = ROOT / "game" / "Assets" / "_Project" / "Audio" / "Generated" / "Clips"
OUT = ROOT / "artifacts" / "audio-synth-0176"
MAIN_ROOT = Path(r"C:\Users\matma\Documents\Claude\kamion")
REFS = [  # (label, path, start s, dur s, licence) -- comparison only
    ("ref M55-002 autokar, zmiany biegow (CC0)", "research/_incoming/mistral-p5-audio-3/files/fs_846043_volvo-b8r-bus-ride-highway-HQ.mp3", 60.0, 20.0, "CC0"),
    ("ref M55-001 spust powietrza + przejazd (CC0)", "research/_incoming/mistral-p5-audio-3/files/fs_637922_kyles_truck-air-release-pass.mp3", 0.0, 12.0, "CC0"),
    ("ref P5-002 hamulce silnikowe I-15 (fragment)", "research/gptpro/p5-audio-refs-2/files/P5-002.wav", 0.0, 20.0, "see manifest"),
    ("ref P5-006 zwolnienie hamulcow (CC0?)", "research/gptpro/p5-audio-refs-2/files/P5-006.mp3", 0.0, 4.3, "see manifest"),
]

# --------------------------------------------------------------------------- runtime laws (mirror LayerMath.cs)
WHEEL_R = 0.51           # tire_315_80_r22_5.tire.json radius
FINAL_DRIVE = 3.4        # tractor_4x2_generic.vehicle.json
RET_MAX_T, RET_MAX_P, RET_FULL_RPM = 4000.0, 600e3, 900.0  # RetarderDefinition defaults
RET_TONE_FULL_RPM = 1600.0
RET_TONE_MIX, RET_FLOW_MIX = 0.35, 0.65


def shaft_rpm_from_speed(v: float) -> float:
    return v / WHEEL_R * FINAL_DRIVE * 60 / (2 * math.pi)


def retarder_power(fill: float, shaft_rpm: float) -> float:
    w = shaft_rpm * 2 * math.pi / 60
    t = RET_MAX_T * min(1.0, (shaft_rpm / RET_FULL_RPM) ** 2)
    if w > 1e-3:
        t = min(t, RET_MAX_P / w)
    return fill * t * w


def retarder_tone_gain(fill: float, shaft_rpm: float, vol: float) -> float:
    return vol * RET_TONE_MIX * fill ** 0.8 * min(1.0, shaft_rpm / RET_TONE_FULL_RPM) ** 1.5


def retarder_flow_gain(power_w: float, vol: float) -> float:
    return vol * RET_FLOW_MIX * math.sqrt(min(1.0, max(0.0, power_w / RET_MAX_P)))


def retarder_tone_pitch(shaft_rpm: float) -> float:
    return min(2.5, max(0.2, shaft_rpm / s76.REF_SHAFT_RPM))


def old_retarder_gain(fill: float, vol: float) -> float:   # LayerMath.RetarderGain (pre-0176)
    return vol * fill ** 0.9


def old_retarder_pitch(v: float) -> float:                 # LayerMath.RetarderPitch (pre-0176)
    return 0.5 + 1.0 * min(1.0, v / 22.0)


def ebrake_release_level(rpm: float, vol: float) -> float:
    return vol * (0.4 + 0.6 * min(1.0, max(0.0, (rpm - 900.0) / 1100.0)))


# --------------------------------------------------------------------------- io helpers
def load(path: Path, start: float = 0.0, dur: float | None = None) -> np.ndarray:
    if path.suffix.lower() in (".mp3", ".ogg", ".opus"):
        cmd = ["ffmpeg", "-v", "error", "-ss", str(start)] + (["-t", str(dur)] if dur else []) + \
              ["-i", str(path), "-ac", "1", "-ar", str(FS), "-f", "f32le", "-"]
        raw = subprocess.run(cmd, capture_output=True, check=True).stdout
        return np.frombuffer(raw, dtype=np.float32).astype(np.float64)
    x, fs = sf.read(path, always_2d=True)
    x = x.mean(axis=1)
    if fs != FS:
        x = signal.resample_poly(x, FS, fs)
    i0 = int(start * FS)
    return x[i0:i0 + int(dur * FS)] if dur else x[i0:]


def clip(rel: str) -> np.ndarray:
    return load(CLIPS / rel)


def wav(path: Path, x: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(path, np.clip(x, -1, 1).astype(np.float32), FS, subtype="PCM_16")


def norm_render_all(x: np.ndarray, is_loop: bool) -> np.ndarray:
    """Same peak normalisation as render_all.py for SFX (loops -6 dBFS, one-shots -1 dBFS)."""
    return x * (10 ** ((-6.0 if is_loop else -1.0) / 20) / (np.max(np.abs(x)) + 1e-12))


def new_layers() -> dict[str, np.ndarray]:
    out = {}
    for name, (fn, is_loop, prof) in s76.LAYERS.items():
        x = norm_render_all(fn(), is_loop)
        out[name] = x
        c = sl.cab_filter(x, is_loop, prof)
        pk = np.max(np.abs(c))
        out[s76.cab_name(name, is_loop)] = c * (10 ** (-1 / 20) / pk) if pk > 10 ** (-1 / 20) else c
    return out


# --------------------------------------------------------------------------- mini runtime mirror
class Voice:
    """Loop playback with a per-sample pitch and gain curve (linear interpolation, like AudioSource.pitch)."""

    def __init__(self, data: np.ndarray):
        self.d = data
        self.pos = 0.0

    def render(self, pitch: np.ndarray, gain: np.ndarray) -> np.ndarray:
        n = len(pitch)
        ph = self.pos + np.concatenate([[0.0], np.cumsum(pitch[:-1])])
        self.pos = (ph[-1] + pitch[-1]) % len(self.d)
        ph %= len(self.d)
        i = ph.astype(np.int64)
        f = ph - i
        y = self.d[i] * (1 - f) + self.d[(i + 1) % len(self.d)] * f
        return y * gain


def smooth(g: np.ndarray, up_s: float, down_s: float) -> np.ndarray:
    """LayerMath.ExponentialStep per sample (attack / release time constants)."""
    out = np.empty_like(g)
    y = 0.0
    a_up, a_dn = 1 - math.exp(-1 / (up_s * FS)), 1 - math.exp(-1 / (down_s * FS))
    for k, v in enumerate(g):
        y += (v - y) * (a_up if v > y else a_dn)
        out[k] = y
    return out


def place(buf: np.ndarray, x: np.ndarray, at_s: float, gain: float) -> None:
    i0 = int(at_s * FS)
    m = min(len(x), len(buf) - i0)
    buf[i0:i0 + m] += gain * x[:m]


def engine_bed(persp: str, rpm: np.ndarray, load: np.ndarray, cell: int = 1300) -> np.ndarray:
    """Engine context: one rpm cell, pitch rpm/cell, off/on layers cross-faded by load (enough for A/B)."""
    on = clip(f"engine/{persp}/engine_{persp}_on_{cell:04d}.wav")
    off = clip(f"engine/{persp}/engine_{persp}_off_{cell:04d}.wav")
    p = rpm / cell
    return Voice(on).render(p, np.sqrt(load)) + Voice(off).render(p, np.sqrt(1 - load))


def road_bed(persp: str, v: np.ndarray) -> np.ndarray:
    name = "road_roll_loop" if persp == "ext" else "road_roll_cab_loop"
    vn = np.clip(v / 25, 0, 1)
    return Voice(clip(f"sfx/{name}.wav")).render(0.6 + 0.6 * vn, 0.45 * (0.55 if persp == "cab" else 1) * vn ** 1.5)


# --------------------------------------------------------------------------- scenes
def scene_retarder(new: dict, persp: str, version: str) -> np.ndarray:
    """Downhill: 85 -> 12 km/h on the retarder at full lever, release, coast 2 s."""
    dur = 14.0
    n = int(dur * FS)
    t = np.arange(n) / FS
    v = np.interp(t, [0, 1.0, 11.0, 14.0], [85, 85, 12, 12]) / 3.6
    cmd = ((t > 1.0) & (t < 11.5)).astype(float)
    fill = smooth(cmd, 0.4, 0.3)
    shaft = shaft_rpm_from_speed(1) * v
    rpm = np.clip(shaft * 1.0, 650, 1900)  # 12th gear ~1:1 -> engine rpm ~ shaft rpm (context only)
    bed = 0.55 * engine_bed(persp, rpm, np.zeros(n)) + road_bed(persp, v)
    vol = 0.5 * (0.85 if persp == "cab" else 1.0)
    if version == "A":
        g = smooth(np.array([old_retarder_gain(f, vol) for f in fill]), 0.08, 0.25)
        name = "retarder_loop" if persp == "ext" else "retarder_cab_loop"
        lay = Voice(clip(f"sfx/{name}.wav")).render(np.array([old_retarder_pitch(x) for x in v]), g)
    else:
        pw = np.array([retarder_power(f, s) for f, s in zip(fill, shaft)])
        gt = smooth(np.array([retarder_tone_gain(f, s, vol) for f, s in zip(fill, shaft)]), 0.08, 0.25)
        gf = smooth(np.array([retarder_flow_gain(p, vol) for p in pw]), 0.08, 0.25)
        pitch = np.array([retarder_tone_pitch(s) for s in shaft])
        tn = "retarder_tone_loop" if persp == "ext" else "retarder_tone_cab_loop"
        fn = "retarder_flow_loop" if persp == "ext" else "retarder_flow_cab_loop"
        lay = Voice(new[tn]).render(pitch, gt) + Voice(new[fn]).render(pitch, gf)
    return bed + lay


SHIFT = (0.12, 0.15, 0.20, 0.15)  # GearboxDefinition: torque ramp, neutral, sync, clutch close [s]


def scene_amt(new: dict, persp: str, version: str) -> np.ndarray:
    """Three up-shifts under load (1750 -> 1250 rpm), AMT phases timed like GearboxDefinition."""
    dur = 10.0
    n = int(dur * FS)
    t = np.arange(n) / FS
    rpm = np.full(n, 1100.0)
    load = np.ones(n)
    events = []
    t0 = 0.0
    for k in range(3):
        t_shift = 1.0 + 3.0 * k
        a = t >= t0
        rise = (t >= t0) & (t < t_shift)
        rpm[rise] = 1250 + 500 * (t[rise] - t0) / (t_shift - t0) if k else 1100 + 650 * (t[rise] - t0) / (t_shift - t0)
        tr, tn, ts, te = (t_shift, t_shift + SHIFT[0], t_shift + SHIFT[0] + SHIFT[1], t_shift + sum(SHIFT[:3]))
        td = te + SHIFT[3]
        m = (t >= tr) & (t < td)
        load[m] = np.interp(t[m], [tr, tn, te, td], [1, 0, 0, 1])
        rpm[m] = np.interp(t[m], [tr, tn, ts, te, td], [1750, 1740, 1500, 1260, 1250])
        events.append((tr, tn, te, td))
        t0 = td
        _ = a
    rpm[t >= t0] = 1250 + 300 * (t[t >= t0] - t0) / (dur - t0)
    bed = engine_bed(persp, rpm, load)
    pv = 0.55 * (0.6 if persp == "cab" else 1.0)
    fx = np.zeros(n)
    sfx = lambda name: new[name if persp == "ext" else s76.cab_name(name, False)]  # noqa: E731
    for i, (tr, tn, te, td) in enumerate(events):
        if version == "A":
            place(fx, clip(f"sfx/{'gearshift_air' if persp == 'ext' else 'gearshift_air_cab'}.wav"), tr, pv * 0.6)
        else:
            place(fx, sfx("amt_disengage"), tn, pv * 0.55)
            place(fx, sfx("amt_engage" if i % 2 == 0 else "amt_engage_b"), te, pv * 0.6)
            place(fx, sfx("amt_clutch_chuff"), td, pv * 0.45)
    return bed + fx


def scene_ebrake(new: dict, persp: str, version: str) -> np.ndarray:
    """Coast at 1700 rpm, engine brake 1.2-5 s and 6.5-9 s (actuator tau 0.25 s)."""
    dur = 10.5
    n = int(dur * FS)
    t = np.arange(n) / FS
    cmd = (((t > 1.2) & (t < 5.0)) | ((t > 6.5) & (t < 9.0))).astype(float)
    state = smooth(cmd, 0.25, 0.25)
    rpm = np.interp(t, [0, 5, 6.5, 9, 10.5], [1700, 1550, 1650, 1480, 1450])
    bed = engine_bed(persp, rpm, np.zeros(n)) + road_bed(persp, np.full(n, 60 / 3.6))
    eb = clip(f"ebrake/{persp}/ebrake_{persp}_1600.wav")
    bed += Voice(eb).render(rpm / 1600.0, state * (0.85 if persp == "cab" else 1.0))
    if version == "B":
        name = lambda b: b if persp == "ext" else s76.cab_name(b, False)  # noqa: E731
        vol = 0.5 * (0.7 if persp == "cab" else 1.0)
        for on, off in ((1.2, 5.0), (6.5, 9.0)):
            place(bed, new[name("ebrake_engage")], on + 0.02, vol * 0.7)
            r = float(np.interp(off, t, rpm))
            place(bed, new[name("ebrake_release")], off + 0.02, ebrake_release_level(r, vol))
    return bed


def scene_dryer(new: dict, persp: str, version: str) -> np.ndarray:
    """Idle, compressor loaded 0-3 s, governor cut-out at 3 s (purge), second cut-out at 11 s."""
    dur = 15.0
    n = int(dur * FS)
    t = np.arange(n) / FS
    rpm = np.full(n, 600.0)
    bed = engine_bed(persp, rpm, np.full(n, 0.15), cell=600)
    comp = "compressor_loop" if persp == "ext" else "compressor_cab_loop"
    loaded = (((t < 3.0) | ((t > 8.0) & (t < 11.0)))).astype(float)
    bed += Voice(clip(f"sfx/{comp}.wav")).render(np.full(n, 0.6), smooth(loaded * 0.06 * (0.75 if persp == "cab" else 1), 0.15, 0.12))
    pv = 0.55 * (0.6 if persp == "cab" else 1.0)
    if version == "A":
        a = "air_dryer_purge" if persp == "ext" else "air_dryer_purge_cab"
        b = "air_dryer_purge_b" if persp == "ext" else "air_dryer_purge_b_cab"
        place(bed, clip(f"sfx/{b}.wav"), 3.0, pv * 0.9)
        place(bed, clip(f"sfx/{a}.wav"), 11.0, pv * 0.8)
    else:
        a = "air_dryer_purge_v2" if persp == "ext" else "air_dryer_purge_v2_cab"
        b = "air_dryer_purge_v2b" if persp == "ext" else "air_dryer_purge_v2b_cab"
        place(bed, new[a], 3.0, pv * 0.85)
        place(bed, new[b], 11.0, pv * 0.85)
    return bed


SCENES = {"retarder": scene_retarder, "amt": scene_amt, "ebrake": scene_ebrake, "dryer": scene_dryer}


# --------------------------------------------------------------------------- analysis
def hf_transients(x: np.ndarray) -> int:
    """5 ms windows whose >4 kHz energy is 15 dB over the 0.5 s running median (el_regen04 crackle rule)."""
    y = signal.sosfilt(signal.butter(4, 4000, "hp", fs=FS, output="sos"), x)
    w = int(0.005 * FS)
    e = np.array([np.mean(y[i:i + w] ** 2) for i in range(0, len(y) - w, w)]) + 1e-14
    med = signal.medfilt(e, 101)
    return int(np.sum(10 * np.log10(e / (med + 1e-14)) > 15))


def spectrogram(ax, x: np.ndarray, title: str, fmax: float = 10000.0) -> None:
    f, tt, s = signal.spectrogram(x, FS, nperseg=2048, noverlap=1536)
    sdb = 10 * np.log10(s + 1e-12)
    ax.pcolormesh(tt, f, sdb, shading="auto", vmin=sdb.max() - 80, vmax=sdb.max(), cmap="magma")
    ax.set_ylim(20, fmax)
    ax.set_yscale("log")
    ax.set_title(title, fontsize=8)
    ax.tick_params(labelsize=7)


def fig_pair(path: Path, panels: list[tuple[str, np.ndarray]]) -> None:
    fig, axs = plt.subplots(len(panels), 1, figsize=(9.6, 2.3 * len(panels)), squeeze=False)
    for ax, (title, x) in zip(axs[:, 0], panels):
        if x is None or len(x) == 0:
            ax.text(0.5, 0.5, title + ": brak (warstwa nie istniala)", ha="center", va="center", fontsize=9)
            ax.set_axis_off()
            continue
        spectrogram(ax, x, title)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    save_png_small(fig, path)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-refs", action="store_true")
    args = ap.parse_args()
    new = new_layers()
    rep: dict = {"layers": {}, "laws": {}, "scenes": {}}

    for name, x in new.items():
        is_loop = name.endswith("_loop")
        r = {"seconds": round(len(x) / FS, 3), "peak_dbfs": round(dsp.db(np.max(np.abs(x))), 2),
             "lufs": round(lufs(x, FS), 2), "hf_transients": hf_transients(np.tile(x, 2) if is_loop else x)}
        if is_loop:
            r["seam"] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in seam_metrics(x).items()}
        else:
            r["edge_first_last"] = [round(float(abs(x[0])), 6), round(float(abs(x[-1])), 6)]
        rep["layers"][name] = r

    # runtime laws: retarder vs speed at full fill, engine-brake release level vs rpm
    rows = []
    for kmh in (5, 10, 20, 30, 50, 70, 85):
        s = shaft_rpm_from_speed(kmh / 3.6)
        p = retarder_power(1.0, s)
        rows.append({"kmh": kmh, "shaft_rpm": round(s), "power_kw": round(p / 1e3, 1),
                     "tone_db": round(dsp.db(retarder_tone_gain(1, s, 0.5) + 1e-9), 1),
                     "flow_db": round(dsp.db(retarder_flow_gain(p, 0.5) + 1e-9), 1),
                     "old_db": round(dsp.db(old_retarder_gain(1, 0.5)), 1),
                     "tone_bpf_hz": round(s76.blade_pass_hz(s), 1)})
    rep["laws"]["retarder_full_fill"] = rows
    rep["laws"]["ebrake_release_level"] = {r: round(ebrake_release_level(r, 0.5), 3) for r in (900, 1200, 1500, 1800, 2000)}

    # spectrograms before / after
    spec = OUT / "spec"
    before = {
        "retarder": [("A (main) retarder_loop", clip("sfx/retarder_loop.wav")),
                     ("B tone (1000 rpm walu)", new["retarder_tone_loop"]), ("B flow", new["retarder_flow_loop"])],
        "ebrake_events": [("A (main): brak zdarzen wlacz/zwolnij", None), ("B ebrake_engage", new["ebrake_engage"]),
                          ("B ebrake_release", new["ebrake_release"])],
        "amt": [("A (main) gearshift_air", clip("sfx/gearshift_air.wav")), ("B amt_disengage", new["amt_disengage"]),
                ("B amt_engage", new["amt_engage"]), ("B amt_clutch_chuff", new["amt_clutch_chuff"])],
        "dryer": [("A (main) air_dryer_purge", clip("sfx/air_dryer_purge.wav")),
                  ("A (main) air_dryer_purge_b", clip("sfx/air_dryer_purge_b.wav")),
                  ("B air_dryer_purge_v2", new["air_dryer_purge_v2"]), ("B air_dryer_purge_v2b", new["air_dryer_purge_v2b"])],
    }
    for key, panels in before.items():
        fig_pair(spec / f"before_after_{key}.png", panels)

    # owner A/B scenes
    ab = OUT / "ab"
    for sc, fn in SCENES.items():
        for persp in ("ext", "cab"):
            a = fn(new, persp, "A")
            b = fn(new, persp, "B")
            pk = max(np.max(np.abs(a)), np.max(np.abs(b)))
            g = 10 ** (-1 / 20) / pk if pk > 10 ** (-1 / 20) else 1.0
            wav(ab / f"{sc}_{persp}_A_main.wav", a * g)
            wav(ab / f"{sc}_{persp}_B_0176.wav", b * g)
            rep["scenes"][f"{sc}_{persp}"] = {"A_lufs": round(lufs(a * g, FS), 2), "B_lufs": round(lufs(b * g, FS), 2),
                                             "A_hf_transients": hf_transients(a), "B_hf_transients": hf_transients(b)}
            if persp == "ext":
                fig_pair(spec / f"scene_{sc}.png", [(f"scena {sc} A (main)", a * g), (f"scena {sc} B (0176)", b * g)])

    if not args.no_refs:
        panels = []
        for label, rel, st, du, _lic in REFS:
            p = MAIN_ROOT / rel
            if p.exists():
                panels.append((label, load(p, st, du)))
        if panels:
            fig_pair(spec / "references.png", panels)
            rep["references"] = [r[0] for r in REFS]

    (OUT / "checks.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")
    for k, v in rep["layers"].items():
        print(k, v)
    for r in rows:
        print(r)
    print(json.dumps(rep["scenes"], indent=0))


if __name__ == "__main__":
    main()
