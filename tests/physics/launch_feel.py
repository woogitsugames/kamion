# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib>=3.8"]
# ///
"""Launch-feel metrics and plot (ADR 0134): 0-30/50/60 km/h from pedal-on, up-shifts to 50 km/h, cab and chassis pitch.

Usage: uv run tests/physics/launch_feel.py <csv>... [--png]
Signs: pitch_deg (chassis) = asin(fwd.y), > 0 nose up; cab_pitch_deg > 0 = cab nose down relative to the frame.
Eye/camera pitch in the world (nose up) = chassis - cab (the cab-view camera rides on the cab pivot).
"""
import csv, sys
from pathlib import Path

KEYS = ("t", "speed_kmh", "a_long", "pitch_deg", "cab_pitch_deg", "gear", "rpm", "throttle_in")

def load(p):
    with open(p, newline="") as f:
        return [{k: float(row[k]) for k in KEYS} for row in csv.DictReader(f)]

def metrics(rows):
    t0 = next(r["t"] for r in rows if r["throttle_in"] > 0.01)
    base = next(r["pitch_deg"] for r in rows if r["t"] >= t0)
    out = {}
    for v in (30, 50, 60):
        out[f"t0_{v}_s"] = next((round(r["t"] - t0, 2) for r in rows if r["speed_kmh"] >= v), None)
    t50 = out["t0_50_s"] or 1e9
    shifts, prev, prev_rpm = [], None, 0.0
    for r in rows:
        g = int(r["gear"])
        if g > 0:
            if prev is not None and g != prev and r["t"] - t0 <= t50:
                shifts.append((round(r["t"] - t0, 2), prev, g, round(r["speed_kmh"], 1), round(prev_rpm)))
            if prev is None or g == prev:
                prev_rpm = r["rpm"]
            prev = g
    win = [r for r in rows if t0 <= r["t"] <= t0 + t50]
    out["upshifts_to_50"] = shifts
    out["max_cab_pitch_rel_deg"] = round(max(abs(r["cab_pitch_deg"]) for r in win), 3)
    out["max_chassis_pitch_deg"] = round(max(abs(r["pitch_deg"] - base) for r in win), 3)
    eye = [(r["pitch_deg"] - base) - r["cab_pitch_deg"] for r in win]
    out["max_eye_pitch_deg"] = round(max(abs(e) for e in eye), 3)
    out["eye_pitch_p2p_deg"] = round(max(eye) - min(eye), 3)
    out["max_a_long"] = round(max(r["a_long"] for r in win), 3)
    out["mean_a_0_50"] = round((50 / 3.6) / t50, 3) if out["t0_50_s"] else None
    return out, t0, base

def plot(p, rows, t0, base, title):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    t = [r["t"] - t0 for r in rows]
    fig, ax = plt.subplots(5, 1, figsize=(10, 11), sharex=True)
    ax[0].plot(t, [r["speed_kmh"] for r in rows]); ax[0].set_ylabel("speed km/h")
    ax[1].step(t, [r["gear"] for r in rows], where="post"); ax[1].set_ylabel("gear")
    ax[2].plot(t, [r["rpm"] for r in rows]); ax[2].set_ylabel("rpm")
    ax[3].plot(t, [r["a_long"] for r in rows]); ax[3].set_ylabel("a_long m/s2")
    ax[4].plot(t, [r["pitch_deg"] - base for r in rows], label="chassis (nose up +)")
    ax[4].plot(t, [-r["cab_pitch_deg"] for r in rows], label="cab rel. frame (nose up +)")
    ax[4].plot(t, [(r["pitch_deg"] - base) - r["cab_pitch_deg"] for r in rows], label="eye = chassis + cab", lw=2)
    ax[4].set_ylabel("pitch deg"); ax[4].legend(loc="upper right")
    for a in ax: a.grid(alpha=.3)
    ax[4].set_xlim(-0.5, 30); ax[4].set_xlabel("s from pedal on")
    fig.suptitle(title); fig.tight_layout()
    out = Path(p).with_suffix(".feel.png"); fig.savefig(out, dpi=80); return out

if __name__ == "__main__":
    png = "--png" in sys.argv
    for p in [a for a in sys.argv[1:] if not a.startswith("--")]:
        rows = load(p)
        m, t0, base = metrics(rows)
        print(Path(p).name)
        for k, v in m.items():
            if k == "upshifts_to_50":
                print(f"  upshifts_to_50 = {len(v)}: " + "  ".join(f"{a}s {b}->{c} @{d}km/h {e}rpm" for a, b, c, d, e in v))
            else:
                print(f"  {k} = {v}")
        if png:
            print("  png:", plot(p, rows, t0, base, f"{Path(p).parent.name}/{Path(p).stem}"))
