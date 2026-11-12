"""ElevenLabs REGEN-04 (docs/owner/ELEVENLABS-REGEN-04.md, ADR 0156): cab engine without load (overrun / idle).

    uv run python el_regen04.py analyse [--src <dir>]     # all 8 takes: track, plateaus, line dB, clicks -> json/csv/sheets
    uv run python el_regen04.py cut [--src <dir>]         # replace the cab/off cells listed in CELLS (manifest + clips)

Takes: ENG_CAB_OVERRUN_SWEEP (1)-(4) and ENG_CAB_IDLE_STEADY (1)-(4), 12 s, 48 kHz stereo (owner, 2026-11-12, v3).

analyse, per take
  track       Viterbi salience track of the strongest harmonic ladder (el_regen01.salience_track, 15-140 Hz, 0.6 s / 0.1 s)
  sweep       the asked shape is one slow monotonic fall: fall_frac = share of frames with track <= 1.01 x running min
              from the first frame (1 = monotonic fall), rpm start / end / max (rpm = line x 20, R6 firing convention, ADR 0137)
  plateaus    maximal windows >= PLAT_MIN_S where the track stays within +-PLAT_TOL of its window median; per plateau:
              rpm, line_db (prominence of the line at the median frequency over a +-25 Hz running median of the Welch
              spectrum; the metric of the grid cells below), YIN period / line ratio (octave check, ADR 0138), level std,
              clicks inside
  clicks      broadband transients: 5 ms energy above 4 kHz more than CLICK_DB over its 0.5 s running median
  level       std / range of 250 ms RMS (dB), peak, clipped samples, LUFS

line_db(cell) = same prominence at rpm/20 (+-3 %) of a grid loop (loop played twice). ADR 0148 reported 7.5-7.7 dB for
cab/off 1200/1500 with an older run of this measure; on the clips of main this script gives 8.2 / 8.9 dB (both listed).

cut: every cell in CELLS is cut from the authored window of its take like el_prepare.sweep_cell (line_follow inside the
window, el_sweepcut.warp_to_constant flattens the followed line onto rpm/20, flatten_level, PSOLA stretch if shorter
than LOOP_MIN_S, 40 ms seam), loudness-matched to the procedural cell (BS.1770) like every other cell, and written over
game/Assets/_Project/Audio/ElevenLabs/Clips/engine/cab/el_engine_cab_off_<rpm>.wav; its el_manifest.json entry is
replaced (provenance: source, window, warp, prompt REGEN-04). All other cells and effects stay byte-identical.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402
from scipy import signal  # noqa: E402
from scipy.ndimage import median_filter  # noqa: E402

from el_analyze import MAIN, db, lufs, prominence_db, seam, welch_db, yin_f0  # noqa: E402
from el_regen01 import common, line_follow, salience_track  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "artifacts" / "audio-regen04"
SRC = MAIN / "art-source" / "audio" / "elevenlabs"
FS = 48000
IDS = ["ENG_CAB_OVERRUN_SWEEP", "ENG_CAB_IDLE_STEADY"]
PLAT_TOL, PLAT_MIN_S = 0.05, 2.0
CLICK_DB = 15.0

_SET = {"batch": "REGEN-04", "model": "v3", "duration": 12, "influence": 80, "loop": False, "variants": 4,
        "generated": "2026-11-12", "plan": "ElevenCreative Pro"}
PROMPTS = {
    "ENG_CAB_OVERRUN_SWEEP": "Inside the closed cab of a heavy truck rolling down a gentle slope in a high gear with the driver's foot completely off the accelerator: the inline-six diesel is driven by the wheels with no fuel, engine speed falls slowly and smoothly from medium revs to just above idle over the whole clip, a clear steady low engine hum with distinct firing pulses heard through the floor, soft and light, no acceleration, no gear change, no exhaust brake, no road noise, no music, no voices",
    "ENG_CAB_IDLE_STEADY": "Inside the closed cab of a stationary heavy truck, the inline-six diesel idling smoothly and evenly, a clear low regular throb from the engine through the floor and seat, every firing pulse even, faint injector ticking, no air compressor, no air hiss, no revving, no road noise, no music, no voices",
}


def prompt_entry(pid: str) -> dict:
    return {"id": pid, "prompt": PROMPTS[pid], **_SET}


# ------------------------------------------------------------------------------------------------------- measures
def line_db_at(x: np.ndarray, fs: int, f_line: float, tol: float = 0.03) -> float:
    """Prominence (dB over the +-25 Hz running median of the Welch spectrum) of the strongest bin within +-tol of f_line."""
    f, p = welch_db(x, fs)
    pr = prominence_db(f, p)
    k = (f > f_line * (1 - tol)) & (f < f_line * (1 + tol))
    return float(pr[k].max())


def cell_line_db(x: np.ndarray, fs: int, rpm: float) -> float:
    return line_db_at(np.tile(x, 2), fs, rpm / 20.0)


def clicks(x: np.ndarray, fs: int) -> list[float]:
    sos = signal.butter(4, 4000, "hp", fs=fs, output="sos")
    h = signal.sosfiltfilt(sos, x) ** 2
    w = int(0.005 * fs)
    n = len(h) // w
    e = 10 * np.log10(h[:n * w].reshape(n, w).mean(1) + 1e-20)
    base = median_filter(e, int(0.5 / 0.005) | 1, mode="nearest")
    hits = np.where(e - base > CLICK_DB)[0]
    out, last = [], -1e9
    for i in hits:
        t = i * 0.005
        if t - last > 0.05:
            out.append(round(t, 3))
        last = t
    return out


def plateaus(t: np.ndarray, f: np.ndarray) -> list[tuple[int, int]]:
    """Greedy maximal windows (frame index l..r) where |f / median - 1| <= PLAT_TOL, length >= PLAT_MIN_S."""
    dt = t[1] - t[0]
    out, i = [], 0
    n = len(f)
    while i < n:
        best = None
        for r in range(n - 1, i, -1):
            m = np.median(f[i:r + 1])
            if np.all(np.abs(f[i:r + 1] / m - 1) <= PLAT_TOL):
                best = r
                break
        if best is not None and (best - i) * dt >= PLAT_MIN_S:
            out.append((i, best))
            i = best + 1
        else:
            i += 1
    return out


def env_db(x: np.ndarray, fs: int, win_s: float = 0.25) -> np.ndarray:
    w = int(win_s * fs)
    return np.array([db(float(np.sqrt(np.mean(x[i:i + w] ** 2)))) for i in range(0, len(x) - w + 1, w)])


def analyse_take(path: Path) -> tuple[dict, dict]:
    r, x, fs = common(path)
    r.update(seam(x, fs))
    tr = salience_track(x, fs)
    t, f = tr["t"], tr["f0"]
    rpm = f * 20
    sm = signal.savgol_filter(rpm, 11, 2)
    runmin = np.minimum.accumulate(sm)
    r.update({"rpm_start": float(np.median(rpm[:10])), "rpm_end": float(np.median(rpm[-10:])), "rpm_max": float(rpm.max()),
              "rpm_min": float(rpm.min()), "t_rpm_max": float(t[int(np.argmax(rpm))]),
              "fall_frac": float(np.mean(sm <= 1.01 * runmin)), "track_sal_med": float(np.median(tr["sal"]))})
    cl = clicks(x, fs)
    r["clicks"] = cl
    r["n_clicks"] = len(cl)
    pl = []
    for l, rr in plateaus(t, f):
        t0, t1 = float(t[l] - 0.3), float(t[rr] + 0.3)
        t0, t1 = max(0.0, t0), min(len(x) / fs, t1)
        seg = x[int(t0 * fs):int(t1 * fs)]
        fm = float(np.median(f[l:rr + 1]))
        fy, ap = yin_f0(seg, fs)
        e = env_db(seg, fs)
        pl.append({"t0": round(t0, 2), "t1": round(t1, 2), "dur_s": round(t1 - t0, 2), "rpm": round(fm * 20),
                   "line_db": round(line_db_at(seg, fs, fm), 1), "line2_db": round(line_db_at(seg, fs, 2 * fm), 1),
                   "yin_ratio": round(fy / fm, 2), "yin_ap": round(ap, 2), "level_std_db": round(float(np.std(e)), 2),
                   "rms_dbfs": round(db(float(np.sqrt(np.mean(seg ** 2)))), 1),
                   "clicks": [c for c in cl if t0 <= c <= t1]})
    r["plateaus"] = pl
    return r, tr


def sheet(fid: str, rows: list[dict], tracks: dict, src: Path, out: Path) -> None:
    rr = [r for r in rows if r["id"] == fid]
    fig, axs = plt.subplots(2, len(rr), figsize=(5 * len(rr), 7), squeeze=False, gridspec_kw={"height_ratios": [3, 1]})
    for j, r in enumerate(rr):
        x = sf.read(src / r["file"], always_2d=True)[0].mean(1)
        f, t, S = signal.spectrogram(x, FS, nperseg=1 << 14, noverlap=(1 << 14) * 7 // 8)
        k = f <= 400
        L = 10 * np.log10(S[k] + 1e-20)
        ax = axs[0, j]
        ax.pcolormesh(t, f[k], L, shading="auto", cmap="magma", vmin=L.max() - 60)
        tr = tracks[r["file"]]
        ax.plot(tr["t"], tr["f0"], color="cyan", lw=0.8)
        for p in r["plateaus"]:
            ax.axvspan(p["t0"], p["t1"], ymin=0, ymax=0.03, color="lime")
            ax.text(p["t0"], 380, f"{p['rpm']} rpm\n{p['line_db']} dB", color="w", fontsize=7, va="top")
        for c in r["clicks"]:
            ax.axvline(c, color="r", lw=0.6, ls="--")
        for g in (900, 1200, 1500):
            ax.axhline(g / 20, color="w", lw=0.4, ls=":")
        ax.set_title(f"{r['file']}  fall {100 * r['fall_frac']:.0f} %  clicks {r['n_clicks']}", fontsize=8)
        ax.set_ylabel("Hz (dotted: 900/1200/1500 rpm / 20)", fontsize=7)
        axs[1, j].plot(np.arange(len(x)) / FS, x, lw=0.3)
        axs[1, j].set_ylim(-0.5, 0.5)
        axs[1, j].set_xlabel("s", fontsize=7)
    fig.tight_layout()
    fig.savefig(out / f"{fid}.png", dpi=60)
    plt.close(fig)


def cmd_analyse(src: Path) -> None:
    out = ART / "analysis"
    out.mkdir(parents=True, exist_ok=True)
    rows, tracks = [], {}
    for fid in IDS:
        for v in (1, 2, 3, 4):
            p = src / f"{fid} ({v}).wav"
            r, tr = analyse_take(p)
            rows.append(r)
            tracks[p.name] = tr
            print(f"{p.name:32s} lufs {r['lufs']:6.1f} pk {r['peak_dbfs']:5.1f} clip {r['clips']}  rpm {r['rpm_start']:5.0f}->"
                  f"{r['rpm_end']:5.0f} (max {r['rpm_max']:5.0f} @ {r['t_rpm_max']:.1f} s, min {r['rpm_min']:5.0f})  "
                  f"fall {100 * r['fall_frac']:3.0f} %  sal {r['track_sal_med']:4.1f}  clicks {r['clicks']}")
            for pl in r["plateaus"]:
                print(f"    plateau {pl['t0']:5.2f}-{pl['t1']:5.2f} s  {pl['rpm']:5d} rpm  line {pl['line_db']:5.1f} dB  2x {pl['line2_db']:5.1f}  "
                      f"yin {pl['yin_ratio']:.2f} ap {pl['yin_ap']:.2f}  lvl std {pl['level_std_db']:.2f}  rms {pl['rms_dbfs']}  clicks {pl['clicks']}")
    (out / "regen04.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    flat = []
    for r in rows:
        for pl in r["plateaus"] or [{}]:
            flat.append({"file": r["file"], "lufs": round(r["lufs"], 1), "peak_dbfs": round(r["peak_dbfs"], 1),
                         "rpm_start": round(r["rpm_start"]), "rpm_end": round(r["rpm_end"]), "rpm_max": round(r["rpm_max"]),
                         "fall_frac": round(r["fall_frac"], 2), "n_clicks": r["n_clicks"],
                         **{f"pl_{k}": v for k, v in pl.items() if k != "clicks"}})
    with open(out / "regen04.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, sorted({k for f in flat for k in f}, key=lambda k: (k != "file", k)))
        w.writeheader()
        w.writerows(flat)
    for fid in IDS:
        sheet(fid, rows, tracks, src, out)


# ------------------------------------------------------------------------------------------------------- cut
# Authored after artifacts/audio-regen04/analysis (sheets + regen04.json) and `cut --dry` (candidate table):
# cell rpm -> (take, window t0-t1 s, line band Hz searched in every frame). None of the four OVERRUN_SWEEP takes falls
# monotonically (rise to 1750-2000 rpm, then a 1.5 s drop to a ~900 rpm plateau), so the steady IDLE takes are cut.
# Pick (artifacts/audio-regen04/cut/dry.txt): IDLE_STEADY (4) is a steady 1467 rpm cab take with a 20 dB line and a
# consistent period (YIN 0.95); both weak cells come from it (warp x0.81-0.85 / x1.01-1.06). Alternatives: 1200 from
# IDLE_STEADY (3) has 17.7 dB and a 5.1 dB timbre step to the 900 cell (IDLE (4): 3.1 dB). 600/900 keep their sources
# (21.2 / 22.3 dB, no candidate is better). Steps 1200-1500 3.5 dB (was 3.55), 1500-1800 3.6 dB (was 2.8).
CELLS: dict[int, tuple[str, float, float, tuple[float, float]]] = {
    1200: ("ENG_CAB_IDLE_STEADY (4).wav", 1.75, 8.25, (66, 80)),
    1500: ("ENG_CAB_IDLE_STEADY (4).wav", 1.75, 8.25, (66, 80)),
}
# windows from `scan` (best 6.5 s: 2 x level std - line dB, no clicks); OVERRUN (4): its ~900 rpm plateau after the drop
CANDIDATES: list[tuple[int, str, float, float, tuple[float, float]]] = [
    (600, "ENG_CAB_IDLE_STEADY (1).wav", 0.0, 6.5, (34, 42)),
    (900, "ENG_CAB_IDLE_STEADY (1).wav", 0.0, 6.5, (34, 42)),
    (900, "ENG_CAB_IDLE_STEADY (3).wav", 1.0, 7.5, (46, 56)),
    (900, "ENG_CAB_OVERRUN_SWEEP (4).wav", 7.1, 11.9, (40, 50)),
    (1200, "ENG_CAB_IDLE_STEADY (3).wav", 1.0, 7.5, (46, 56)),
    (1200, "ENG_CAB_IDLE_STEADY (4).wav", 1.75, 8.25, (66, 80)),
    (1500, "ENG_CAB_IDLE_STEADY (4).wav", 1.75, 8.25, (66, 80)),
]
WIN_S = 6.5


def scan_window(x: np.ndarray, f_line: float, t_lo: float, t_hi: float, win_s: float = WIN_S) -> tuple[float, float, dict]:
    """Best win_s window inside [t_lo, t_hi]: cost = 2 x level std (250 ms, dB) - line_db, clicks excluded."""
    cl = clicks(x, FS)
    best = None
    for t0 in np.arange(t_lo, max(t_lo, t_hi - win_s) + 1e-6, 0.25):
        t1 = t0 + win_s
        if any(t0 <= c <= t1 for c in cl):
            continue
        seg = x[int(t0 * FS):int(t1 * FS)]
        ld = line_db_at(seg, FS, f_line, 0.05)
        sd = float(np.std(env_db(seg, FS)))
        c = 2 * sd - ld
        if best is None or c < best[0]:
            best = (c, float(t0), float(t1), {"line_db": round(ld, 1), "level_std_db": round(sd, 2)})
    return best[1], best[2], best[3]


def cut_cell(src: Path, take: str, t0: float, t1: float, band: tuple[float, float], rpm: int) -> tuple[np.ndarray, dict]:
    from el_prepare import LOOP_MIN_S, mono, seam_loop
    from el_sweepcut import flatten_level, smooth_track, stretch_psola, warp_to_constant
    sos = signal.butter(2, 25.0, "hp", fs=FS, output="sos")
    x = signal.sosfiltfilt(sos, mono(src / take))
    tr = line_follow(x, FS, max(0.0, t0 - 0.2), min(len(x) / FS, t1 + 0.2), band, fixed=True)
    t, fsm = tr["t"], smooth_track(tr["t"], tr["f0"])
    y, info = warp_to_constant(x, FS, t, fsm, t0, t1, rpm / 20.0)
    y, info["level_flatten_db"] = flatten_level(y, FS)
    info["stretch"] = 1.0
    if len(y) < int(LOOP_MIN_S * FS):
        info["stretch"] = LOOP_MIN_S * FS / len(y)
        y = stretch_psola(y, FS, rpm / 20.0, int(LOOP_MIN_S * FS))
    info["line_sal_med_db"] = float(np.median(tr["sal"]))
    return seam_loop(y), info


def band_steps(cells: dict[int, np.ndarray]) -> dict:
    from el_verify import band_levels
    ks = sorted(cells)
    bl = {k: band_levels(cells[k], FS) for k in ks}
    return {f"{a}-{b}": round(float(np.mean(np.abs(bl[b] - bl[a]))), 2) for a, b in zip(ks, ks[1:])}


def manifest_path(root: Path = ROOT) -> Path:
    return root / "game" / "Assets" / "_Project" / "Audio" / "ElevenLabs" / "el_manifest.json"


def current_cells(root: Path = ROOT) -> tuple[dict, dict[int, np.ndarray], dict[int, str]]:
    man = json.loads(manifest_path(root).read_text(encoding="utf-8"))
    cells = {c["rpm"]: c for c in man["clips"] if c["kind"] == "engine" and c["perspective"] == "cab" and c["layer"] == "off"}
    return man, {r: sf.read(root / c["file"])[0] for r, c in cells.items()}, {r: c["source"] for r, c in cells.items()}


def cell_row(x: np.ndarray, rpm: int) -> dict:
    fy, ap = yin_f0(x, FS)
    return {"line_db": round(cell_line_db(x, FS, rpm), 1), "yin_ratio": round(fy / (rpm / 20), 2), "yin_ap": round(ap, 2),
            "lufs": round(lufs(x, FS), 1), "len_s": round(len(x) / FS, 2)}


def cmd_cut(src: Path, dry: bool) -> None:
    from el_prepare import soft_limit, synth_lufs, to_lufs, write
    out = ART / "cut"
    out.mkdir(parents=True, exist_ok=True)
    man, cur, cur_src = current_cells()
    ref = synth_lufs()
    lines = ["current cab/off cells: line_db at rpm/20 (loop x2), YIN period / line, LUFS, source"]
    for r, x in sorted(cur.items()):
        lines.append(f"  {r:5d}  {cell_row(x, r)}  src {cur_src[r]}")
    lines.append("timbre steps (mean |d| 1/3-oct, dB): " + json.dumps(band_steps(cur)))
    todo = CANDIDATES if dry else [(r, *v) for r, v in CELLS.items()]
    made, infos = {}, {}
    for rpm, take, t0, t1, band in todo:
        y, info = cut_cell(src, take, t0, t1, band, rpm)
        y, gain = to_lufs(y, ref[("cab", "off", rpm)])
        y, lim = soft_limit(y)
        info.update({"gain_db": gain, "limit_db": lim, **cell_row(y, rpm), "seam": seam(y, FS)})
        key = (rpm, take, t0)
        made[key], infos[key] = y, info
        lines.append(f"  cand {rpm:5d} <- {take:30s} {t0:5.2f}-{t1:5.2f} s  measured {info['rpm_measured_mean']:6.0f} rpm  "
                     f"warp {info['warp_min']:.3f}-{info['warp_max']:.3f}  flat {info['level_flatten_db']:.1f} dB  "
                     f"line {info['line_db']:5.1f} dB  yin {info['yin_ratio']:.2f} ap {info['yin_ap']:.2f}  "
                     f"{info['lufs']:6.1f} LUFS ({gain:+.1f} dB, limit {lim:.1f})  seam {info['seam']['seam_jump_ratio']:.2f} / "
                     f"{info['seam']['seam_hf_spike_db']:.1f} dB  len {info['len_s']:.2f} s")
        tag = take.replace(" ", "").replace(".wav", "").replace("(", "_").replace(")", "")
        sf.write(out / f"cand_{rpm}_{tag}_{t0:.2f}.wav", np.tile(y, 2).astype(np.float32), FS, subtype="PCM_16")
    if dry:
        import itertools
        rpms = sorted({k[0] for k in made})
        opts = [[k for k in made if k[0] == r] + [None] for r in rpms]
        for combo in itertools.product(*opts):
            cells = dict(cur)
            for k in combo:
                if k is not None:
                    cells[k[0]] = made[k]
            tag = ", ".join(f"{r}:{k[1].split('(')[0][8:12]}{k[1][-6:-5]}@{k[2]}" if k else f"{r}:keep" for r, k in zip(rpms, combo))
            lines.append(f"  steps [{tag}] " + json.dumps(band_steps(cells)))
    else:
        for key, y in made.items():
            rpm, take, t0 = key
            info = infos[key]
            name = f"el_engine_cab_off_{rpm:04d}"
            f = write(name, "engine/cab", y)
            pid = take.split(" (")[0]
            seg = {k: info[k] for k in ("seg_t0", "seg_t1", "seg_len_s", "warp_min", "warp_max", "rpm_measured_mean",
                                        "level_flatten_db", "stretch")}
            seg.update({"segment_kind": "steady", "batch": "REGEN-04"})
            entry = {"name": name, "file": f, "kind": "engine", "perspective": "cab", "rpm": rpm, "layer": "off", "load": 0.0,
                     "rpm_exact": float(rpm), "cycles": max(1, int(round(len(y) / FS * rpm / 120))), "samples": len(y),
                     "source": take, "source_rpm_measured": info["rpm_measured_mean"],
                     "pitch_ratio": rpm / info["rpm_measured_mean"], "gain_db": info["gain_db"],
                     "target_lufs": ref[("cab", "off", rpm)], "limit_db": info["limit_db"], "lufs": lufs(y, FS),
                     "source_prompt_id": pid, "sweep_segment": seg}
            i = next(i for i, c in enumerate(man["clips"]) if c["name"] == name)
            man["clips"][i] = entry
            man["prompts"][pid] = prompt_entry(pid)
        used = {c["source_prompt_id"] for c in man["clips"]} | {s["source_prompt_id"] for s in man["sfx"]}
        # drop only plain-ID prompts no cell uses any more ("<ID> REGEN-0n" keys are kept as they are)
        man["prompts"] = {k: v for k, v in man["prompts"].items() if " " in k or k in used}
        manifest_path().write_text(json.dumps(man, indent=1), encoding="utf-8")
        _, new, new_src = current_cells()
        lines.append("after: line_db / YIN / LUFS")
        for r, x in sorted(new.items()):
            lines.append(f"  {r:5d}  {cell_row(x, r)}  src {new_src[r]}")
        lines.append("timbre steps after: " + json.dumps(band_steps(new)))
    (out / ("dry.txt" if dry else "cut.txt")).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["analyse", "scan", "cut"])
    ap.add_argument("--src", default=str(SRC))
    ap.add_argument("--dry", action="store_true", help="cut: evaluate CANDIDATES, write nothing to the game")
    a = ap.parse_args()
    if a.cmd == "analyse":
        cmd_analyse(Path(a.src))
    elif a.cmd == "scan":
        from el_prepare import mono
        for take, f_line, lo, hi in (("ENG_CAB_IDLE_STEADY (3).wav", 50.8, 0.0, 12.0), ("ENG_CAB_IDLE_STEADY (4).wav", 73.0, 0.0, 8.3),
                                     ("ENG_CAB_IDLE_STEADY (1).wav", 37.9, 0.0, 10.1), ("ENG_CAB_OVERRUN_SWEEP (4).wav", 45.2, 6.8, 12.0)):
            print(take, scan_window(mono(Path(a.src) / take), f_line, lo, hi))
    else:
        cmd_cut(Path(a.src), a.dry)
