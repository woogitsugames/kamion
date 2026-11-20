"""D94 / ADR 0306: did the player's autopilot keep the combination in its lane through the Knyszyn roundabout?

Reads a player telemetry CSV (`-telemetry 1`, VehicleTelemetryRecorder: t, x, z, heading_deg, trailer_x, trailer_z,
per-wheel *_surface / *_contact) and reports, inside a radius around a point (default: the Knyszyn ring centre in the
frame of the CSV, given in that frame):
  * wheel samples on Gravel (4) / Grass (5) (SurfaceTable: kerb tops / paving count as hard),
  * max lateral distance of the tractor and the trailer body from the route link polyline (route_links.json, tile-local,
    shifted by --offset E,N into the CSV frame).

    uv run --no-project python tools/worldgen/qa/combo_player_run.py <telemetry.csv> --link knyszyn-dk65-to-dw671-w
        --offset <E,N of the tile origin in the CSV frame> [--centre E,N --radius 60]
"""
import argparse
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LINKS = ROOT / "game/Assets/_Project/World/Runtime/Streaming/Resources/WorldStreaming/route_links.json"


def seg_dist(p, P):
    best = 1e9
    for (ax, ay), (bx, by) in zip(P, P[1:]):
        dx, dy = bx - ax, by - ay
        l2 = dx * dx + dy * dy or 1e-12
        t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / l2))
        best = min(best, math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy))
    return best


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("csv"); ap.add_argument("--link", required=True)
    ap.add_argument("--offset", default="0,0"); ap.add_argument("--centre"); ap.add_argument("--radius", type=float, default=60.0)
    a = ap.parse_args(argv)
    ox, oy = map(float, a.offset.split(","))
    L = next(x for x in json.loads(LINKS.read_text(encoding="utf-8"))["links"] if x["id"] == a.link)
    P = [(e + ox, n + oy) for e, n in zip(L["e"], L["n"])]
    rows = list(csv.DictReader(l for l in open(a.csv, encoding="utf-8") if not l.startswith("#")))
    surf_cols = [k for k in rows[0] if k.endswith("_surface")]
    c = tuple(map(float, a.centre.split(","))) if a.centre else None
    n = off = 0
    lat_t = lat_r = 0.0
    for r in rows:
        x, z = float(r["x"]), float(r["z"])
        if c and math.hypot(x - c[0], z - c[1]) > a.radius:
            continue
        n += 1
        off += sum(1 for k in surf_cols if r[k] in ("4", "5", "4.0", "5.0"))
        lat_t = max(lat_t, seg_dist((x, z), P))
        if r.get("trailer_x"):
            lat_r = max(lat_r, seg_dist((float(r["trailer_x"]), float(r["trailer_z"])), P))
    print(json.dumps({"samples": n, "wheel_samples_gravel_or_grass": off, "tractor_max_from_line_m": round(lat_t, 2),
                      "trailer_body_max_from_line_m": round(lat_r, 2), "wheels": len(surf_cols)}, indent=1))


if __name__ == "__main__":
    main()
