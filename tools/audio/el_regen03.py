"""ElevenLabs REGEN-03 (docs/owner/ELEVENLABS-REGEN-03.md, ADR 0145): tyre scrub in a tight turn and hard squeal,
exterior + cabin, takes (1)-(4) each. Measures every take and picks the best one per ID automatically.

    uv run python el_regen03.py [--src <dir>]       # report + sheet only (el_fx.py imports select() and wires the picks)

Per take (after the same loop processing as el_fx.py: mono, circular 25 Hz high-pass, 40 ms equal-power seam):
  lufs        integrated loudness (BS.1770) of the raw mono take
  drift_db    std of the 0.5 s short-term level (a loop must not swell; a swell is heard as a repeat every 10 s)
  seam        el_analyze.seam: jump ratio (< 1) and 4 kHz+ energy spike at the joint (< 6 dB)
  tone_db     highest narrow-band line of the long-term spectrum over its local median (+-25 Hz) in 400-6000 Hz:
              the 'whistle' the owner rejected (procedural squeal: ~930 Hz line). PASS < 12 dB (the turbo whistle
              criterion of el_regen02.py, inverted)
  tone_frac   share of 85 ms frames where one bin in 400-6000 Hz stands > 18 dB over its local (+-180 Hz) floor
              (narrow line in that frame; a wavering squeal has some, a whistle has them all); PASS < 0.5
  lf_share    energy share below 150 Hz (engine drone; the runtime engine already plays): smaller is better
  centroid    spectral centroid [Hz] (scrub should sit low, the squeal higher)
  peak, clipped samples
  rhythm_acf  envelope (1-6 kHz) autocorrelation peak at 0.2-2 s: a regular creak train sounds like a machine
Pick = among PASS takes the lowest cost  drift_db + 4 * lf_share + 0.5 * max(0, tone_db - 6) + 8 * max(0, rhythm_acf - 0.3); if none passes, the
lowest cost overall is reported with FAIL and NOT wired (el_fx keeps the procedural loop).
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from scipy import signal  # noqa: E402

from el_analyze import MAIN, lufs, prominence_db, seam, welch_db  # noqa: E402
from el_prepare import FS, ROOT, circular_hp, mono, seam_loop  # noqa: E402

ART = ROOT / "artifacts" / "tyre-scrub" / "regen03"
IDS = ["TYRE_SCRUB_TIGHT_TURN", "TYRE_SCRUB_TIGHT_TURN_CAB", "TYRE_SQUEAL_HARD", "TYRE_SQUEAL_HARD_CAB"]
TONE_MAX_DB, TONE_FRAC_MAX = 12.0, 0.5

# REGEN-03 prompts (docs/owner/ELEVENLABS-REGEN-03.md), provenance for el_manifest.json
_SET = {"batch": "REGEN-03", "model": "v3", "duration": 10, "influence": 80, "loop": True, "variants": 4}
PROMPTS = {
    "TYRE_SCRUB_TIGHT_TURN": "Close outside recording of a heavy articulated truck making a very tight slow turn on dry asphalt at walking speed: the trailer's multi-axle tyres are dragged sideways, producing a continuous low rubbery scrubbing and groaning with irregular creaks and short chirps, gravel crunch faintly under the rubber, no engine roar in the foreground, no squeal whistle, no music, no voices",
    "TYRE_SCRUB_TIGHT_TURN_CAB": "Inside the closed cab of a heavy truck during a very tight slow turn, heard through the floor and the rear wall: muffled low rubber scrubbing and groaning from the trailer tyres dragged sideways on asphalt, irregular dull creaks, quiet diesel idle in the background, no squeal whistle, no music, no voices",
    "TYRE_SQUEAL_HARD": "Outside recording of a heavy truck's large tyres squealing on dry asphalt while cornering too fast: a rough, low-pitched, wavering rubber squeal with grit and texture, not a thin whistle, varying in intensity, tyre roar underneath, no engine in the foreground, no music, no voices",
    "TYRE_SQUEAL_HARD_CAB": "Inside the closed cab of a heavy truck cornering too fast: muffled low rubber squeal from the tyres heard through the cab, rough and wavering, tyre and road roar underneath, steady diesel in the background, no music, no voices",
}


def prompt_entry(pid: str) -> dict:
    return {"id": pid, "prompt": PROMPTS[pid], **_SET}


WIN_S = 6.0          # loop length cut from the 10 s take (the steadiest window; dropouts would mark the loop)
SEAM_S = 0.04


def best_window(x: np.ndarray) -> float:
    """Start [s] of the WIN_S window with the steadiest 0.25 s level that is not quieter than the take (a dropout or a
    swell inside a loop is heard as a repeat). cost = std(level) + 0.5 * max(0, median(take) - mean(window))."""
    h = int(0.25 * FS)
    lv = np.array([10 * math.log10(np.mean(x[i:i + h] ** 2) + 1e-20) for i in range(0, len(x) - h + 1, h)])
    n = int(WIN_S / 0.25)
    ref = float(np.median(lv))
    best, t0 = 1e9, 0.0
    for k in range(0, max(1, len(lv) - n - 1)):
        w = lv[k:k + n]
        c = float(np.std(w)) + 0.5 * max(0.0, ref - float(np.mean(w)))
        if c < best:
            best, t0 = c, k * 0.25
    return t0


def loopify(x: np.ndarray, t0: float | None = None) -> np.ndarray:
    x = circular_hp(x)
    if t0 is None:
        t0 = best_window(x)
    a = int(t0 * FS)
    return seam_loop(x[a:a + int((WIN_S + SEAM_S) * FS)], SEAM_S)


def measure(x: np.ndarray) -> dict:
    t0 = best_window(circular_hp(x))
    y = loopify(x, t0)
    r = {"window_s": t0, "lufs": lufs(x, FS), "peak_dbfs": 20 * math.log10(np.abs(x).max() + 1e-12), "clipped": int(np.sum(np.abs(x) >= 0.999))}
    w = int(0.5 * FS)
    st = [10 * math.log10(np.mean(y[i:i + w] ** 2) + 1e-20) for i in range(0, len(y) - w, w)]
    r["drift_db"] = float(np.std(st))
    r.update(seam(y, FS))
    f, p = welch_db(y, FS, 1 << 14)
    prom = prominence_db(f, p)
    band = (f >= 400) & (f <= 6000)
    i = int(np.argmax(np.where(band, prom, -99)))
    r["tone_db"], r["tone_hz"] = float(prom[i]), float(f[i])
    fs_, _, S = signal.stft(y, FS, nperseg=4096, noverlap=2048)
    b = (fs_ >= 400) & (fs_ <= 6000)
    from scipy.ndimage import median_filter
    mag = 20 * np.log10(np.abs(S[b]) + 1e-12)
    loc = mag - median_filter(mag, size=(31, 1), mode="nearest")   # +-180 Hz local floor per frame
    r["tone_frac"] = float(np.mean(loc.max(axis=0) > 18.0))
    # rhythm: autocorrelation of the 1-6 kHz envelope (100 Hz frame rate) at lags 0.2-2 s; a regular pulse train
    # (creak every 0.55 s) is heard as a machine / a repeat, real scrub is irregular (siren_scan.py uses ACF > 0.45)
    env = np.abs(signal.hilbert(signal.sosfiltfilt(signal.butter(4, [1000, 6000], "bp", fs=FS, output="sos"), y)))
    env = env[: len(env) // 480 * 480].reshape(-1, 480).mean(axis=1)
    env = env - np.convolve(env, np.ones(100) / 100, "same")      # remove the slow (> 1 s) level swell: rhythm only
    ac = np.correlate(env, env, "full")[len(env) - 1:]
    ac = ac / (ac[0] + 1e-20)
    r["rhythm_acf"] = float(ac[20:200].max())
    pw = 10 ** (p / 10)
    r["lf_share"] = float(pw[f < 150].sum() / pw.sum())
    r["centroid_hz"] = float((f * pw).sum() / pw.sum())
    r["pass"] = (r["tone_db"] < TONE_MAX_DB and r["tone_frac"] < TONE_FRAC_MAX and r["seam_jump_ratio"] < 1.0
                 and r["seam_hf_spike_db"] < 6.0 and r["clipped"] == 0 and r["rhythm_acf"] < 0.45)
    r["cost"] = r["drift_db"] + 4 * r["lf_share"] + 0.5 * max(0.0, r["tone_db"] - 6.0) + 8 * max(0.0, r["rhythm_acf"] - 0.3)
    return r


def scan(src: Path) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for pid in IDS:
        rows = []
        for n in range(1, 13):
            p = src / f"{pid} ({n}).wav"
            if p.exists():
                rows.append({"file": p.name, **measure(mono(p))})
        out[pid] = rows
    return out


def select(src: Path) -> dict[str, str | None]:
    """Best passing take per REGEN-03 ID (file name), None when absent or nothing passes."""
    res = {}
    for pid, rows in scan(src).items():
        ok = [r for r in rows if r["pass"]]
        res[pid] = min(ok, key=lambda r: r["cost"])["file"] if ok else None
    return res


def sheet(src: Path, table: dict[str, list[dict]], picks: dict, out: Path) -> None:
    items = [(pid, r) for pid in IDS for r in table[pid]]
    if not items:
        return
    fig, axs = plt.subplots(len(IDS), 4, figsize=(18, 3.2 * len(IDS)))
    for ax in axs.flat:
        ax.axis("off")
    for k, pid in enumerate(IDS):
        for j, r in enumerate(table[pid][:4]):
            ax = axs[k, j]
            ax.axis("on")
            y = loopify(mono(src / r["file"]), r["window_s"])
            f, t, S = signal.spectrogram(y, FS, nperseg=2048, noverlap=1536)
            ax.pcolormesh(t, f / 1000, 10 * np.log10(S + 1e-14), vmin=-130, vmax=-40, shading="auto", cmap="magma")
            ax.set_ylim(0, 8)
            mark = "  << PICK" if picks.get(pid) == r["file"] else ""
            ax.set_title(f"{r['file']}{mark}\nLUFS {r['lufs']:.1f} drift {r['drift_db']:.1f} dB tone {r['tone_db']:.1f} dB@{r['tone_hz']:.0f} "
                         f"frac {r['tone_frac']:.2f} acf {r['rhythm_acf']:.2f} LF {r['lf_share']:.2f} c {r['centroid_hz']:.0f} {'PASS' if r['pass'] else 'FAIL'}",
                         fontsize=7, color="red" if mark else "black")
            ax.tick_params(labelsize=6)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=55)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(MAIN / "art-source" / "audio" / "elevenlabs"))
    a = ap.parse_args()
    src = Path(a.src)
    table = scan(src)
    picks = {pid: (min([r for r in rows if r["pass"]], key=lambda r: r["cost"])["file"] if any(r["pass"] for r in rows) else None)
             for pid, rows in table.items()}
    lines = []
    for pid in IDS:
        for r in table[pid]:
            lines.append(f"{r['file']:34s} win {r['window_s']:4.2f} s LUFS {r['lufs']:6.1f} pk {r['peak_dbfs']:5.1f} drift {r['drift_db']:4.1f} dB "
                         f"seam {r['seam_jump_ratio']:.2f}/{r['seam_hf_spike_db']:+.1f} dB tone {r['tone_db']:5.1f} dB @ {r['tone_hz']:6.0f} Hz "
                         f"frac {r['tone_frac']:.2f} acf {r['rhythm_acf']:.2f} LF {r['lf_share']:.2f} centroid {r['centroid_hz']:5.0f} Hz cost {r['cost']:.2f} "
                         f"{'PASS' if r['pass'] else 'FAIL'}{'  << PICK' if picks[pid] == r['file'] else ''}")
        lines.append(f"  -> {pid}: {picks[pid]}")
    ART.mkdir(parents=True, exist_ok=True)
    (ART / "regen03.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (ART / "regen03.json").write_text(json.dumps({"picks": picks, "takes": table}, indent=1), encoding="utf-8")
    sheet(src, table, picks, ART / "regen03_sheet.png")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
