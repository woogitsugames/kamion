"""Prepare the selected ElevenLabs files as game layers (ADR 0137).

    uv run python el_prepare.py [--src <dir>]

Input : the owner's raw files (<src>/<ID> (n).wav, 48 kHz stereo) + artifacts/audio-el/analysis/analysis.json
        (el_analyze.py) for the measured rpm of every engine loop.
Output: game/Assets/_Project/Audio/ElevenLabs/Clips/{engine/ext,engine/cab,ebrake/ext,ebrake/cab,sfx}/*.wav
        (48 kHz mono 16-bit, tracked in git via LFS) and game/Assets/_Project/Audio/ElevenLabs/el_manifest.json
        (same schema as tools/audio's manifest.json, + provenance) read by VehicleAudioImporter.

Engine grid: ElevenLabs ignores the rpm number in the prompt (all 96 loops sit at 40-75 Hz dominant line,
~800-1500 rpm equivalent). Every grid cell (perspective x load x nominal rpm) therefore takes the best *stable*
loop of that perspective/load from the whole pool, wherever its prompt rpm was, and resamples it to the nominal rpm.
Processing of a loop:
  1. mono downmix, 25 Hz high-pass (zero phase, applied circularly so the loop stays seamless)
  2. seam: last L=40 ms crossfaded (equal power) into the first L -> loop length N-L, continuous at the wrap
  3. periodic FFT resample N -> M = round(N * rpm_measured / rpm_nominal) (pitch to the nominal rpm, seam kept)
  4. loudness matched to the procedural bank cell of the same perspective/load/rpm (BS.1770 LUFS), so the mix
     constants of EngineAudio/TruckAudioController keep their meaning; peak checked < -1 dBFS.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal

from el_analyze import MAIN, comb_estimate, lufs, track
from el_regen01 import REGEN01, line_follow, prompt_entry
from el_sweepcut import MAX_LEN_S, choose_segment, flatten_level, smooth_track, stretch_psola, top_segment, warp_to_constant
from sfx_layers import cab_filter

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "game" / "Assets" / "_Project" / "Audio" / "ElevenLabs"
ANALYSIS = ROOT / "artifacts" / "audio-el" / "analysis" / "analysis.json"
ANALYSIS_R01 = ROOT / "artifacts" / "audio-regen01" / "analysis" / "regen01.json"  # el_regen01.py (ADR 0138)
REPORT = ROOT / "artifacts" / "audio-regen01" / "prepare.txt"
SYNTH = MAIN / "art-source" / "audio" / "generated"
FS = 48000
GRID = [600, 900, 1200, 1500, 1800, 2100]
SEAM_S = 0.040

# ---------------------------------------------------------------------------------------------------------------
# Authored choices (after reviewing artifacts/audio-el/analysis/sheets/*.png). None = automatic ranking.
# Overrides after the cross-check with the independent GPT review (artifacts/audio-el/COMPARE-GPT.md): the two sources
# it ranked least stable within their prompt ID (EXT_OFF_900 (4), CAB_OFF_1200 (4)) are replaced where a source it ranked
# first/steady exists at a usable pitch; CAB_OFF_1200 (4) stays only where its high pitch (1426 rpm) is needed.
ENGINE_PICK: dict[tuple[str, str, int], str | None] = {
    # ext/off 1800-2100 keep EXT_OFF_900 (4): the GPT pick EXT_OFF_1200 (2) has no usable firing line (its 20-120 Hz line
    # wanders 18.8 %, the strong 133 Hz line is ambiguous k=2/k=3) and failed el_verify pitch (> 4 %) when tried.
    # cab/off 1200/1500 were ENG_CAB_OFF_1800 (3) (GPT pick, 1218 rpm; line only ~8 dB, ADR 0148); since ADR 0156 they
    # are cut from REGEN-04 (el_regen04.CELLS, below)
}
# ADR 0138: rows cut from one REGEN-01 sweep (one machine, consistent timbre across the row) instead of picking loops.
# rise = (t0, t1, start band Hz, harmonic number of the followed line), steady = windows for targets outside the rise
# (idle before it). Windows authored from artifacts/audio-regen01/analysis/sheets/ENG_EXT_ON_SWEEP.png. Sweep = el_regen01
# rank 1: ENG_EXT_ON_SWEEP (4), 904->1772 rpm, monotonic 91 %, line 22.7 dB, period (YIN) = line in 100 % of 1 s chunks.
# (2)/(3) rise further but carry a constant ~46 Hz partial: their 1500/1800 cells are periodic an octave low (YIN 0.49/0.51).
# ENG_CAB_ON_SWEEP: no variant rises monotonically (25-77 %) with a consistent period, the cab/on row keeps picked loops.
LOOP_MIN_S = 3.6  # output loop length floor (> 3 s asserted by ElevenLabsEngineAudioTests, + seam crossfade margin)
SWEEP_ROWS: dict[tuple[str, str], dict] = {
    ("ext", "on"): {"file": "ENG_EXT_ON_SWEEP (4).wav", "rise": (9.0, 15.4, (40, 50), 1),
                    "steady": (5.0, 9.0, (36, 46), 1)},
}
EVENTS = {
    # name in game          : (source file, kind, target)  target = LUFS or "rel:<db>" relative to a synth clip
    "el_engine_start_ext": ("ENG_START_EXT (3).wav", "oneshot", -30.0),
    "el_engine_start_cab": ("ENG_START_CAB (3).wav", "oneshot", -33.0),
    "el_engine_stop_ext": ("ENG_STOP_EXT (3).wav", "oneshot", -33.0),
    "el_idle_clatter_loop": ("ENG_IDLE_CLATTER (2).wav", "loop", -40.0),
    "el_turbo_wastegate": ("TURBO_WASTEGATE (4).wav", "oneshot", "turbo_liftoff"),
    "el_retarder_loop": ("RETARDER_LOOP (1).wav", "loop", "retarder_loop"),
}
EBRAKE_SRC = "EXHAUST_BRAKE_LOOP (3).wav"
EBRAKE_GRID = [1000, 1400, 1800, 2200]
# ---------------------------------------------------------------------------------------------------------------


def mono(path: Path) -> np.ndarray:
    d, fs = sf.read(path, always_2d=True)
    assert fs == FS, (path, fs)
    return d.mean(axis=1)


def circular_hp(x: np.ndarray, fc: float = 25.0) -> np.ndarray:
    sos = signal.butter(2, fc, "hp", fs=FS, output="sos")
    n = len(x)
    y = signal.sosfiltfilt(sos, np.concatenate([x, x, x]))
    return y[n:2 * n]


def seam_loop(x: np.ndarray, seam_s: float = SEAM_S) -> np.ndarray:
    L = int(seam_s * FS)
    n = len(x)
    y = x[: n - L].copy()
    t = np.linspace(0, np.pi / 2, L, endpoint=False)
    y[:L] = x[:L] * np.sin(t) + x[n - L:] * np.cos(t)
    return y


def resample_periodic(x: np.ndarray, ratio: float) -> tuple[np.ndarray, float]:
    """ratio = f_new / f_old (pitch factor). Returns (y, exact ratio)."""
    n = len(x)
    m = int(round(n / ratio))
    return signal.resample(x, m), n / m


def fade(x: np.ndarray, fi: float, fo: float) -> np.ndarray:
    y = x.copy()
    a, b = int(fi * FS), int(fo * FS)
    if a:
        y[:a] *= np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    if b:
        y[-b:] *= np.cos(np.linspace(0, np.pi / 2, b)) ** 2
    return y


def trim_silence(x: np.ndarray, thr_db: float = -50.0) -> np.ndarray:
    env = np.convolve(np.abs(x), np.ones(240) / 240, "same")
    lim = np.max(env) * 10 ** (thr_db / 20)
    idx = np.where(env > lim)[0]
    a = max(0, idx[0] - int(0.01 * FS))
    b = min(len(x), idx[-1] + int(0.05 * FS))
    return x[a:b]


def to_lufs(x: np.ndarray, target: float) -> tuple[np.ndarray, float]:
    g = 10 ** ((target - lufs(x, FS)) / 20)
    return x * g, 20 * math.log10(g)


def soft_limit(x: np.ndarray, ceil_db: float = -1.0, knee: float = 0.6) -> tuple[np.ndarray, float]:
    """Memoryless soft knee above knee*ceiling (seam-safe for loops). Returns (y, peak reduction dB)."""
    c = 10 ** (ceil_db / 20)
    k = knee * c
    a = np.abs(x)
    if a.max() <= c:
        return x, 0.0
    over = a > k
    y = x.copy()
    y[over] = np.sign(x[over]) * (k + (c - k) * np.tanh((a[over] - k) / (c - k)))
    return y, 20 * math.log10(a.max() / np.abs(y).max())


def write(name: str, sub: str, x: np.ndarray) -> str:
    p = OUT / "Clips" / sub / f"{name}.wav"
    p.parent.mkdir(parents=True, exist_ok=True)
    pk = np.abs(x).max()
    if pk > 10 ** (-1 / 20):
        raise ValueError(f"{name}: peak {20 * math.log10(pk):.1f} dBFS > -1")
    sf.write(p, x.astype(np.float32), FS, subtype="PCM_16")
    return p.relative_to(ROOT).as_posix()


def synth_lufs() -> dict:
    man = json.loads((SYNTH / "manifest.json").read_text(encoding="utf-8"))
    out = {}
    for c in man["clips"]:
        if c["kind"] == "engine" and c["rpm"] in GRID and c["layer"] in ("off", "on"):
            out[(c["perspective"], c["layer"], c["rpm"])] = lufs(sf.read(SYNTH.parent.parent.parent / c["file"])[0], FS)
        if c["kind"] == "ebrake":
            out[("ebrake", c["perspective"], c["rpm"])] = lufs(sf.read(SYNTH.parent.parent.parent / c["file"])[0], FS)
    for s in man["sfx"]:
        out[("sfx", s["name"])] = lufs(sf.read(SYNTH.parent.parent.parent / s["file"])[0], FS)
    return out


_AMBIG: dict[str, float] = {}


def ladder_ambiguity(src: Path, r: dict) -> float:
    """Prominence (dB) of a line at 0.5x or 1.5x the dominant one: >= 6 dB means the ladder spacing (period) is half the
    dominant line, i.e. the loop would be heard an octave below the grid cell (ADR 0138). Cached per file."""
    if r["file"] not in _AMBIG:
        from el_analyze import prominence_db, welch_db
        f, pdb = welch_db(mono(src / r["file"]), FS)
        pr = prominence_db(f, pdb)
        df = f[1] - f[0]
        v = []
        for m in (0.5, 1.5):
            j = int(round(r["dom_hz"] * m / df))
            v.append(float(pr[max(0, j - 3): j + 4].max()))
        _AMBIG[r["file"]] = max(v)
    return _AMBIG[r["file"]]


def candidates(rows: list[dict], persp: str, load: str, src: Path | None = None) -> list[dict]:
    """Stable, clearly tonal loops of one perspective/load (any prompt rpm)."""
    out = []
    for r in rows:
        if r.get("persp") != persp or r.get("load") != load:
            continue
        span = (r["rpm_max"] - r["rpm_min"]) / r["rpm_med"]
        # seam is re-made by seam_loop(), so the raw seam only screens gross faults; span = 1 s tracking of a weak
        # line is noisy, 15 % still means a held note (sheets reviewed)
        # ADR 0138: range widened for the REGEN-01 high/slow-idle loops; level-unstable (revving) loops excluded
        ok = (r["dom_prom_db"] >= 9 and span <= 0.15 and r["seam_jump_ratio"] < 1.0
              and abs(r["drift_db"]) < 3 and 580 <= r["rpm_med"] <= 2000 and r.get("level_range_db", 0.0) <= 8)
        if ok and src is not None and ladder_ambiguity(src, r) >= 6.0:
            ok = False
        if ok:
            out.append(dict(r, span=span))
    return out


def score(c: dict, target: int) -> float:
    shift = abs(math.log2(target / c["rpm_med"]))
    return 2.0 * c["ladder_n"] + c["dom_prom_db"] / 4 - 60 * c["span"] - 14 * shift - 40 * max(0.0, shift - 0.6)


def sweep_cell(src: Path, cfg: dict, rpm: int) -> tuple[np.ndarray, dict]:
    """One grid cell cut from a sweep (el_sweepcut). Inside the rise: flattened segment around rpm. Above it: the top
    of the rise, flattened and shifted up. Below it: the authored steady (idle) window, flattened and shifted down."""
    sos = signal.butter(2, 25.0, "hp", fs=FS, output="sos")
    x = signal.sosfiltfilt(sos, mono(src / cfg["file"]))
    f_t = rpm / 20.0
    t0, t1, band, k = cfg["rise"]
    tr = line_follow(x, FS, t0, t1, band)
    t, fsm = tr["t"], smooth_track(tr["t"], tr["f0"] / k)
    seg, kind = choose_segment(t, fsm, f_t), "rise"
    if seg is None and f_t > fsm.max():
        seg, kind = top_segment(t, fsm), "top"
    if seg is None:
        s0, s1, sband, sk = cfg["steady"]
        st = line_follow(x, FS, s0, s1, sband, fixed=True)
        t, fsm = st["t"], smooth_track(st["t"], st["f0"] / sk)
        mid, half = 0.5 * (s0 + s1), min(MAX_LEN_S, s1 - s0) / 2
        seg, kind = (max(mid - half, float(t[0])), min(mid + half, float(t[-1]))), "steady"
    y, info = warp_to_constant(x, FS, t, fsm, seg[0], seg[1], f_t)
    y, info["level_flatten_db"] = flatten_level(y, FS)
    info["stretch"] = 1.0
    if len(y) < int(LOOP_MIN_S * FS):  # fast part of the sweep: PSOLA-stretch to a loop that is not heard as a loop
        info["stretch"] = LOOP_MIN_S * FS / len(y)
        y = stretch_psola(y, FS, f_t, int(LOOP_MIN_S * FS))
    info["segment_kind"] = kind
    return seam_loop(y), info


def main() -> None:
    from el_regen04 import CELLS as R04_CELLS, cut_cell as r04_cut, prompt_entry as r04_prompt  # noqa: N811
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(MAIN / "art-source" / "audio" / "elevenlabs"))
    a = ap.parse_args()
    src = Path(a.src)
    rows = [r for r in json.loads(ANALYSIS.read_text(encoding="utf-8")) if "error" not in r]
    if ANALYSIS_R01.exists():
        rows += [r for r in json.loads(ANALYSIS_R01.read_text(encoding="utf-8")) if "persp" in r]
    gen = json.loads((src / "generation-manifest.json").read_text(encoding="utf-8"))
    prompt_of = {g["id"]: g for g in gen}
    prompt_of.update({k: prompt_entry(k) for k in REGEN01})
    ref = synth_lufs()
    clips, sfx, report = [], [], []
    for persp_up, persp in (("EXT", "ext"), ("CAB", "cab")):
        for load_up, layer, load in (("OFF", "off", 0.0), ("ON", "on", 1.0)):
            cands = candidates(rows, persp_up, load_up, src)
            prev = None
            for rpm in GRID:
                cfg = SWEEP_ROWS.get((persp, layer))
                if cfg:
                    y, info = sweep_cell(src, cfg, rpm)
                    target = ref[(persp, layer, rpm)]
                    y, gain = to_lufs(y, target)
                    y, lim = soft_limit(y)
                    name = f"el_engine_{persp}_{layer}_{rpm:04d}"
                    f = write(name, f"engine/{persp}", y)
                    cycles = max(1, int(round(len(y) / FS * rpm / 120)))
                    clips.append({"name": name, "file": f, "kind": "engine", "perspective": persp, "rpm": rpm, "layer": layer,
                                  "load": load, "rpm_exact": float(rpm), "cycles": cycles, "samples": len(y),
                                  "source": cfg["file"], "source_rpm_measured": info["rpm_measured_mean"],
                                  "pitch_ratio": rpm / info["rpm_measured_mean"], "gain_db": gain, "target_lufs": target,
                                  "limit_db": lim, "lufs": lufs(y, FS), "source_prompt_id": cfg["file"].split(" (")[0],
                                  "sweep_segment": info})
                    report.append(f"{name:28s} <- {cfg['file']:28s} {info['segment_kind']:6s} {info['seg_t0']:5.2f}-{info['seg_t1']:5.2f} s "
                                  f"measured {info['rpm_measured_mean']:6.0f} rpm  warp {info['warp_min']:.3f}-{info['warp_max']:.3f}  "
                                  f"level flat {info['level_flatten_db']:.1f} dB  stretch x{info['stretch']:.2f}  "
                                  f"{gain:+.1f} dB -> {target:.1f} LUFS  limit {lim:.1f} dB")
                    continue
                if (persp, layer) == ("cab", "off") and rpm in R04_CELLS:  # ADR 0156: REGEN-04 steady cab take
                    take, w0, w1, band = R04_CELLS[rpm]
                    y, info = r04_cut(src, take, w0, w1, band, rpm)
                    target = ref[(persp, layer, rpm)]
                    y, gain = to_lufs(y, target)
                    y, lim = soft_limit(y)
                    name = f"el_engine_{persp}_{layer}_{rpm:04d}"
                    f = write(name, f"engine/{persp}", y)
                    seg = {k: info[k] for k in ("seg_t0", "seg_t1", "seg_len_s", "warp_min", "warp_max", "rpm_measured_mean",
                                                "level_flatten_db", "stretch")}
                    seg.update({"segment_kind": "steady", "batch": "REGEN-04"})
                    clips.append({"name": name, "file": f, "kind": "engine", "perspective": persp, "rpm": rpm, "layer": layer,
                                  "load": load, "rpm_exact": float(rpm), "cycles": max(1, int(round(len(y) / FS * rpm / 120))),
                                  "samples": len(y), "source": take, "source_rpm_measured": info["rpm_measured_mean"],
                                  "pitch_ratio": rpm / info["rpm_measured_mean"], "gain_db": gain, "target_lufs": target,
                                  "limit_db": lim, "lufs": lufs(y, FS), "source_prompt_id": take.split(" (")[0],
                                  "sweep_segment": seg})
                    prompt_of[take.split(" (")[0]] = r04_prompt(take.split(" (")[0])
                    report.append(f"{name:28s} <- {take:28s} steady {w0:5.2f}-{w1:5.2f} s measured {info['rpm_measured_mean']:6.0f} rpm  "
                                  f"warp {info['warp_min']:.3f}-{info['warp_max']:.3f}  {gain:+.1f} dB -> {target:.1f} LUFS  limit {lim:.1f} dB")
                    prev = take
                    continue
                pick = ENGINE_PICK.get((persp, layer, rpm))
                if pick:
                    c = next(r for r in rows if r["file"] == pick)
                    c = dict(c, span=(c["rpm_max"] - c["rpm_min"]) / c["rpm_med"])
                else:
                    ranked = sorted(cands, key=lambda c: score(c, rpm) - (3 if prev and c["file"] == prev else 0), reverse=True)
                    c = ranked[0]
                prev = c["file"]
                x = circular_hp(mono(src / c["file"]))
                x = seam_loop(x)
                ratio = rpm / c["rpm_med"]
                y, exact = resample_periodic(x, ratio)
                rpm_exact = c["rpm_med"] * exact
                target = ref[(persp, layer, rpm)]
                y, gain = to_lufs(y, target)
                y, lim = soft_limit(y)
                name = f"el_engine_{persp}_{layer}_{rpm:04d}"
                f = write(name, f"engine/{persp}", y)
                cycles = max(1, int(round(len(y) / FS * rpm_exact / 120)))
                clips.append({"name": name, "file": f, "kind": "engine", "perspective": persp, "rpm": rpm, "layer": layer,
                              "load": load, "rpm_exact": rpm_exact, "cycles": cycles, "samples": len(y),
                              "source": c["file"], "source_rpm_measured": c["rpm_med"], "pitch_ratio": exact,
                              "gain_db": gain, "target_lufs": target, "limit_db": lim, "lufs": lufs(y, FS), "source_prompt_id": c["id"]})
                report.append(f"{name:28s} <- {c['file']:28s} measured {c['rpm_med']:6.0f} rpm  x{exact:.3f}  "
                              f"span {100 * c['span']:.1f}%  {gain:+.1f} dB -> {target:.1f} LUFS  limit {lim:.1f} dB")
    # engine (exhaust) brake: one source, resampled to a small rpm grid, both perspectives
    next(r for r in rows if r["file"] == EBRAKE_SRC)
    xe = circular_hp(mono(src / EBRAKE_SRC))
    c = comb_estimate(xe, FS)
    fd = 72.5 if abs(c["comb_f"] - 72.5) > 3 else c["comb_f"]
    tr = track(xe, FS, fd, c["_f"], c["_prom"], force_k=1)
    eb_rpm = tr["rpm_med"]
    xe = seam_loop(xe)
    for rpm in EBRAKE_GRID:
        y, exact = resample_periodic(xe, rpm / eb_rpm)
        for persp in ("ext", "cab"):
            z = y if persp == "ext" else cab_filter(y, True, "mech")
            key = ("ebrake", persp, min(max(rpm, 900), 2100) // 100 * 100)
            target = ref.get(key, ref[("ebrake", persp, 1500)])
            z, gain = to_lufs(z, target)
            z, _ = soft_limit(z)
            name = f"el_ebrake_{persp}_{rpm:04d}"
            f = write(name, f"ebrake/{persp}", z)
            clips.append({"name": name, "file": f, "kind": "ebrake", "perspective": persp, "rpm": rpm, "layer": None,
                          "load": 0.0, "rpm_exact": eb_rpm * exact, "cycles": max(1, int(round(len(z) / FS * eb_rpm * exact / 120))),
                          "samples": len(z), "source": EBRAKE_SRC, "source_rpm_measured": eb_rpm, "pitch_ratio": exact,
                          "gain_db": gain, "target_lufs": target, "source_prompt_id": "EXHAUST_BRAKE_LOOP"})
            report.append(f"{name:28s} <- {EBRAKE_SRC:28s} measured {eb_rpm:6.0f} rpm  x{exact:.3f}  {gain:+.1f} dB")
    # events
    for name, (file, kind, target) in EVENTS.items():
        x = mono(src / file)
        if kind == "loop":
            x = seam_loop(circular_hp(x))
        else:
            x = fade(trim_silence(signal.sosfiltfilt(signal.butter(2, 25, "hp", fs=FS, output="sos"), x)), 0.003, 0.08)
        t = ref[("sfx", target)] if isinstance(target, str) else target
        y, gain = to_lufs(x, t)
        pk = np.abs(y).max()
        if pk > 10 ** (-1.5 / 20):  # short transients: LUFS target may overshoot the peak, limit by gain
            y *= 10 ** (-1.5 / 20) / pk
            gain += 20 * math.log10(10 ** (-1.5 / 20) / pk)
        f = write(name, "sfx", y)
        sfx.append({"name": name, "file": f, "loop": kind == "loop", "samples": len(y), "source": file,
                    "gain_db": gain, "lufs": lufs(y, FS), "source_prompt_id": file.split(" (")[0]})
        # cab perspective of the exterior-only events (prerendered, ADR 0017)
        if name in ("el_engine_stop_ext", "el_turbo_wastegate", "el_retarder_loop", "el_idle_clatter_loop"):
            prof = {"el_engine_stop_ext": "mech", "el_turbo_wastegate": "pneu", "el_retarder_loop": "mech", "el_idle_clatter_loop": "mech"}[name]
            z = cab_filter(y, kind == "loop", prof)
            cname = {"el_engine_stop_ext": "el_engine_stop_cab", "el_turbo_wastegate": "el_turbo_wastegate_cab",
                     "el_retarder_loop": "el_retarder_cab_loop", "el_idle_clatter_loop": "el_idle_clatter_cab_loop"}[name]
            f = write(cname, "sfx", z)
            sfx.append({"name": cname, "file": f, "loop": kind == "loop", "samples": len(z), "source": file,
                        "gain_db": gain, "lufs": lufs(z, FS), "source_prompt_id": file.split(" (")[0], "cab_filter": prof})
        report.append(f"{name:28s} <- {file:28s} {gain:+.1f} dB")
    used = sorted({c["source_prompt_id"] for c in clips} | {s["source_prompt_id"] for s in sfx})
    man = {
        "generator": "ElevenLabs Sound Effects v3 (owner, ElevenCreative Pro, 2026-11-12) -> tools/audio/el_prepare.py",
        "sample_rate": FS, "rpm_grid": GRID, "ebrake_rpm_grid": EBRAKE_GRID,
        "load_layers": {"off": 0.0, "on": 1.0}, "clips": clips, "sfx": sfx,
        "prompts": {k: prompt_of[k] for k in used if k in prompt_of},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    mp = OUT / "el_manifest.json"
    if mp.exists():  # keep the effects written by el_fx.py (ADR 0142)
        old = json.loads(mp.read_text(encoding="utf-8"))
        fx = [s for s in old.get("sfx", []) if s.get("group") == "fx"]
        man["sfx"] += fx
        for s in fx:
            if s["source_prompt_id"] in old.get("prompts", {}):
                man["prompts"][s["source_prompt_id"]] = old["prompts"][s["source_prompt_id"]]
        if "fx_generator" in old:
            man["fx_generator"] = old["fx_generator"]
    mp.write_text(json.dumps(man, indent=1), encoding="utf-8")
    rep = REPORT
    rep.parent.mkdir(parents=True, exist_ok=True)
    rep.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
