# /// script
# requires-python = ">=3.10"
# ///
"""Find jolts in a Unity vehicle telemetry CSV (VehicleTelemetryRecorder, columns vel_x/vel_y/vel_z/route_s).

Usage:
    uv run tools/telemetry/route_jolt.py artifacts/device/<serial>/<ts>/telemetry/drive-*.csv [--top 8] [--wheels]

Record on the phone with `pwsh scripts/device-metrics.ps1 -Serial <s> -Launch -DurationSeconds 100 -Scene WorldC
-Autopilot route -Speed 50 -Trailer 40 -Extra telemetry=1`, then
`adb -s <s> pull /sdcard/Android/data/com.woogitsugames.kamion/files/telemetry <dir>`.

Prints the largest per-step body velocity changes |dv| (m/s per physics step) with the route position, and with
--wheels the per-wheel compression / load / surface around the worst one. Reference (A16, 40 t, 50 km/h): median
|dv| ~0.005 m/s, p99 ~0.07 m/s; a kerb strike shows as 0.5-0.7 m/s plus a wheel Fz spike (several x static load).
"""
from __future__ import annotations

import argparse
import csv
import math
import statistics


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--wheels", action="store_true")
    a = ap.parse_args()
    with open(a.csv, newline="") as f:
        rows = [r for r in csv.DictReader(f) if r.get("t") and r["t"][:1].isdigit()]
    if not rows or "vel_x" not in rows[0]:
        raise SystemExit("no vel_x/vel_y/vel_z columns - record with a build that has them (telemetry=1)")
    vel = [(float(r["vel_x"]), float(r["vel_y"]), float(r["vel_z"])) for r in rows]
    dv = [0.0] + [math.dist(vel[i], vel[i - 1]) for i in range(1, len(vel))]
    s = sorted(dv[1:])
    print(f"{len(rows)} steps, t {rows[-1]['t']} s, route_s {float(rows[-1]['route_s']):.0f} m; "
          f"|dv| median {statistics.median(s):.4f}, p99 {s[int(len(s) * 0.99)]:.3f}, max {s[-1]:.3f} m/s")
    order = sorted(range(len(rows)), key=lambda i: dv[i], reverse=True)[: a.top]
    for i in order:
        r = rows[i]
        print(f"  |dv| {dv[i]:.3f} m/s  s={float(r['route_s']):.1f} m  t={float(r['t']):.2f} s  "
              f"v={float(r['speed_kmh']):.1f} km/h  pitch={float(r['pitch_deg']):.2f}  pos=({float(r['x']):.1f}, {float(r['y']):.2f}, {float(r['z']):.1f})")
    if a.wheels:
        wheels = [k[:-3] for k in rows[0] if k.endswith("_fz") and k != "kingpin_fz"]
        w0 = order[0]
        for r in rows[max(0, w0 - 60): w0 + 10: 5]:
            cells = " ".join(f"{w}:{float(r[w + '_comp']):+.3f}/{float(r[w + '_fz']) / 1000:.0f}kN/s{r[w + '_surface']}" for w in wheels)
            print(f"  t={float(r['t']):.2f} s={float(r['route_s']):.1f} {cells}")


if __name__ == "__main__":
    main()
