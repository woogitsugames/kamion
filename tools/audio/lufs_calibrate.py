"""D92 / ADR 0311: cab loudness calibration from Windows player captures.

The player records the listener mix after the cab bus gain (``-audio_capture``, ADR 0286; ``CabinBusFilter``, ADR 0311).
This script measures a capture segment (BS.1770-4 via ``pc_capture.measure``), cross-checks it with ffmpeg's ``ebur128``
filter when ffmpeg is on PATH, and prints the gain that puts the segment on the target:

    uv run python lufs_calibrate.py <capture.wav> --seg drive:8:62 --current-db 0 [--target -18] [--out dir --label x]

new_gain_db = current_db + (target - measured_integrated); the true peak after the change is
measured_true_peak + (new - current) and must stay <= the ceiling (-1 dBTP), otherwise the script refuses (exit 2):
the fix would then be a limiter or a mix change, not a bus gain. Exit 0 = within +-tolerance already, 1 = change needed
(the new value is printed), 2 = the change would break the true-peak ceiling or the gain range.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

import pc_capture

GAIN_RANGE_DB = (-12.0, 12.0)  # CabinLoudness.MinGainDb / MaxGainDb


def ffmpeg_ebur128(wav: Path, t0: float, t1: float) -> dict | None:
    """Integrated loudness / true peak of [t0, t1] by ffmpeg ebur128 (independent implementation), or None."""
    exe = shutil.which("ffmpeg")
    if exe is None:
        return None
    cmd = [exe, "-hide_banner", "-nostats", "-ss", f"{t0:.3f}", "-t", f"{t1 - t0:.3f}", "-i", str(wav),
           "-af", "ebur128=peak=true:framelog=quiet", "-f", "null", "-"]
    out = subprocess.run(cmd, capture_output=True, text=True, check=False).stderr
    summary = out[out.rfind("Summary:"):] if "Summary:" in out else out
    i = re.search(r"I:\s+(-?[\d.]+) LUFS", summary)
    lra = re.search(r"LRA:\s+(-?[\d.]+) LU", summary)
    tp = re.search(r"Peak:\s+(-?[\d.inf]+) dBFS", summary)
    if i is None:
        return None
    return {"lufs_integrated": float(i.group(1)), "lra_lu": float(lra.group(1)) if lra else None,
            "true_peak_dbtp": float(tp.group(1)) if tp and tp.group(1) not in ("-inf", "inf") else None,
            "log_tail": summary.strip().splitlines()[-12:]}


def plan(measured_i: float, measured_tp: float, current_db: float, target: float, tol: float, ceiling: float) -> dict:
    """Pure decision (unit-tested): new gain, predicted level / true peak, verdict code."""
    delta = target - measured_i
    new_db = round(current_db + delta, 2)
    pred_tp = measured_tp + delta
    if abs(delta) <= tol:
        code = 0
    elif pred_tp > ceiling or not (GAIN_RANGE_DB[0] <= new_db <= GAIN_RANGE_DB[1]):
        code = 2
    else:
        code = 1
    return {"delta_db": round(delta, 2), "new_gain_db": new_db, "predicted_lufs": round(measured_i + delta, 2),
            "predicted_true_peak_dbtp": round(pred_tp, 2), "code": code}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("wav", type=Path, nargs="+", help="one or more captures; several = one programme (concatenated)")
    ap.add_argument("--seg", required=True, help="name:t0:t1 (seconds into each capture) = the calibrated cab drive")
    ap.add_argument("--current-db", type=float, required=True, help="cab bus gain the captures were made with")
    ap.add_argument("--target", type=float, default=-18.0)
    ap.add_argument("--tol", type=float, default=1.0)
    ap.add_argument("--ceiling", type=float, default=-1.0)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--label", default="calib")
    a = ap.parse_args()
    name, t0, t1 = a.seg.split(":")[0], float(a.seg.split(":")[1]), float(a.seg.split(":")[2])
    parts, fs = [], None
    for w in a.wav:
        x, r = sf.read(w, always_2d=True, dtype="float64")
        if fs is not None and r != fs:
            raise SystemExit(f"rate mismatch: {w}")
        fs = r
        parts.append(x[int(t0 * fs):int(t1 * fs)])
    seg = np.concatenate(parts)
    m = pc_capture.measure(seg, fs)
    if len(a.wav) == 1:
        ff = ffmpeg_ebur128(a.wav[0], t0, t1)
    else:  # the concatenated programme through ffmpeg too (temp float WAV next to the output)
        tmp = (a.out or Path(".")) / f"{a.label}_concat.wav"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        sf.write(tmp, seg.astype(np.float32), fs, subtype="FLOAT")
        ff = ffmpeg_ebur128(tmp, 0.0, len(seg) / fs)
        tmp.unlink()
    p = plan(m["lufs_integrated"], m["true_peak_dbtp"], a.current_db, a.target, a.tol, a.ceiling)
    rep = {"files": [str(w) for w in a.wav], "segment": {"name": name, "t0": t0, "t1": t1},
           "current_gain_db": a.current_db, "target_lufs": a.target, "tolerance_lu": a.tol, "ceiling_dbtp": a.ceiling,
           "bs1770": m, "ffmpeg_ebur128": ff, "plan": p}
    if a.out:
        a.out.mkdir(parents=True, exist_ok=True)
        (a.out / f"{a.label}_calib.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(json.dumps({k: rep[k] for k in ("segment", "current_gain_db", "plan")}, indent=2))
    print(f"BS.1770 I={m['lufs_integrated']} LUFS TP={m['true_peak_dbtp']} dBTP LRA={m['lra_lu']} | ffmpeg "
          f"I={ff['lufs_integrated'] if ff else 'n/a'} TP={ff['true_peak_dbtp'] if ff else 'n/a'}")
    return p["code"]


if __name__ == "__main__":
    raise SystemExit(main())
