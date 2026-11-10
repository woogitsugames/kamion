"""Hero depot hall: authored override `kind: hero_depot` (ADR 0071, pattern of streetscape.hero_bridge / ADR 0067).

The generic hall of one building (streetscape.buildings_mesh: sandwich-panel box by rule) is replaced by an authored
Blender asset that stands exactly on the data footprint:

  1. `plan()`   before the buildings are meshed: writes the *spec* of every hero depot - the BDOT10k / LoD1 footprint
                (annex protrusions split off the main wall ring), LoD1 height, smoothed ground under every facade,
                authored facade features (dock row, strip windows, louvres, doors, portals, downpipes), roof layout,
                segment cuts - to `Data/Regions/<id>/generated/landmarks/<asset>.spec.json` (git) and checks that the
                asset (`art-source/world/landmarks/<asset>/<asset>.glb` + `_meta.json`) was built from exactly this spec
                (sha256). A stale / missing asset is rebuilt with Blender when available (`KAMION_BLENDER` or `blender`
                on PATH, unless `KAMION_NO_BLENDER`); otherwise the building keeps its generic geometry and the override
                is reported stale (manifest `overrides_stale`, streetscape QA `hero_depots`).
  2. buildings_mesh.build() takes the dock rows of a hero building from the spec (same dict as docks_for(), so aprons,
                parked trailers, tyre scrub and yard props keep working) and, when the asset is ready, drops the
                building's visible layers (the collision prism stays).
  3. `apply()`  adds one point instance per asset segment (prototype `landmark_depot_<asset>_<k>`, LOD0/1/2 in the
                asset GLB), the dock bumper / annex collision boxes and the triangle counts for the frame estimate.

Dock geometry follows roads.standards (DOCK_FLOOR_H 1.20 m, DOCK_PITCH 4.0 m, door 3.0 x 3.0 m): the trailer physics
and the existing dock positions are unchanged. Every dimension without a source is a WORKING_VALUE in DEFAULTS or in the
override (`confidence`), read by eye off the GUGiK orthophoto and the CC0 street photos listed in the override.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import Point, Polygon

from roads import meshing as M
from roads import standards as S

REPO = Path(__file__).resolve().parents[3]
KIND = "hero_depot"
SCHEMA = "truck-sim-pl/hero-depot-spec/1"
BLENDER_SCRIPT = REPO / "tools" / "blender" / "world" / "landmarks" / "make_depot.py"
PROTO_PREFIX = "landmark_depot_"

# Metres. WORKING_VALUE unless a source is named (override `sources`).
DEFAULTS = {
    "segment_max_m": 46.0,
    "plinth_h_m": 0.60,            # precast concrete plinth above the ground outside the dock row
    "parapet_h_m": 0.45,           # attic above the roof membrane
    "parapet_t_m": 0.30,
    "coping_h_m": 0.30,            # graphite coping fascia (seen: dark band along the top edge, CC0 photo)
    "panel_course_m": 1.0,         # horizontal cladding course
    "strip_sill_m": 6.60,          # high-level strip windows: sill / height above the facade ground (CC0 photo
    "strip_h_m": 2.00,             # 20210904_101250: band height = gap to the coping; LoD1 height 10.2 m)
    "strip_frame_m": 0.22,         # vermilion frame bar
    "strip_mullion_m": 0.60,       # narrow upright panes
    "dock_floor_h_m": S.DOCK_FLOOR_H,
    "dock_pitch_m": S.DOCK_PITCH,
    "dock_door_w_m": S.DOCK_DOOR_W,
    "dock_door_h_m": S.DOCK_DOOR_H,
    "dock_shelter_w_m": S.DOCK_SHELTER_W,
    "dock_shelter_h_m": S.DOCK_SHELTER_H,
    "dock_shelter_d_m": S.DOCK_SHELTER_D,
    "bumper_proud_m": 0.12,
    "downpipe_d_m": 0.12,
    "skylight_pitch_m": [6.0, 6.0],   # orthophoto: staggered grid of small roof lights
    "skylight_size_m": 1.2,
    "court_roof_h_m": 5.0,         # light roof inside the inner ring (orthophoto: lighter, lower surface)
    "weathering": 1,               # generator revision of the wall run-off space (r11): bump to rebuild the asset
    "lod_ends_m": [100.0, 400.0, 20000.0],   # at lodBias 1 (InstanceImporter.Policy / build_world.instance_ends)
}


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _r(v, n=3):
    return round(float(v), n)


def _edges(ring):
    return [(np.asarray(ring[i], float), np.asarray(ring[(i + 1) % len(ring)], float)) for i in range(len(ring))]


def _find_annexes(ring, authored, origin):
    """Protrusions of the footprint (short, front, short with the two short edges antiparallel) whose front edge
    midpoint is within 4 m of an authored annex `at`. Returns ([(i_first_vertex, annex dict)], stale names)."""
    n = len(ring)
    out, stale = [], []
    for a in authored:
        at = np.asarray(a["at"], float) - origin
        best = None
        for i in range(n):
            p0, p1, p2, p3 = (np.asarray(ring[(i + k) % n], float) for k in range(4))
            l0, l1, l2 = (np.linalg.norm(q - p) for p, q in ((p0, p1), (p1, p2), (p2, p3)))
            if l0 > 6.0 or l2 > 6.0 or l0 < 0.8 or l2 < 0.8:
                continue
            if float(np.dot((p1 - p0) / l0, (p3 - p2) / l2)) > -0.95:
                continue
            d = float(np.linalg.norm((p1 + p2) / 2 - at))
            if d < 4.0 and (best is None or d < best[0]):
                best = (d, i)
        if best is None:
            stale.append(a["name"])
        else:
            out.append((best[1], a))
    return out, stale


def build_spec(o, bld, zsample, origin) -> tuple[dict | None, list]:
    """Spec of one hero depot. bld: buildings_mesh.load() entry; zsample(e[], n[]) -> smoothed ground height."""
    prm = {**DEFAULTS, **(o.get("set") or {})}
    poly = shapely.geometry.polygon.orient(bld["poly"])
    ring = [np.asarray(p, float) for p in list(poly.exterior.coords)[:-1]]
    stale = []
    annex_hits, st = _find_annexes(ring, o.get("annexes") or [], origin)
    stale += [f"annex:{x}" for x in st]
    drop = set()
    annexes = []
    n = len(ring)
    for i, a in annex_hits:
        p0, p1, p2, p3 = (ring[(i + k) % n] for k in range(4))
        drop |= {(i + 1) % n, (i + 2) % n}
        annexes.append({"name": a["name"], "style": a.get("style", "plain"), "h_m": _r(a.get("h_m", 3.4)),
                        "quad": [[_r(v[0]), _r(v[1])] for v in (p0, p1, p2, p3)],
                        "door": a.get("door"), "note": a.get("note")})
    main = Polygon([ring[i] for i in range(n) if i not in drop], [list(r.coords) for r in poly.interiors])
    main = shapely.geometry.polygon.orient(main.simplify(float(o.get("simplify_m", 0.6))))
    mring = [np.asarray(p, float) for p in list(main.exterior.coords)[:-1]]
    zg_all = zsample(np.array([p[0] for p in ring]), np.array([p[1] for p in ring]))
    zref = float(np.median(zg_all))
    h = float(bld["props"].get("height_m") or 10.0)
    edges = []
    facades = list(o.get("facades") or [])
    used = set()
    for i, (a, b) in enumerate(_edges(mring)):
        L = float(np.linalg.norm(b - a))
        d = (b - a) / L
        nout = np.array([d[1], -d[0]])
        us = np.unique(np.concatenate([np.arange(0.0, L, 4.0), [L]]))
        q = a[None, :] + d[None, :] * us[:, None] + nout[None, :] * 1.5
        zg = zsample(q[:, 0], q[:, 1])
        e = {"i": i, "a": [_r(a[0]), _r(a[1])], "b": [_r(b[0]), _r(b[1])], "L": _r(L),
             "ground": [[_r(u, 2), _r(z)] for u, z in zip(us, zg)], "name": f"e{i}", "features": {}}
        mid = (a + b) / 2
        for k, f in enumerate(facades):
            at = np.asarray(f["at"], float) - origin
            if k not in used and L > 3.0 and float(np.linalg.norm(mid - at)) < float(f.get("tol_m", 6.0)):
                used.add(k)
                e["name"] = f["name"]
                feats = {key: f[key] for key in ("docks", "strips", "louvres", "doors", "drive_doors", "office_windows",
                                                 "downpipes", "wall_lights", "ladders", "party", "note") if key in f}
                if "docks" in feats:
                    dk = dict(feats["docks"])
                    cnt = int(dk["count"])
                    pitch = float(dk.get("pitch_m", prm["dock_pitch_m"]))
                    # default = the rule of buildings_mesh.docks_for (centred on the ORIGINAL footprint edge)
                    u0 = float(dk["first_u_m"]) if dk.get("first_u_m") is not None else None
                    if u0 is None:
                        le = float(dk.get("centre_on_len_m", L))
                        u0 = (le - (cnt - 1) * pitch) / 2
                    m3 = a + d * (float(dk.get("centre_on_len_m", L)) / 2) + nout * 3.0
                    yz = float(zsample(np.array([m3[0]]), np.array([m3[1]]))[0])
                    feats["docks"] = {"count": cnt, "pitch_m": _r(pitch), "first_u_m": _r(u0), "yard_z": _r(yz),
                                      "first_num": int(dk.get("first_num", 1)),
                                      "open": {str(k_): float(v_) for k_, v_ in (dk.get("open") or {}).items()},
                                      "missing_guides": [int(x) for x in dk.get("missing_guides") or []]}
                e["features"] = feats
        edges.append(e)
    stale += [f"facade:{f['name']}" for k, f in enumerate(facades) if k not in used]
    # annex -> edge + station of its base on the main ring
    for ax in annexes:
        c = (np.asarray(ax["quad"][0]) + np.asarray(ax["quad"][3])) / 2
        best = min(edges, key=lambda e: Point(*c).distance(shapely.LineString([e["a"], e["b"]])))
        a = np.asarray(best["a"])
        d = (np.asarray(best["b"]) - a) / best["L"]
        u0, u1 = sorted(float(np.dot(np.asarray(ax["quad"][k]) - a, d)) for k in (0, 3))
        ax.update({"edge": best["i"], "u": [_r(u0), _r(u1)],
                   "depth_m": _r(np.linalg.norm(np.asarray(ax["quad"][1]) - np.asarray(ax["quad"][0])))})
    # segments: every main edge cut into pieces <= segment_max_m at stations clear of openings
    segs = []
    for e in edges:
        L = e["L"]
        ncut = max(1, int(math.ceil(L / prm["segment_max_m"])))
        busy = _busy(e, annexes, prm)
        cuts = [0.0]
        for k in range(1, ncut):
            u = L * k / ncut
            for dlt in sorted(np.arange(0.0, 8.0, 0.25).tolist() + (-np.arange(0.25, 8.0, 0.25)).tolist(), key=abs):
                if all(not (b0 - 0.4 < u + dlt < b1 + 0.4) for b0, b1 in busy):
                    u += dlt
                    break
            cuts.append(_r(u))
        cuts.append(L)
        for u0, u1 in zip(cuts[:-1], cuts[1:]):
            a = np.asarray(e["a"])
            d = (np.asarray(e["b"]) - a) / L
            c = a + d * (u0 + u1) / 2
            segs.append({"edge": e["i"], "u": [_r(u0), _r(u1)], "anchor": [_r(c[0]), _r(c[1]), _r(zref)]})
    cen = np.asarray(main.representative_point().coords[0])
    roof = dict(o.get("roof") or {})
    patches = []
    for p in roof.get("patches") or []:
        patches.append({"mat": p["mat"], "ring": [[_r(x - origin[0]), _r(y - origin[1])] for x, y in p["ring_epsg2180"]]})
    spec = {
        "schema": SCHEMA, "id": o["id"], "asset": o["asset"], "building": o["building"],
        "frame": "local E, N (EPSG:2180 minus region origin), U absolute EVRF2007; metres",
        "params": {k: prm[k] for k in sorted(prm)},
        "zref": _r(zref), "zbot": _r(min(float(np.min(zg_all)), min(z for e in edges for _, z in e["ground"])) - 0.5), "h_m": _r(h), "ztop": _r(zref + h),
        "ring": [[_r(p[0]), _r(p[1])] for p in mring],
        "holes": [[[_r(p[0]), _r(p[1])] for p in list(r.coords)[:-1]] for r in main.interiors],
        "footprint_ring": [[_r(p[0]), _r(p[1])] for p in ring],
        "edges": edges, "annexes": annexes, "segments": segs,
        "roof": {"anchor": [_r(cen[0]), _r(cen[1]), _r(zref)], "patches": patches,
                 "vents": int(roof.get("vents", 14)), "skylights": bool(roof.get("skylights", True))},
        "style": o.get("style") or {},
        "confidence": o.get("confidence_detail") or {},
    }
    return spec, stale


def _busy(e, annexes, prm):
    """[u0, u1] intervals of an edge that a segment cut must avoid."""
    f = e["features"]
    out = []
    if "docks" in f:
        dk = f["docks"]
        for k in range(dk["count"]):
            u = dk["first_u_m"] + k * dk["pitch_m"]
            out.append((u - prm["dock_shelter_w_m"] / 2 - 0.2, u + prm["dock_shelter_w_m"] / 2 + 0.2))
    for key, half in (("doors", 0.8), ("drive_doors", 2.4)):
        for dr in f.get(key) or []:
            w = float(dr.get("w_m", half * 2)) / 2 + 0.3
            out.append((dr["u_m"] - w, dr["u_m"] + w))
    for ax in annexes:
        if ax.get("edge") == e["i"]:
            out.append((ax["u"][0] - 0.3, ax["u"][1] + 0.3))
    return out


def dock_rows(spec) -> list:
    """Dock rows of the spec in the dict shape of buildings_mesh.docks_for()."""
    prm = spec["params"]
    out = []
    for e in spec["edges"]:
        dk = e["features"].get("docks")
        if not dk:
            continue
        a, b = np.asarray(e["a"]), np.asarray(e["b"])
        d = (b - a) / e["L"]
        nout = np.array([d[1], -d[0]])
        docks = [{"u": dk["first_u_m"] + k * dk["pitch_m"], "num": dk["first_num"] + k} for k in range(dk["count"])]
        a0 = a + d * (docks[0]["u"] - 2.5)
        a1 = a + d * (docks[-1]["u"] + 2.5)
        apron = Polygon([a0, a1, a1 + nout * S.DOCK_APRON_L, a0 + nout * S.DOCK_APRON_L])
        out.append({"id": f"{spec['building']}:docks{e['i']}", "edge": (a, b), "docks": docks, "yard_z": dk["yard_z"],
                    "apron": apron, "hero": spec["id"], "bumper_proud": prm["bumper_proud_m"]})
    return out


def asset_paths(asset: str):
    d = REPO / "art-source" / "world" / "landmarks" / asset
    return d, d / f"{asset}.glb", d / f"{asset}_meta.json"


def spec_path(region_id: str, asset: str) -> Path:
    return REPO / "Data" / "Regions" / region_id / "generated" / "landmarks" / f"{asset}.spec.json"


def _asset_meta(asset, sha):
    _, glb, meta = asset_paths(asset)
    if not (glb.exists() and meta.exists()):
        return None, "missing"
    m = json.loads(meta.read_text(encoding="utf-8"))
    if m.get("spec_sha256") != sha:
        return None, "stale"
    if m.get("glb_sha256") != hashlib.sha256(glb.read_bytes()).hexdigest():
        return None, "glb_changed"
    return m, "ok"


def _blender():
    exe = os.environ.get("KAMION_BLENDER") or shutil.which("blender")
    return exe if exe and Path(exe).exists() else None


def rebuild_asset(spec_file: Path, log) -> bool:
    exe = _blender()
    if exe is None or os.environ.get("KAMION_NO_BLENDER"):
        return False
    log(f"hero depot: asset stale -> blender {BLENDER_SCRIPT.name}")
    r = subprocess.run([exe, "-b", "--factory-startup", "-P", str(BLENDER_SCRIPT), "--", "--spec", str(spec_file)],
                       capture_output=True, text=True)
    if r.returncode != 0 or "DEPOT_RESULT: OK" not in r.stdout:
        log("hero depot: blender failed:", (r.stdout + r.stderr)[-600:])
        return False
    return True


def plan(w, region_id, overrides, blds, zsample, log=lambda *a: None) -> dict:
    """{building id: {override, spec, meta | None, sha, docks}} for every hero depot whose building exists.
    meta is None when the asset does not match the spec (generic geometry kept, override reported stale)."""
    out = {}
    rep = w.stats.setdefault("hero_depots", {"applied": [], "stale": []})
    origin = np.asarray(w.origin, float)
    by_id = {b["id"]: b for b in blds}
    for o in overrides:
        if o.get("kind") != KIND:
            continue
        bld = by_id.get(o["building"])
        if bld is None:
            rep["stale"].append({"id": o["id"], "why": "building not in buildings.geojson"})
            w.net.overrides_stale.append(o["id"])
            continue
        spec, stale = build_spec(o, bld, zsample, origin)
        sp = spec_path(region_id, o["asset"])
        sp.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(spec, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
        if not sp.exists() or sp.read_text(encoding="utf-8") != text:
            sp.write_text(text, encoding="utf-8", newline="\n")
        sha = _sha(spec)
        meta, why = _asset_meta(o["asset"], sha)
        if meta is None and why != "glb_changed" and rebuild_asset(sp, log):
            meta, why = _asset_meta(o["asset"], sha)
        if meta is None:
            rep["stale"].append({"id": o["id"], "why": f"asset {why}: run blender -b --factory-startup -P "
                                 f"tools/blender/world/landmarks/make_depot.py -- --spec {sp.relative_to(REPO).as_posix()}"})
            w.net.overrides_stale.append(o["id"])
            log("hero depot", o["id"], "STALE:", why, "- generic geometry kept")
        if stale:
            rep["stale"].append({"id": o["id"], "why": "authored features without a matching footprint edge: " + ", ".join(stale)})
        out[o["building"]] = {"override": o, "spec": spec, "meta": meta, "sha": sha, "docks": dock_rows(spec),
                              "unmatched": stale}
    return out


def apply(w, heroes: dict, pl, log=lambda *a: None) -> dict:
    """Instances + collision of the hero depots whose asset is ready. Returns {prototype: {tris_lod0..2}}."""
    rep = w.stats.setdefault("hero_depots", {"applied": [], "stale": []})
    tris = {}
    for bid, h in heroes.items():
        o, spec, meta = h["override"], h["spec"], h["meta"]
        if meta is None:
            continue
        prm = spec["params"]
        src = f"override:{o['id']}"
        for seg in meta["segments"]:
            a = seg["anchor"]
            pl.items.append({"p": seg["name"], "e": _r(a[0]), "n": _r(a[1]), "z": _r(a[2]), "yaw": 0.0, "src": src})
            tris[seg["name"]] = {"tris_lod0": seg["tris"][0], "tris_lod1": seg["tris"][1], "tris_lod2": seg["tris"][2]}
        nbox = 0
        for dk in h["docks"]:
            a, b = dk["edge"]
            d = (b - a) / np.linalg.norm(b - a)
            nout = np.array([d[1], -d[0]])
            zf = dk["yard_z"] + prm["dock_floor_h_m"]
            for dock in dk["docks"]:
                # the two rubber bumpers as one collision block: the trailer rear stops bumper_proud before the wall
                c = a + d * dock["u"] + nout * prm["bumper_proud_m"] / 2
                M.box(w.buf, "collision", "collision_building", c, d, 1.3, prm["bumper_proud_m"] / 2,
                      zf - 0.55, zf, f"hero:{o['id']}:bumper")
                nbox += 1
        w.net.overrides_applied.append({"id": o["id"], "targets": [bid]})
        rep["applied"].append({
            "id": o["id"], "asset": o["asset"], "building": bid, "spec_sha256": h["sha"],
            "glb_sha256": meta["glb_sha256"], "segments": len(meta["segments"]),
            "docks": int(sum(len(dk["docks"]) for dk in h["docks"])), "collision_boxes": nbox,
            "tris": {f"lod{k}": int(sum(s_["tris"][k] for s_ in meta["segments"])) for k in range(3)},
            "materials": meta["materials"], "confidence": spec["confidence"]})
        log("hero depot", o["id"], "applied:", rep["applied"][-1]["tris"], f"{len(meta['segments'])} segments")
    return tris


def standalone_spec(region_id: str):
    """Spec without the full world build (asset iteration): the same inputs as plan() - buildings.geojson, the NMT
    heightfield smoothed with PAVED_SMOOTH_M - so the result normally equals the spec of build_world."""
    import types

    from scipy import ndimage

    from roads import pipeline
    from roads import profile as P

    from . import buildings_mesh as BM
    from . import paved as PV
    region = pipeline.load_region(region_id)
    origin = (region["origin"]["x"], region["origin"]["y"])
    tm = json.loads((pipeline.REGIONS / region_id / "terrain.json").read_text(encoding="utf-8"))
    hf = P.load_heightfield(tm, REPO, origin)
    sm = ndimage.gaussian_filter(hf.z, S.PAVED_SMOOTH_M)
    overrides = pipeline.load_overrides(region_id)
    fc = json.loads((pipeline.REGIONS / region_id / "buildings.geojson").read_text(encoding="utf-8"))
    blds = BM.load(fc, origin, overrides)
    w = types.SimpleNamespace(stats={}, origin=origin, net=types.SimpleNamespace(overrides_stale=[], overrides_applied=[]))
    os.environ["KAMION_NO_BLENDER"] = "1"
    out = plan(w, region_id, overrides, blds, lambda e, n: PV.bilinear(sm, hf, np.asarray(e, float), np.asarray(n, float)), print)
    return out, w.stats


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="bialystok-industrial-c")
    a = ap.parse_args()
    res, stats = standalone_spec(a.region)
    for bid, h in res.items():
        sp = h["spec"]
        print(bid, "sha", h["sha"][:12], "edges", [(e["name"], e["L"]) for e in sp["edges"]], "segments", len(sp["segments"]),
              "annexes", [(x["name"], x["edge"], x["u"]) for x in sp["annexes"]], "unmatched", h["unmatched"])
        for e in sp["edges"]:
            if "docks" in e["features"]:
                g = [z for _, z in e["ground"]]
                print("  docks", e["features"]["docks"], "ground along facade min/max", min(g), max(g))
