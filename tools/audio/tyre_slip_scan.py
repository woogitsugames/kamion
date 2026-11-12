"""ADR 0145: where does the tyre squeal switch on? Reads physics-runner telemetry CSVs (per-wheel transient slip ratio
kappa' and slip angle alpha', the same WheelState fields TruckAudioController reads) and evaluates the audio mapping
before (LayerMath.SquealGain on the worst combined slip of all wheels) and after (scrub from the trailer / tandem
lateral slip at low speed, squeal from tractor + trailer combined slip with a speed gate).

Run:
  dotnet run -c Release --project tools/physics-runner/Runner -- --scenarios artifacts/tyre-scrub/scenarios \
      --out artifacts/tyre-scrub/runner --no-multi
  cd tools/audio; uv run python tyre_slip_scan.py ../../artifacts/tyre-scrub/runner [--plot out.png]

The python mirror of the C# mapping lives here (scrub_gain / squeal_gain_v2); TyreScrubTests pin the same numbers.
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

import numpy as np

KAPPA_REF, ALPHA_REF = 0.12, 0.10          # LayerMath (unchanged)


def smooth01(x: float) -> float:
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def combined(kappa: float, alpha: float) -> float:
    return math.hypot(kappa / KAPPA_REF, alpha / ALPHA_REF)


# --- before (ADR 0007 .. 0142) ---
def squeal_gain_v1(s: float, v: float) -> float:
    if v < 1.5:
        return 0.0
    return smooth01((s - 0.8) / 0.6) * min(max((v - 1.5) / 2.5, 0.0), 1.0)


# --- after (ADR 0145), mirror of LayerMath.ScrubGain / SquealGain ---
SCRUB_A0_DEG, SCRUB_A1_DEG = 1.0, 5.0       # trailer/tandem lateral slip: onset, full
SCRUB_V_ON, SCRUB_V_FULL, SCRUB_V_OFF0, SCRUB_V_OFF1 = 0.3, 1.2, 6.0, 11.0   # m/s
SQUEAL_ON, SQUEAL_FULL = 1.3, 2.0           # combined slip (norm.), above the steady low-speed tandem scrub
SQUEAL_V0, SQUEAL_V1 = 5.0, 9.0             # m/s (18 / 32 km/h)


def scrub_gain(alpha_deg: float, v: float) -> float:
    a = smooth01((alpha_deg - SCRUB_A0_DEG) / (SCRUB_A1_DEG - SCRUB_A0_DEG))
    on = smooth01((v - SCRUB_V_ON) / (SCRUB_V_FULL - SCRUB_V_ON))
    off = 1.0 - smooth01((v - SCRUB_V_OFF0) / (SCRUB_V_OFF1 - SCRUB_V_OFF0))
    return a * on * off


def squeal_gain_v2(s: float, v: float) -> float:
    return smooth01((s - SQUEAL_ON) / (SQUEAL_FULL - SQUEAL_ON)) * smooth01((v - SQUEAL_V0) / (SQUEAL_V1 - SQUEAL_V0))


def scan(path: Path) -> dict:
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return {}
    names = [k[:-len("_alpha_deg")] for k in rows[0] if k.endswith("_alpha_deg")]
    n = len(rows)
    tail = rows[int(n * 0.6):]                      # steady state: last 40 %
    v = np.array([abs(float(r["v_fwd"])) for r in tail])
    out = {"id": path.stem, "v_kmh": float(np.mean(v) * 3.6), "art_deg": float(np.mean([abs(float(r["articulation_deg"])) for r in tail]))}
    worst = {"tractor": 0.0, "trailer": 0.0}
    alpha_max = {"tractor": 0.0, "trailer": 0.0}
    per_wheel = {}
    g1 = g_scrub = g_sq2 = 0.0
    for r in tail:
        vv = abs(float(r["v_fwd"]))
        s_all = s_tr = 0.0
        a_trl = 0.0
        for nm in names:
            if float(r.get(nm + "_contact", 1)) < 0.5 or float(r[nm + "_fz"]) <= 0:
                continue
            a = abs(float(r[nm + "_alpha_deg"]))
            k = abs(float(r[nm + "_slip"]))
            s = combined(k, math.radians(a))
            per_wheel[nm] = max(per_wheel.get(nm, 0.0), a)
            grp = "trailer" if nm.startswith("T_") else "tractor"
            worst[grp] = max(worst[grp], s)
            alpha_max[grp] = max(alpha_max[grp], a)
            s_all = max(s_all, s)
            if grp == "trailer":
                a_trl = max(a_trl, a)
            else:
                s_tr = max(s_tr, s)
        g1 += squeal_gain_v1(s_all, vv)
        # scrub: worst lateral slip of the trailer axles (tractor rear duals when solo) – mean over the tail
        a_scrub = a_trl if a_trl > 0 else max(abs(float(r[nm + "_alpha_deg"])) for nm in names if nm.startswith("rear"))
        g_scrub += scrub_gain(a_scrub, vv)
        g_sq2 += squeal_gain_v2(s_all, vv)
    m = len(tail)
    out.update(worst_tractor=worst["tractor"], worst_trailer=worst["trailer"], alpha_tractor=alpha_max["tractor"],
               alpha_trailer=alpha_max["trailer"], squeal_v1=g1 / m, scrub_v2=g_scrub / m, squeal_v2=g_sq2 / m, wheels=per_wheel)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--out", default=None, help="write the table here")
    a = ap.parse_args()
    lines = ["| run | v km/h | artic. deg | max alpha tractor / trailer deg | combined slip (norm.) tractor / trailer | "
             "squeal before | scrub after | squeal after |", "|---|---|---|---|---|---|---|---|"]
    for p in sorted(Path(a.dir).glob("*.csv")):
        r = scan(p)
        if not r:
            continue
        lines.append(f"| {r['id']} | {r['v_kmh']:.1f} | {r['art_deg']:.1f} | {r['alpha_tractor']:.2f} / {r['alpha_trailer']:.2f} | "
                     f"{r['worst_tractor']:.2f} / {r['worst_trailer']:.2f} | {r['squeal_v1']:.2f} | {r['scrub_v2']:.2f} | {r['squeal_v2']:.2f} |")
        lines.append("|  wheels max alpha | " + ", ".join(f"{k} {v:.1f}" for k, v in r["wheels"].items()) + " |||||||")
    txt = "\n".join(lines)
    print(txt)
    if a.out:
        Path(a.out).write_text(txt + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
