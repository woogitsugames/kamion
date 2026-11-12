"""Swept path of the 16.47 m tractor + tridem semitrailer along gate-3 segments G3-A / G3-B (task 2026-11-10).

The physics core drives the route closed-loop (tools/physics-runner, driver type "path": Stanley steering on the
steer-axle centre, PI speed hold), laden 40 t, flat ground (grade ignored: low-speed off-tracking is kinematic).
The driven poses are checked against the generated road surface (visual `road` + `paved` nodes of
chunk_*.glb, the meshes the kerb colliders are built from) rasterised top-down at RES m:

  carriageway  road_* / yard_* (incl. flush joins of adjacent carriageways)
  apron        apron_sett (roundabout truck apron, 4 cm mountable kerb, standards.ROUNDABOUT_APRON_W)
  kerb         curb_concrete tops (13 cm kerbs, island kerb behind the apron)
  off          sidewalk / verge / shoulder / path / terrain (no road mesh)

Per tyre (3 points across the tread: inner edge, centre, outer edge, at the axle line) the signed clearance to the
edge of carriageway+apron (+ inside, - on the kerb / beyond) and the apron use (how far onto the apron).
Body: tractor bumper / cab corners, trailer front and rear corners; overhang beyond the kerb line is reported
(it passes over a 13 cm kerb) and the clearance to prop collider boxes (posts, signs; route_corridor.prop_boxes)
is checked, since those are walls for the body.

Run:  uv run --project tools/worldgen python tests/physics/swept_path_gate3.py [--out artifacts/swept/<ts>]
Writes <out>/swept_<seg>_<variant>.csv (runner), <out>/plot_<ring>_<variant>.png, <out>/summary.json, prints table.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy import ndimage

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tests" / "gis"))
import route_corridor as RC  # noqa: E402

REGION = "bialystok-industrial-c"
REGION_DIR = REPO / "Data" / "Regions" / REGION
ROUTE = REGION_DIR / "route_start.json"
SEGMENTS = REGION_DIR / "gate3_segment.json"
RES = 0.10                      # raster cell [m]
SMOOTH_M = 4.0                  # WORKING_VALUE: driver-line smoothing (Gaussian sigma) of the route polyline

# --- vehicle geometry (art-source/truck/dims.json + physics definitions; tractor origin = rear axle, trailer origin
# = ground below kingpin). Tyre lateral positions: centre of each tyre, half tread width.
WB = 3.70
FW_LEAD = 0.68
TYRES = {   # name: (frame, z, lateral centre |x|, half tread)
    "steer":   ("T", WB, 1.02, 0.1575),                          # 315/80 R22.5, track 2.04
    "drive_o": ("T", 0.0, 0.91 + 0.17, 0.1575),                  # duals, pair centre 0.91, spacing 0.34
    "drive_i": ("T", 0.0, 0.91 - 0.17, 0.1575),
    "trl_1":   ("S", -6.39, 1.02, 0.1925),                       # 385/65 R22.5 singles, track 2.04
    "trl_2":   ("S", -7.70, 1.02, 0.1925),
    "trl_3":   ("S", -9.01, 1.02, 0.1925),
}
BODY = {    # name: (frame, z, |x|)  corners
    "bumper":       ("T", WB + 1.45, 1.245),
    "cab_back":     ("T", WB - 0.95 - 1.40, 1.245),
    "trailer_front": ("S", 1.60, 1.275),
    "trailer_rear": ("S", -12.00, 1.275),
}

CARRIAGEWAY = {"road_asphalt", "road_asphalt_new", "road_concrete", "road_paving", "road_gravel", "yard_asphalt",
               "yard_behaton", "yard_concrete", "yard_concrete_worn", "yard_gravel", "yard_paving", "yard_slabs"}
CAT = {"off": 0, "carriageway": 1, "apron": 2, "kerb": 3, "side": 4}

# --- speed profile (WORKING_VALUEs, driver model): lateral 1.2 m/s^2 (laden artic, comfortable), decel 0.8,
# accel 0.4 m/s^2; roundabout ring capped to the task range 15-25 km/h (variant "slow": 15 km/h cap).
A_LAT, A_DEC, A_ACC = 1.2, 0.8, 0.4
V_MIN_KMH = 8.0
VARIANTS = {"v25": 25.0, "v15": 15.0}
# driver lines: "lane" = steer axle on the smoothed route (lane centre), "wide" = a truck driver's line, steer axle
# moved outward by WIDE_GAIN x the steady-state off-tracking at the local radius (capped WIDE_MAX_M) so the trailer
# tracks in the lane; WORKING_VALUEs
LINES = ("lane", "wide")
WIDE_GAIN, WIDE_MAX_M = 0.5, 1.75
RUNS = {  # segment id: (s from [m], s to [m], analysed window [m]); the runs start 25 m early so the trailer settles
    "G3-A": (0.0, 452.0, (12.0, 450.0)),
    "G3-B": (1205.0, 1800.0, (1232.0, 1790.0)),
}


def dotnet() -> list[str]:
    for p in (Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "dotnet" / "dotnet.exe",
              Path(os.environ.get("ProgramFiles", "")) / "dotnet" / "dotnet.exe"):
        if p.exists():
            os.environ.setdefault("DOTNET_ROOT", str(p.parent))
            return [str(p)]
    return ["dotnet"]


# ------------------------------------------------------------------------------------------------ route / speed
def route_line(s0, s1, step=1.0):
    r = json.loads(ROUTE.read_text(encoding="utf-8"))
    P = np.asarray(r["points_en"], float)
    ms = np.asarray(r["maxspeed_kmh"], float)
    d = np.hypot(*np.diff(P, axis=0).T)
    keep = np.concatenate([[True], d > 1e-6])
    P, ms = P[keep], ms[keep]
    s = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
    ss = np.arange(s0, min(s1, s[-1]), step)
    Q = np.column_stack([np.interp(ss, s, P[:, 0]), np.interp(ss, s, P[:, 1])])
    # driver line: the route polyline has OSM-node kinks at junctions (up to ~100 deg at the ring entries); a driver
    # steers a continuous curve, so the steer-axle reference is the route smoothed with a Gaussian of SMOOTH_M
    Q = ndimage.gaussian_filter1d(Q, SMOOTH_M / step, axis=0, mode="nearest")
    vmax = ms[np.clip(np.searchsorted(s, ss) - 1, 0, len(ms) - 1)]
    return ss, Q, vmax


def offtracking(k):
    """steady-state off-tracking front axle -> tridem centre of this combination at path curvature k [1/m]"""
    R = 1.0 / np.maximum(np.abs(k), 1e-4)
    Rr = np.sqrt(np.maximum(R ** 2 - WB ** 2, 1.0))
    Rk = np.sqrt(Rr ** 2 + FW_LEAD ** 2)
    Rt = np.sqrt(np.maximum(Rk ** 2 - 7.70 ** 2, 1.0))
    return R - Rt


def wide_line(Q):
    k = ndimage.gaussian_filter1d(curvature(Q), 6.0)
    T = np.gradient(Q, axis=0)
    T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-9)
    Nl = np.column_stack([-T[:, 1], T[:, 0]])
    a = np.minimum(WIDE_GAIN * offtracking(k), WIDE_MAX_M)
    a = ndimage.gaussian_filter1d(a, 8.0)          # start swinging out before the turn, like a driver
    return Q - (np.sign(k) * a)[:, None] * Nl


def ring_line(centre, r, laps=1.25, approach=30.0, step=1.0):
    """Full circulation (CCW, Polish right-hand traffic) on the ring carriageway centre line, entered on a tangent
    at the north point heading west: the design-vehicle case of the guidance (U-turn / 3rd-4th exit)."""
    c = np.asarray(centre, float)
    a = np.arange(-approach, 0.0, step)
    top = c + np.array([0.0, r])
    A = np.column_stack([top[0] - a, np.full(len(a), top[1])])          # heading west towards the top point
    th = np.arange(0.0, laps * 2 * math.pi, step / r)
    C = np.column_stack([c[0] - r * np.sin(th), c[1] + r * np.cos(th)])  # CCW from the top
    Q = np.vstack([A, C])
    ss = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(Q, axis=0).T))])
    return ss, Q


def curvature(Q, half=4):
    k = np.zeros(len(Q))
    for i in range(half, len(Q) - half):
        a, b, c = Q[i - half], Q[i], Q[i + half]
        ab, bc, ca = np.linalg.norm(b - a), np.linalg.norm(c - b), np.linalg.norm(a - c)
        cr = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        k[i] = 2 * cr / max(ab * bc * ca, 1e-9)       # + = left turn
    return k


def speed_profile(ss, Q, vmax, rings, ring_cap_kmh, ring_fixed=False):
    k = np.abs(ndimage.uniform_filter1d(curvature(Q), 5))
    v = np.minimum(vmax / 3.6, np.sqrt(A_LAT / np.maximum(k, 1e-6)))
    for c, r in rings:
        inring = np.hypot(Q[:, 0] - c[0], Q[:, 1] - c[1]) < r + 8.0
        v[inring] = ring_cap_kmh / 3.6 if ring_fixed else np.minimum(v[inring], ring_cap_kmh / 3.6)
    v = np.maximum(v, V_MIN_KMH / 3.6)
    ds = np.diff(ss)
    for i in range(len(v) - 2, -1, -1):
        v[i] = min(v[i], math.sqrt(v[i + 1] ** 2 + 2 * A_DEC * ds[i]))
    for i in range(1, len(v)):
        v[i] = min(v[i], math.sqrt(v[i - 1] ** 2 + 2 * A_ACC * ds[i - 1]))
    return v * 3.6


def scenario(seg, var, ss, Q, vk):
    d = Q[1] - Q[0]
    head = math.degrees(math.atan2(d[0], d[1]))
    # rear axle placed WB behind the first path point (steer axle on the path)
    t0 = d / np.linalg.norm(d)
    rear = Q[0] - t0 * WB
    dur = float(np.sum(np.diff(ss) / np.maximum(vk[:-1] / 3.6, 0.5))) + 20.0
    return {
        "schemaVersion": 1, "id": f"swept_{seg}_{var}",
        "description": f"Swept path {seg} ({var}), laden 40 t, Stanley path follower on the steer axle",
        "spec": "task 2026-11-10 swept path gate 3", "combination": "laden40",
        "initial": {"speedKmh": float(vk[0]), "gear": 0, "headingDeg": head, "x": float(rear[0]), "z": float(rear[1])},
        "duration": round(dur, 1), "sampleEvery": 1,
        "driver": {"type": "path", "stanleyGain": 1.5,
                   "path": [[round(float(x), 3), round(float(z), 3), round(float(v), 2)] for (x, z), v in zip(Q, vk)]},
        "checks": [],
    }


# ------------------------------------------------------------------------------------------------ surface raster
MAIN = Path(str(REPO).split(os.sep + ".claude" + os.sep + "worktrees")[0])   # worktrees: big binaries live in main


def _first(*cands):
    for c in cands:
        if c.exists() and c.stat().st_size > 1024:
            return c
    return cands[0]


WORLD = _first(REPO / "Data" / "raw" / "derived" / REGION / "world" / "chunk_0_0.glb",
               MAIN / "Data" / "raw" / "derived" / REGION / "world" / "chunk_0_0.glb").parent
PROPS = _first(REPO / "art-source" / "world" / "props" / "street_props.glb",
               MAIN / "art-source" / "world" / "props" / "street_props.glb")


def surface_raster(lo, hi):
    world = WORLD
    nx, ny = int(math.ceil((hi[0] - lo[0]) / RES)), int(math.ceil((hi[1] - lo[1]) / RES))
    cat = np.zeros((ny, nx), np.uint8)
    zb = np.full((ny, nx), -1e9)
    for f in sorted(world.glob("chunk_*_*.glb")):
        if f.name.endswith(".low.glb"):
            continue
        doc, data, binoff = RC.read_glb(f)
        for node in ("road", "paved"):
            for mat, T in RC.node_triangles(doc, data, binoff, node).items():
                if mat in CARRIAGEWAY:
                    c = CAT["carriageway"]
                elif mat == "apron_sett":
                    c = CAT["apron"]
                elif mat == "curb_concrete":
                    c = CAT["kerb"]
                elif mat.startswith(("marking", "decal", "drain")):
                    continue
                else:
                    c = CAT["side"]
                sel = (T[:, :, 0].max(1) >= lo[0]) & (T[:, :, 0].min(1) <= hi[0]) & \
                      (T[:, :, 1].max(1) >= lo[1]) & (T[:, :, 1].min(1) <= hi[1])
                for tri in T[sel]:
                    _raster_tri(tri, c, cat, zb, lo, nx, ny)
    return cat, world, zb


def _raster_tri(tri, c, cat, zb, lo, nx, ny):
    xy = (tri[:, :2] - lo) / RES - 0.5
    i0, i1 = max(0, int(math.floor(xy[:, 0].min()))), min(nx - 1, int(math.ceil(xy[:, 0].max())))
    j0, j1 = max(0, int(math.floor(xy[:, 1].min()))), min(ny - 1, int(math.ceil(xy[:, 1].max())))
    if i1 < i0 or j1 < j0:
        return
    (x0, y0), (x1, y1), (x2, y2) = xy
    den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    if abs(den) < 1e-9:
        return
    X, Y = np.meshgrid(np.arange(i0, i1 + 1), np.arange(j0, j1 + 1))
    a = ((y1 - y2) * (X - x2) + (x2 - x1) * (Y - y2)) / den
    b = ((y2 - y0) * (X - x2) + (x0 - x2) * (Y - y2)) / den
    g = 1 - a - b
    m = (a >= -1e-6) & (b >= -1e-6) & (g >= -1e-6)
    if not m.any():
        return
    z = a * tri[0, 2] + b * tri[1, 2] + g * tri[2, 2]
    sub_z = zb[j0:j1 + 1, i0:i1 + 1]
    upd = m & (z > sub_z)
    sub_z[upd] = z[upd]
    cat[j0:j1 + 1, i0:i1 + 1][upd] = c


OVERHEAD_M = 4.5     # a prop standing this far above the road surface under it is on a deck overhead (vehicle 4.0 m)


def props_near(world, lo, hi, zb=None, skipped=None):
    """Prop collider footprints in the window. ADR 0123: with `zb` (top z of the road / paved surfaces per raster
    cell, bridge decks are another node) a prop whose base stands more than OVERHEAD_M above the road surface under
    it is on a viaduct overhead (lamps on the Andersa decks above Rondo Biezenstwa, 5.9 m over the ring) and is not
    an obstacle of the road below - the analysis is 2-D and read them as posts on the truck apron."""
    boxes = RC.prop_boxes(PROPS)
    out = []
    for f in sorted(world.glob("instances_*_*.json")):
        for it in json.loads(f.read_text(encoding="utf-8"))["instances"]:
            b = boxes.get(it["p"])
            if b is None or not (lo[0] <= it["e"] <= hi[0] and lo[1] <= it["n"] <= hi[1]):
                continue
            if zb is not None and "z" in it:
                i, j = int((it["e"] - lo[0]) / RES), int((it["n"] - lo[1]) / RES)
                r_ = max(1, int(round(0.6 / RES)))
                win = zb[max(0, j - r_):j + r_ + 1, max(0, i - r_):i + r_ + 1]
                win = win[win > -1e8]
                if win.size and it["z"] - float(win.max()) > OVERHEAD_M:
                    if skipped is not None:
                        skipped.append({"p": it["p"], "e": it["e"], "n": it["n"], "z": it["z"],
                                        "road_z": round(float(win.max()), 2)})
                    continue
            yaw = it.get("yaw", 0.0)
            ca, sa = math.cos(yaw), math.sin(yaw)
            C = np.array([[x, y] for x in (b[0], b[3]) for y in (b[1], b[4])])
            W = np.column_stack([it["e"] + C[:, 0] * ca - C[:, 1] * sa, it["n"] + C[:, 0] * sa + C[:, 1] * ca])
            out.append((it["p"], W[[0, 1, 3, 2]]))
    return out


# ------------------------------------------------------------------------------------------------ poses
def load_poses(csv_path):
    import csv
    with open(csv_path, newline="", encoding="utf-8") as fh:
        rd = csv.reader(fh)
        h = next(rd)
        ix = {k: h.index(k) for k in ("t", "x", "z", "heading_deg", "speed_kmh", "articulation_deg", "trailer_x",
                                      "trailer_z", "steer_angle_deg", "a_lat")}
        rows = np.array([[float(r[ix[k]]) for k in ix] for r in rd])
    return {k: rows[:, i] for i, k in enumerate(ix)}


def frames(P):
    """Tractor frame (origin rear axle) and trailer frame (origin below kingpin): origin + forward unit (E, N)."""
    psi = np.radians(P["heading_deg"])
    fT = np.column_stack([np.sin(psi), np.cos(psi)])
    oT = np.column_stack([P["x"], P["z"]])
    kp = oT + fT * FW_LEAD
    tr = np.column_stack([P["trailer_x"], P["trailer_z"]])
    # trailer heading from its body position (origin below kingpin -> trailer x/z is that origin) is degenerate;
    # use the articulation with the sign that puts the trailer axle behind the kingpin consistently
    best = None
    for sg in (1.0, -1.0):
        ps = psi - sg * np.radians(P["articulation_deg"])
        fS = np.column_stack([np.sin(ps), np.cos(ps)])
        err = np.median(np.linalg.norm(tr - kp, axis=1))
        # the right sign makes the tridem centre move along the trailer axis (no side slip at walking-pace
        # off-tracking); the wrong one is off by twice the articulation
        ax_ = tr + fS * (-7.70)
        v = np.gradient(ax_, axis=0)
        sp = np.linalg.norm(v, axis=1)
        mv = sp > 1e-3
        dirn = np.mean(np.sum(v[mv] / sp[mv, None] * fS[mv], axis=1))
        if best is None or dirn > best[0]:
            best = (dirn, fS, err)
    return (oT, fT), (tr, best[1]), best[2], best[0]


def pts(frame, z, x):
    o, f = frame
    r = np.column_stack([f[:, 1], -f[:, 0]])      # right
    return o + f * z + r * x


# ------------------------------------------------------------------------------------------------ analysis
def analyse(P, cat, lo, props, ss_win, Q, ss):
    (fT, fS) = None, None
    tract, trail, kp_err, dirn = frames(P)
    ok = (cat == CAT["carriageway"]) | (cat == CAT["apron"])
    cw = cat == CAT["carriageway"]
    d_in = ndimage.distance_transform_edt(ok) * RES
    d_out = ndimage.distance_transform_edt(~ok) * RES
    d_cw_out = ndimage.distance_transform_edt(~cw) * RES   # distance from apron cells to carriageway
    ny, nx = cat.shape

    def sample(arr, p):
        i = np.clip(((p[:, 0] - lo[0]) / RES).astype(int), 0, nx - 1)
        j = np.clip(((p[:, 1] - lo[1]) / RES).astype(int), 0, ny - 1)
        return arr[j, i]

    # station of each sample (steer-axle projection on the route) to restrict to the analysed window
    front = pts(tract, WB, 0.0)
    from scipy.spatial import cKDTree
    idx, cur = np.zeros(len(front), int), 0
    for n_, p_ in enumerate(front):                 # progressive nearest point (a full lap revisits points)
        j1 = min(len(Q), cur + 60)
        cur = max(0, cur - 5) + int(np.argmin(np.hypot(Q[max(0, cur - 5):j1, 0] - p_[0], Q[max(0, cur - 5):j1, 1] - p_[1])))
        idx[n_] = cur
    st = ss[idx]
    # monotone progress (a full circulation revisits the same points) + stop at the path end
    prog = np.maximum.accumulate(np.searchsorted(ss, st))
    win = (P["t"] > 2.0) & (st >= ss_win[0]) & (st <= ss_win[1]) & (P["speed_kmh"] > 1.0)
    del prog
    res = {"kingpin_consistency_m": float(kp_err), "trailer_dir_cos": float(dirn), "tyres": {}, "body": {}}
    tracks = {}
    for name, (fr, z, xc, hw) in TYRES.items():
        frame = tract if fr == "T" else trail
        worst = None
        for side in (-1, 1):
            for off in (-hw, 0.0, hw):
                p = pts(frame, z, side * (xc + off))
                clr = sample(d_in, p) - sample(d_out, p)
                c = sample(cat, p)
                apr = np.where(c == CAT["apron"], sample(d_cw_out, p), 0.0)
                if off == hw:
                    tracks[(name, side)] = p
                k = np.where(win)[0]
                i = k[np.argmin(clr[k])]
                ia = k[np.argmax(apr[k])]
                cand = {"min_clear_m": round(float(clr[i]), 2), "at_s_m": round(float(st[i]), 1),
                        "at_en": [round(float(p[i, 0]), 1), round(float(p[i, 1]), 1)],
                        "side": "R" if side > 0 else "L", "surface": [k_ for k_, v in CAT.items() if v == c[i]][0],
                        "max_apron_m": round(float(apr[ia]), 2), "apron_at_s_m": round(float(st[ia]), 1),
                        "off_frac": round(float(np.mean(~np.isin(c[k], (1, 2)))), 4)}
                if worst is None or cand["min_clear_m"] < worst["min_clear_m"]:
                    keep_ap = max(worst["max_apron_m"], cand["max_apron_m"]) if worst else cand["max_apron_m"]
                    worst = cand
                    worst["max_apron_m"] = keep_ap
                else:
                    worst["max_apron_m"] = max(worst["max_apron_m"], cand["max_apron_m"])
        res["tyres"][name] = worst
    body_pts = {}
    for name, (fr, z, xc) in BODY.items():
        frame = tract if fr == "T" else trail
        worst = None
        for side in (-1, 1):
            p = pts(frame, z, side * xc)
            body_pts[(name, side)] = p
            over = sample(d_out, p)                   # how far beyond the carriageway+apron edge
            k = np.where(win)[0]
            i = k[np.argmax(over[k])]
            pd = np.full(len(p), 99.0)
            for _, poly in props:
                c = poly.mean(0)
                near = np.hypot(p[:, 0] - c[0], p[:, 1] - c[1]) < 8.0
                if near.any():
                    pd[near] = np.minimum(pd[near], _dist_poly(p[near], poly))
            j = k[np.argmin(pd[k])]
            cand = {"max_overhang_beyond_edge_m": round(float(over[i]), 2), "at_s_m": round(float(st[i]), 1),
                    "side": "R" if side > 0 else "L", "min_prop_clear_m": round(float(pd[j]), 2),
                    "prop_at_s_m": round(float(st[j]), 1)}
            if worst is None:
                worst = cand
            else:
                if cand["max_overhang_beyond_edge_m"] > worst["max_overhang_beyond_edge_m"]:
                    worst.update({k_: cand[k_] for k_ in ("max_overhang_beyond_edge_m", "at_s_m", "side")})
                if cand["min_prop_clear_m"] < worst["min_prop_clear_m"]:
                    worst.update({k_: cand[k_] for k_ in ("min_prop_clear_m", "prop_at_s_m")})
        res["body"][name] = worst
    k = np.where(win)[0]
    res["max_articulation_deg"] = round(float(np.max(np.abs(P["articulation_deg"][k]))), 1)
    res["max_steer_deg"] = round(float(np.max(np.abs(P["steer_angle_deg"][k]))), 1)
    res["speed_kmh_min_max"] = [round(float(P["speed_kmh"][k].min()), 1), round(float(P["speed_kmh"][k].max()), 1)]
    res["max_a_lat"] = round(float(np.max(np.abs(P["a_lat"][k]))), 2)
    res["path_err_m"] = round(float(np.max(np.hypot(*(front[k] - Q[idx[k]]).T))), 2)
    return res, tracks, body_pts, st, win


def _dist_poly(p, poly):
    """distance of points to a convex quad (0 inside)"""
    d = np.full(len(p), np.inf)
    inside = np.ones(len(p), bool)
    for a, b in zip(poly, np.roll(poly, -1, axis=0)):
        ab = b - a
        t = np.clip(((p - a) @ ab) / max(ab @ ab, 1e-12), 0, 1)
        d = np.minimum(d, np.linalg.norm(p - (a + t[:, None] * ab), axis=1))
        cr = ab[0] * (p[:, 1] - a[1]) - ab[1] * (p[:, 0] - a[0])
        inside &= cr >= 0
    inside2 = np.ones(len(p), bool)
    for a, b in zip(poly, np.roll(poly, -1, axis=0)):
        ab = b - a
        inside2 &= (ab[0] * (p[:, 1] - a[1]) - ab[1] * (p[:, 0] - a[0])) <= 0
    d[inside | inside2] = 0.0
    return d


# ------------------------------------------------------------------------------------------------ plot
def plot(path, title, cat, lo, centre, half, tracks, body_pts, win, Q, props, worst_pts):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    i0 = int((centre[0] - half - lo[0]) / RES); i1 = int((centre[0] + half - lo[0]) / RES)
    j0 = int((centre[1] - half - lo[1]) / RES); j1 = int((centre[1] + half - lo[1]) / RES)
    sub = cat[max(j0, 0):j1, max(i0, 0):i1]
    cmap = ListedColormap(["#f2efe6", "#9a9a9a", "#c9a27a", "#3a3a3a", "#d8d4c4"])
    fig, ax = plt.subplots(figsize=(8.5, 8.5), dpi=120)
    ext = (lo[0] + max(i0, 0) * RES, lo[0] + i1 * RES, lo[1] + max(j0, 0) * RES, lo[1] + j1 * RES)
    ax.imshow(sub, origin="lower", extent=ext, cmap=cmap, vmin=0, vmax=4, interpolation="nearest")
    for _, poly in props:
        if abs(poly[0, 0] - centre[0]) < half and abs(poly[0, 1] - centre[1]) < half:
            ax.fill(poly[:, 0], poly[:, 1], color="#7a1fa2", lw=0)
    ax.plot(Q[:, 0], Q[:, 1], color="white", lw=0.8, ls="--", label="route (steer-axle reference)")
    k = np.where(win)[0]
    # body envelope: outline every 0.5 s
    for name, col in (("tractor", "#1f5fa8"), ("trailer", "#c0392b")):
        pass
    step = max(1, len(k) // 400)
    for i in k[::step]:
        tq = [body_pts[("bumper", -1)][i], body_pts[("bumper", 1)][i], body_pts[("cab_back", 1)][i],
              body_pts[("cab_back", -1)][i]]
        sq = [body_pts[("trailer_front", -1)][i], body_pts[("trailer_front", 1)][i],
              body_pts[("trailer_rear", 1)][i], body_pts[("trailer_rear", -1)][i]]
        for q, col in ((tq, "#1f5fa8"), (sq, "#c0392b")):
            q = np.array(q + [q[0]])
            ax.plot(q[:, 0], q[:, 1], color=col, lw=0.25, alpha=0.18)
    styles = {"steer": ("#0b3d91", 1.4), "drive_o": ("#2e86de", 1.2), "trl_1": ("#e67e22", 1.0),
              "trl_3": ("#a93226", 1.4)}
    for (name, side), p in tracks.items():
        if name not in styles:
            continue
        c, lw = styles[name]
        ax.plot(p[k, 0], p[k, 1], color=c, lw=lw, label=f"{name} outer tyre edge" if side > 0 else None)
    for (x, y, lab) in worst_pts:
        ax.plot(x, y, "o", ms=9, mfc="none", mec="#ff00aa", mew=2)
        ax.annotate(lab, (x, y), xytext=(6, 6), textcoords="offset points", fontsize=8, color="#ff00aa")
    ax.set_xlim(centre[0] - half, centre[0] + half)
    ax.set_ylim(centre[1] - half, centre[1] + half)
    ax.set_aspect("equal")
    ax.set_xlabel("E [m] (region-local)"); ax.set_ylabel("N [m]")
    ax.set_title(title, fontsize=10)
    from matplotlib.patches import Patch
    h, l = ax.get_legend_handles_labels()
    h += [Patch(color=c) for c in ("#9a9a9a", "#c9a27a", "#3a3a3a", "#d8d4c4", "#7a1fa2")]
    l += ["carriageway", "truck apron", "kerb top", "sidewalk/verge", "prop collider"]
    ax.legend(h, l, loc="lower left", fontsize=7, framealpha=0.85)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


# ------------------------------------------------------------------------------------------------ main
def run(out: Path, build=True):
    out.mkdir(parents=True, exist_ok=True)
    segdoc = json.loads(SEGMENTS.read_text(encoding="utf-8"))
    rings = {k: (np.array(v["centre_en"]), v["radius_m"]) for k, v in segdoc["ring_fits"].items()}
    scen_dir = out / "scenarios"
    scen_dir.mkdir(exist_ok=True)
    lines = {}
    for seg, (s0, s1, w) in RUNS.items():
        ss, Q0, vmax = route_line(s0, s1)
        for ln in LINES:
            Q = Q0 if ln == "lane" else wide_line(Q0)
            for var, cap in VARIANTS.items():
                vk = speed_profile(ss, Q, vmax, rings.values(), cap)
                (scen_dir / f"swept_{seg}_{ln}-{var}.json").write_text(
                    json.dumps(scenario(seg, f"{ln}-{var}", ss, Q, vk)), encoding="utf-8")
            lines[(seg, ln)] = (ss, Q, w)
    # full circulation of Rondo Bieżeństwa (the route itself only takes the first exit at both roundabouts)
    c, rr = rings["bieżeństwa"]
    ss, Q = ring_line(c, rr)
    for var, cap in VARIANTS.items():
        vk = speed_profile(ss, Q, np.full(len(ss), 50.0), [(c, rr)], cap, ring_fixed=True)
        (scen_dir / f"swept_RING-B_lane-{var}.json").write_text(
            json.dumps(scenario("RING-B", f"lane-{var}", ss, Q, vk)), encoding="utf-8")
    lines[("RING-B", "lane")] = (ss, Q, (60.0, ss[-1] - 5.0))
    dn = dotnet()
    proj = REPO / "tools" / "physics-runner" / "Runner"
    if build:
        subprocess.run(dn + ["build", "-c", "Release", str(proj)], check=True, capture_output=True)
    r = subprocess.run(dn + ["run", "-c", "Release", "--no-build", "--project", str(proj), "--", "--scenarios",
                             str(scen_dir), "--no-multi", "--out", str(out)], capture_output=True, text=True)
    if r.returncode not in (0, 1):
        raise RuntimeError(r.stdout + r.stderr)
    allQ = np.concatenate([q for _, q, _ in lines.values()] +
                          [np.array([c - (r + 45.0), c + (r + 45.0)]) for c, r in rings.values()])
    lo, hi = np.floor(allQ.min(0) - 40.0), np.ceil(allQ.max(0) + 40.0)
    summary = {"res_m": RES, "segments": {}}
    cache = out / "surface.npz"
    if cache.exists() and np.allclose(np.load(cache)["lo"], lo):
        cat, world = np.load(cache)["cat"], WORLD
        zb = np.load(cache)["zb"] if "zb" in np.load(cache).files else None
    else:
        cat, world, zb = surface_raster(lo, hi)
        np.savez_compressed(cache, cat=cat, lo=lo, zb=zb)
    overhead = []
    props = props_near(world, lo, hi, zb, overhead)
    summary["props_overhead_skipped"] = overhead
    ring_of = {"G3-A": "bieżeństwa", "G3-B": "putry", "RING-B": "bieżeństwa"}
    for (seg, ln), (ss, Q, w) in lines.items():
        for var in VARIANTS:
            var = f"{ln}-{var}"
            P = load_poses(out / f"swept_{seg}_{var}.csv")
            res, tracks, body_pts, st, win = analyse(P, cat, lo, props, w, Q, ss)
            summary["segments"][f"{seg}_{var}"] = res
            # ring window plot
            rname = ring_of[seg]
            c, rr = rings[rname]
            worst = []
            for nm, t in res["tyres"].items():
                if t["min_clear_m"] < 0.3 and np.hypot(t["at_en"][0] - c[0], t["at_en"][1] - c[1]) < 70:
                    worst.append((t["at_en"][0], t["at_en"][1], f"{nm} {t['min_clear_m']:+.2f} m"))
            plot(out / f"plot_{seg}_{rname}_{var}.png",
                 f"{seg} {var}: Rondo {rname.capitalize()} (ring R={rr:.1f} m), laden 40 t, 16.47 m artic\n"
                 f"tyre tracks (outer edges), body outline every step-sample; circles = min tyre clearance < 0.3 m",
                 cat, lo, c, rr + 38.0, tracks, body_pts, win, Q, props, worst)
    (out / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    return summary


def table(summary):
    rows = []
    for key, res in summary["segments"].items():
        for nm, t in res["tyres"].items():
            rows.append(f"{key:10s} tyre {nm:8s} min clear {t['min_clear_m']:+5.2f} m @ s={t['at_s_m']:6.1f} {t['side']} "
                        f"({t['surface']}), apron max {t['max_apron_m']:.2f} m @ s={t['apron_at_s_m']}, off-frac {t['off_frac']}")
        for nm, b in res["body"].items():
            rows.append(f"{key:10s} body {nm:13s} overhang beyond edge {b['max_overhang_beyond_edge_m']:.2f} m @ s={b['at_s_m']} {b['side']}, "
                        f"min prop clear {b['min_prop_clear_m']:.2f} m @ s={b['prop_at_s_m']}")
        rows.append(f"{key:10s} artic max {res['max_articulation_deg']} deg, steer max {res['max_steer_deg']} deg, "
                    f"v {res['speed_kmh_min_max']} km/h, a_lat max {res['max_a_lat']}, steer-axle path err max {res['path_err_m']} m, "
                    f"kingpin check {res['kingpin_consistency_m']:.3f} m")
    return "\n".join(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = Path(a.out) if a.out else REPO / "artifacts" / "swept" / datetime.now().strftime("%Y%m%d-%H%M%S")
    print(table(run(out.resolve())))
    print(out)
