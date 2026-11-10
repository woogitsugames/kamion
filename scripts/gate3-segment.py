"""Define the Gate 3 quality-sample segments and their control cameras from the road graph (read-only inputs).

    python scripts/gate3-segment.py --region bialystok-industrial-c [--heightmap <heightmap_2049.r16>]

Reads  Data/Regions/<id>/route_start.json (scripts/export-route.py output: the exact polyline the route autopilot
       follows), roads.graph.json (node ids, ring edges), region.yaml (origin), buildings.geojson,
       heightmap_2049.r16 (gitignored; default Data/raw/derived/<id>/, else --heightmap or $KAMION_HEIGHTMAP).
Writes Data/Regions/<id>/gate3_segment.json and gate3_cameras.json. Deterministic: same inputs -> same bytes.
It never touches generated/control_cameras.json (owned by the world importer).

Two segments, because gate -> Andersa -> Rondo Putry is ~1.4 km on the graph (docs/03 wants 300-500 m):
  G3-A  yard / Kwadrat Park gate -> Rondo Bieżeństwa -> start of the ramp to Andersa  (industrial zone, hero hall)
  G3-B  gen. Andersa final approach -> Rondo Putry entry                             (trunk road, viaducts, gantry)
Heights: bare-earth NMT under the route (WORKING_VALUE for road level; no edge on either segment is tagged bridge=yes in OSM, but the Putry ramp may still run on a structure - re-seat by raycast).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np
import yaml

REPO = Path(__file__).resolve().parents[1]
EYE_M = 2.5          # driver eye height above road (art-source/truck/dims.json, GATE-1 report)
EYE_STEP_M = 50.0    # driver-eye camera spacing along a segment
LOOK_AHEAD_M = 40.0
SPAWN_S_M = 12.0     # the game spawns the truck at s=12 m (WorldSceneBuilder spawnS); a camera there is INSIDE the cab (r6 W-N10)
TRUCK_CLEAR_M = 18.0  # eye cameras at the spawn are moved this far ahead (cab front is ~6 m ahead of the truck origin)

# (id, title, s_start, s_end) - s along route_start.json (m). Rationale in docs/plan/STAGE-3.md.
SEGMENTS = [
    ("G3-A", "Kwadrat Park yard -> depot gate -> Rondo Bieżeństwa -> ramp", 12.0, 450.0),
    ("G3-B", "gen. Andersa approach -> Rondo Putry entry", None, None),  # end = Putry entry node + 20 m, length 486 m
]
G3B_END_NODE, G3B_END_PAD, G3B_LENGTH = "n2629251371", 20.0, 486.0
GATE_NODE = "n1882887381"
RINGS = {"bieżeństwa": "Rondo Pamięci Bieżeństwa 1915 roku", "putry": "Rondo Krzysztofa Jakuba Putry"}

# CC0 owner-approved reference photos (docs/REFERENCES.md), viewed 2026-11-09.
PHOTOS = {
    "G3-A": [
        {"file": "20201102_152339_Rondo_Pamięci_Bieżeństwa_1915_roku_Białystok.jpg", "licence": "CC0", "camera": "photo_biezenstwa_ground",
         "shows": "Rondo Bieżeństwa under the Andersa viaduct: red deck edge, round piers, railing, planting, zebra P-10, lamps"},
    ],
    "G3-B": [
        {"file": "7204_May_2021_in_Białystok.jpg", "licence": "CC0", "camera": "g3b_rondo_putry_approach",
         "shows": "Andersa/Putry viaduct: green deck edge, yellow round piers, transparent noise screens, sign gantry, P-8 arrows, wet asphalt, kerb + paving-block path"},
        {"file": "7197_May_2021_in_Białystok.jpg", "licence": "CC0", "camera": "(street furniture / building)",
         "shows": "Al. Tysiąclecia: sign gantry, fire-station building behind a hedge, grass verge, lamp type (overcast)"},
        {"file": "20240626_103137_June_2024_in_Białystok.jpg", "licence": "CC0", "camera": "(sun, vegetation)",
         "shows": "same fire station in sun: mown verge, young trees on stakes, lattice pylon, paving-block cycle path"},
    ],
}
PHOTO_MOOD_ONLY = ["6972_December_2019_in_Białystok_Aleja_Tysiąclecia_Państwa_Polskiego.jpg (CC0, 'Droga wewnętrzna' sign, wet block paving)",
                   "20201223_141958/143208_Aleja_Tysiąclecia_Państwa_Polskiego.jpg (CC0, old houses, not on the segments)"]


def r3(x):
    return round(float(x), 3)


class Height:
    def __init__(self, path, bbox, ):
        self.ok = path is not None and Path(path).exists()
        self.bbox = bbox
        if self.ok:
            self.a = np.fromfile(path, dtype="<u2").reshape(2049, 2049)
            self.sha = hashlib.sha256(Path(path).read_bytes()).hexdigest()

    def z(self, x, y):  # EPSG:2180 metres, bilinear on the 1 m grid (row 0 = north edge)
        i, j = x - self.bbox[0], self.bbox[3] - y
        i0, j0 = int(math.floor(i)), int(math.floor(j))
        i0, j0 = min(max(i0, 0), 2047), min(max(j0, 0), 2047)
        fi, fj = i - i0, j - j0
        a = self.a
        v = (a[j0, i0] * (1 - fi) * (1 - fj) + a[j0, i0 + 1] * fi * (1 - fj) + a[j0 + 1, i0] * (1 - fi) * fj + a[j0 + 1, i0 + 1] * fi * fj)
        return 120.0 + float(v) * 0.000686655985351339


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="bialystok-industrial-c")
    ap.add_argument("--heightmap")
    a = ap.parse_args()
    rdir = REPO / "Data" / "Regions" / a.region
    region = yaml.safe_load((rdir / "region.yaml").read_text(encoding="utf-8"))
    ox, oy = region["origin"]["x"], region["origin"]["y"]
    bbox = [region["bbox"][k] for k in ("xmin", "ymin", "xmax", "ymax")]
    route_raw = (rdir / "route_start.json").read_bytes()
    route = json.loads(route_raw)
    graph = json.loads((rdir / "roads.graph.json").read_text(encoding="utf-8"))
    P = np.array(route["points_en"], dtype=float)
    step = route["step_m"]
    S = np.arange(len(P)) * step
    S[-1] = route["length_m"] if abs(route["length_m"] - S[-1]) < step else S[-1]
    hm_path = a.heightmap or os.environ.get("KAMION_HEIGHTMAP") or str(REPO / "Data/raw/derived" / a.region / "heightmap_2049.r16")
    H = Height(hm_path, bbox)

    nodes = {n["id"]: n for n in graph["nodes"]}

    def project_s(x, y):
        d = np.hypot(P[:, 0] - (x - ox), P[:, 1] - (y - oy))
        return float(S[int(d.argmin())]), float(d.min())

    def at(s):
        s = min(max(s, 0.0), S[-1])
        return np.array([np.interp(s, S, P[:, 0]), np.interp(s, S, P[:, 1])])

    def tangent(s):
        d = at(s + 2) - at(s - 2)
        return d / max(np.linalg.norm(d), 1e-9)

    def ground(en):
        return H.z(en[0] + ox, en[1] + oy) if H.ok else float("nan")

    node_s = {n: project_s(nodes[n]["x"], nodes[n]["y"]) for n in route["graph_nodes"]}
    ring_fit = {}
    for key, name in RINGS.items():
        pts = [p for e in graph["edges"] if e["attrs"].get("name", {}).get("v", "").startswith(name) for p in e["geometry"]]
        A_ = np.array(pts) - [ox, oy]
        M = np.c_[2 * A_, np.ones(len(A_))]
        sol = np.linalg.lstsq(M, (A_ ** 2).sum(1), rcond=None)[0]
        c = sol[:2]
        ring_fit[key] = {"centre_en": [r3(c[0]), r3(c[1])], "radius_m": r3(math.sqrt(sol[2] + c @ c)), "n_points": len(pts)}

    # ---- segment bounds
    bounds = {}
    for sid, _, s0, s1 in SEGMENTS:
        if sid == "G3-B":
            s1 = node_s[G3B_END_NODE][0] + G3B_END_PAD
            s1 = round(s1 / step) * step
            s0 = s1 - G3B_LENGTH
        bounds[sid] = (s0, s1)

    # ---- buildings near a segment
    from shapely.geometry import LineString, shape
    b = json.loads((rdir / "buildings.geojson").read_text(encoding="utf-8"))
    bld = [(f["id"], shape(f["geometry"]), f["properties"]) for f in b["features"]]

    edge_by_id = {e["id"]: e for e in graph["edges"]}
    out_segs, cams = [], []
    for sid, title, _, _ in SEGMENTS:
        s0, s1 = bounds[sid]
        idx = [i for i, s in enumerate(S) if s0 < s < s1]
        pts = [at(s0)] + [P[i] for i in idx] + [at(s1)]
        pts = np.array(pts)
        length = float(np.hypot(*np.diff(pts, axis=0).T).sum())
        sv = [s0] + [S[i] for i in idx] + [s1]
        graph_len = 0.0
        edges = []
        prev = None
        for i, e in enumerate(route["edge"]):
            if s0 <= S[i] <= s1 and e != prev:
                at_ = edge_by_id[e]["attrs"]
                edges.append({"edge": e, "s_from": r3(S[i]), "name": at_.get("name", {}).get("v"), "highway": at_["highway"]["v"],
                              "lanes": at_.get("lanes", {}).get("v"), "maxspeed_kmh": route["maxspeed_kmh"][i],
                              "oneway": at_["oneway"]["v"], "width_m": at_.get("width", {}).get("v"),
                              "low_confidence": edge_by_id[e].get("low_confidence", [])})
                prev = e
        line = LineString([(x + ox, y + oy) for x, y in pts])
        near = []
        for bid, g, pr in bld:
            d = g.distance(line)
            if d <= 80:
                near.append((pr.get("area_m2", 0), bid, round(d, 1), pr.get("function"), pr.get("height_confidence")))
        near.sort(reverse=True)
        landmarks = []
        for n, (sn, dist) in node_s.items():
            if s0 - 1 <= sn <= s1 + 1:
                lab = {GATE_NODE: "depot gate junction (entry/exit lanes split; gate kit 16 m inside, booms 3 m past the median nose)",
                       "n1882953898": "Rondo Bieżeństwa entry", "n1882953899": "Rondo Bieżeństwa exit (to ramp)",
                       G3B_END_NODE: "Rondo Putry ring node where the route joins (it does not circle the ring)",
                       "n2840742308": "Andersa gantry (sign_gantry override, 40 m before)"}.get(n)
                if lab:
                    landmarks.append({"node": n, "s_m": r3(sn), "label": lab, "off_route_m": r3(dist)})
        out_segs.append({
            "id": sid, "title": title, "s_start_m": r3(s0), "s_end_m": r3(s1), "length_m": r3(length),
            "length_graph_edges_m": None, "n_points": len(pts), "points_en": [[r3(x), r3(y)] for x, y in pts],
            "ground_z_nmt_m": [r3(ground(p)) for p in pts[::5]], "ground_z_note": "every 5th point, bare-earth NMT (not road surface)",
            "edges": edges, "landmarks": landmarks, "unity_launch": None,
            "buildings_within_80m": {"count": len(near), "largest": [{"id": n[1], "area_m2": n[0], "dist_m": n[2], "function": n[3], "height_confidence": n[4]} for n in near[:6]]},
            "reference_photos_cc0": PHOTOS[sid],
        })

    # ---- cameras
    def cam(cid, kind, seg, pos_en, pos_h, look_en, look_h, fov, note, **extra):
        d = {"id": cid, "type": "persp", "kind": kind, "segment": seg,
             "pos": [r3(pos_en[0]), r3(pos_en[1]), r3(pos_h)], "look_at": [r3(look_en[0]), r3(look_en[1]), r3(look_h)],
             "fov_deg": fov, "note": note}
        d.update(extra)
        cams.append(d)

    for sid, _, _, _ in SEGMENTS:
        s0, s1 = bounds[sid]
        tag = sid.lower().replace("-", "")
        # driver eye every 50 m
        k = 0
        s = s0
        while s <= s1 - 10:
            # id keeps the nominal s (comparable with earlier evidence); the camera itself is moved out of the truck if it sits at the spawn.
            sc = s + TRUCK_CLEAR_M if abs(s - SPAWN_S_M) < 1.0 else s
            p, la = at(sc), at(sc + LOOK_AHEAD_M)
            moved = f" (moved +{TRUCK_CLEAR_M:.0f} m ahead of the spawn so it is not inside the truck, W-N10)" if sc != s else ""
            cam(f"{tag}_eye_s{int(round(s)):04d}", "driver_eye", sid, p, ground(p) + EYE_M, la, ground(la) + 2.0, 60.0,
                f"driver eye {EYE_M} m on the autopilot line, {LOOK_AHEAD_M:.0f} m ahead, s={sc:.0f} m (+{sc - s0:.0f} m){moved}", s_m=r3(sc), truck_s_m=None)
            s += EYE_STEP_M
        # 3/4 exterior: truck centre at s_t, camera front-left
        marks = {"G3-A": [(40.0, "yard, hall and docks behind"), (214.0, "at the depot gate"), (338.0, "entering Rondo Bieżeństwa")],
                 "G3-B": [(s0 + 40, "Andersa, 3 lanes, noise screens"), (s0 + 250, "Andersa, ramp to Tysiąclecia"), (s1 - 60, "approach to Rondo Putry")]}[sid]
        for st, what in marks:
            st = round(st / step) * step
            t = tangent(st)
            left = np.array([-t[1], t[0]])
            c = at(st) + t * 14.0 + left * 9.0
            tgt = at(st) - t * 4.0
            cam(f"{tag}_ext34_s{int(st):04d}", "exterior_3q", sid, c, ground(c) + 2.2, tgt, ground(tgt) + 1.8, 50.0,
                f"3/4 front-left exterior of the combination, truck centre at s={st:.0f} m ({what}); camera 14 m ahead, 9 m left, 2.2 m up",
                s_m=r3(st), truck_s_m=r3(st))
        # rondo
        key = "bieżeństwa" if sid == "G3-A" else "putry"
        cx, cy = ring_fit[key]["centre_en"]
        c0 = np.array([cx, cy])
        entry_node = "n1882953898" if sid == "G3-A" else G3B_END_NODE
        se = node_s[entry_node][0]
        t = tangent(se - 5)
        a_ = at(se - 30)
        cam(f"{tag}_rondo_{key[:3]}_approach", "rondo_eye", sid, a_, ground(a_) + EYE_M, c0, ground(c0) + 2.5, 65.0,
            f"driver eye 30 m before the ring entry (s={se - 30:.0f} m), looking at the ring centre (circle fit r={ring_fit[key]['radius_m']} m)", s_m=r3(se - 30))
        ab = c0 - t * 55.0
        cam(f"{tag}_rondo_{key[:3]}_above", "rondo_above", sid, ab, ground(c0) + 45.0, c0, ground(c0) + 2.0, 55.0,
            "oblique from ~45 m up, 55 m back along the approach (same idea as control_cameras putry_above / biezenstwa_above)")
        if sid == "G3-B":
            # viaduct/gantry view matching CC0 7204_May_2021: from the Andersa lane, left-front, low
            tt = tangent(se - 120)
            pa = at(se - 120) + np.array([tt[1], -tt[0]]) * 6.0  # 6 m right of the autopilot line (verge)
            lk = at(se - 50)
            cam("g3b_rondo_putry_approach", "photo_match", sid, pa, ground(pa) + 1.6, lk, ground(lk) + 4.0, 60.0,
                "WORKING_VALUE viewpoint for the CC0 7204_May_2021 comparison (eye ~1.6 m from the verge looking up the road to the gantry); owner/lead may move it", s_m=r3(se - 120))
    reuse = ["photo_biezenstwa_ground", "biezenstwa_above", "stretch_03", "stretch_04", "kwadrat_park_gate", "driver_andersa_to_putry", "putry_above"]
    spec_cams = {
        "schema": "truck-sim-pl/gate3-cameras/1", "region": a.region,
        "frame": "local E,N,U (E,N = EPSG:2180 minus region origin; U absolute EVRF2007 = NMT ground + height above road). Same field names as generated/control_cameras.json.",
        "u_note": "U is bare-earth NMT + eye/camera height (WORKING_VALUE for road level). The importer should re-seat cameras by raycast on the imported road collision (pos.U = hit + height_above_road) if it can.",
        "heightmap_available": H.ok, "reuse_from_control_cameras": reuse,
        "lighting_set": ["overcast", "clear"], "tiers": ["Low", "Medium", "High"],
        "cameras": cams,
    }
    spec_seg = {
        "schema": "truck-sim-pl/gate3-segment/1", "region": a.region, "default_segment": "G3-A",
        "source": {"route_file": "Data/Regions/%s/route_start.json" % a.region, "route_sha256": hashlib.sha256(route_raw).hexdigest(),
                   "route_length_m": route["length_m"], "step_m": step,
                   "heightmap_sha256": H.sha if H.ok else None, "frame": route["frame"]},
        "why_two_segments": "Gate -> Andersa -> Rondo Putry is %.0f m on the route graph (gate s=%.0f, Andersa starts s=%.0f, Putry entry s=%.0f), too long for one 300-500 m sample; "
                            "see docs/plan/STAGE-3.md section 2." % (node_s[G3B_END_NODE][0] - node_s[GATE_NODE][0], node_s[GATE_NODE][0], node_s["n3341716402"][0], node_s[G3B_END_NODE][0]),
        "ring_fits": ring_fit, "node_s_m": {n: r3(v[0]) for n, v in node_s.items()},
        "segments": out_segs,
    }
    for seg in spec_seg["segments"]:
        # polyline length vs the sum of graph edge lengths between the same s range is not comparable (lane offset), so only report polyline.
        seg.pop("length_graph_edges_m")
    (rdir / "gate3_segment.json").write_text(json.dumps(spec_seg, ensure_ascii=False, indent=1, sort_keys=False) + "\n", encoding="utf-8")
    (rdir / "gate3_cameras.json").write_text(json.dumps(spec_cams, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for s_ in out_segs:
        print(f"{s_['id']}: s {s_['s_start_m']}..{s_['s_end_m']}  length {s_['length_m']} m, {s_['n_points']} pts, buildings<=80m {s_['buildings_within_80m']['count']}")
    print(f"cameras: {len(cams)} (heightmap {'yes' if H.ok else 'NO - U is NaN!'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
