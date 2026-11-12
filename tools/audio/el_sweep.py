"""Slow 600->2100 rpm sweep through the runtime mirror with the ElevenLabs banks (ADR 0137): level continuity.

    uv run python el_sweep.py   -> artifacts/audio-el/verify/sweep.png, sweep.json
Max 100 ms RMS step between adjacent windows and the largest deviation of the RMS curve from its 1 s median
(timbre/level seams between cells show up as steps/bumps).
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from scipy.ndimage import median_filter  # noqa: E402

import el_demo as ed  # noqa: E402
import runtime_sim as rs  # noqa: E402
from dsp import FS  # noqa: E402

OUT = ed.ROOT / "artifacts" / "audio-regen01" / "verify"


def main():
    man = json.loads(ed.EL_MAN.read_text(encoding="utf-8"))
    rs.XFADE_COHERENCE = 0.0
    res = {}
    fig, ax = plt.subplots(1, 1, figsize=(10, 4))
    for persp in ("ext", "cab"):
        for load, col in ((1.0, "tab:red"), (0.5, "tab:orange"), (0.0, "tab:green")):
            g = ed.load_grid_el(man, "engine", persp, 6)
            n = int(24 * FS)
            y = np.zeros(n)
            frame = int(FS / rs.FRAME_HZ)
            for i0 in range(0, n, frame):
                g.update(600 + 1500 * i0 / n, load, 1.0)
                y[i0:i0 + frame] = g.render(frame, FS)
            w = FS // 10
            r = 20 * np.log10(np.sqrt(np.array([np.mean(y[i:i + w] ** 2) for i in range(0, n - w, w)])) + 1e-9)
            r = r[5:]
            step = float(np.max(np.abs(np.diff(r))))
            bump = float(np.max(np.abs(r - median_filter(r, 11, mode="nearest"))))
            res[f"{persp}_load{load}"] = {"max_step_db_100ms": step, "max_bump_db": bump}
            rpm = 600 + 1500 * (np.arange(len(r)) + 5) * w / n
            ax.plot(rpm, r, color=col, lw=0.8, ls="-" if persp == "ext" else "--", label=f"{persp} load {load}")
    ax.set_xlabel("rpm")
    ax.set_ylabel("RMS 100 ms [dBFS]")
    ax.legend(fontsize=7, ncol=2)
    ax.set_title("ElevenLabs grid: slow sweep through the runtime mirror (equal-power crossfade)", fontsize=9)
    for r in man["rpm_grid"]:
        ax.axvline(r, color="grey", lw=0.4)
    fig.tight_layout()
    fig.savefig(OUT / "sweep.png", dpi=80)
    (OUT / "sweep.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
