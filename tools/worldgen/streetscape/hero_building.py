"""Hero buildings: authored override `kind: hero_building` (ADR 0070).

A generic building (streetscape.buildings_mesh: extruded BDOT footprint with a rule facade) is replaced by an
authored Blender asset placed as one point instance:

  1. `plan()`   before the buildings are meshed: writes the *spec* of every hero building
                (`Data/Regions/<id>/generated/landmarks/<asset>.spec.json`, git): the authored dimensions
                (`art-source/world/landmarks/<asset>/dims.json`), the BDOT footprints, the floor level and the ground
                heights of everything that stands on the terrain (fence bays, gate, shrubs, flag poles), sampled from
                the smoothed NMT. It then checks that the asset (`<asset>.glb` + `<asset>_meta.json`) was built from
                exactly this spec (sha256). A stale or missing asset is rebuilt with Blender when Blender is available
                (`KAMION_BLENDER` or `blender` on PATH); otherwise the buildings keep their generic geometry and the
                override is reported as stale (streetscape QA `hero_buildings`).
  2. `targets()` ids of the BDOT buildings whose generic mesh is skipped (buildings_mesh.build emits only their
                collision prism and keeps them in the building mask, so paving, terrain and trees still avoid them).
  3. `apply()`  adds the instance (prototype `landmark_<asset>`, LOD0/1/2 in the asset GLB), fence collision and
                returns the triangle counts for the frame estimate.

Standalone (first build of an asset, flat ground from BDOT):
    uv run --project tools/worldgen python tools/worldgen/streetscape/hero_building.py --region <id> --override <override id>
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

REPO = Path(__file__).resolve().parents[3]
KIND = "hero_building"
SCHEMA = "truck-sim-pl/hero-building-spec/1"
BLENDER_SCRIPTS = {"fire_station_jrg2": REPO / "tools" / "blender" / "world" / "landmarks" / "make_fire_station.py"}
LOD_ENDS_M = [150.0, 450.0, 20000.0]     # at lodBias 1 (InstanceImporter.Policy / build_world.instance_ends)


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _r(v, n=3):
    return round(float(v), n)


def asset_paths(asset: str):
    d = REPO / "art-source" / "world" / "landmarks" / asset
    return d, d / f"{asset}.glb", d / f"{asset}_meta.json"


def spec_path(region_id: str, asset: str) -> Path:
    return REPO / "Data" / "Regions" / region_id / "generated" / "landmarks" / f"{asset}.spec.json"


def _hash01(*k) -> float:
    return int(hashlib.sha1(repr(k).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def _subdivide(line, step):
    """Points along a polyline every <= step metres (vertices kept)."""
    out = [np.asarray(line[0], float)]
    for a, b in zip(line[:-1], line[1:]):
        a, b = np.asarray(a, float), np.asarray(b, float)
        n = max(1, int(math.ceil(np.linalg.norm(b - a) / step - 1e-6)))
        out += [a + (b - a) * k / n for k in range(1, n + 1)]
    return out


def build_spec(region_id, o, footprints, zground) -> dict | None:
    """footprints: {building id: ring [[e, n], ...]} (region-local); zground(e, n) -> z."""
    asset = o["asset"]
    dims_p = asset_paths(asset)[0] / "dims.json"
    if not dims_p.exists() or any(b not in footprints for b in o["buildings"]):
        return None
    dims = json.loads(dims_p.read_text(encoding="utf-8"))
    A = np.array(dims["axis"]["origin_en"], float)
    U = np.array(dims["axis"]["u"], float)
    U /= np.linalg.norm(U)
    V = np.array([-U[1], U[0]])

    def en(p):
        return A + U * p[0] + V * p[1]

    def pz(p):
        e, n = en(p)
        return [_r(e), _r(n), _r(zground(e, n))]

    rings = {b: [[_r(x), _r(y)] for x, y in footprints[b]] for b in o["buildings"]}
    zg = [float(zground(x, y)) for b in o["buildings"][:1] for x, y in footprints[b]]
    floor = float(np.median(zg)) + dims["floor_above_ground_m"]
    fence = dims.get("fence", {})
    ground = {
        "footprint_min": _r(min(zg)), "footprint_max": _r(max(zg)),
        "fence": [[pz(p) for p in _subdivide(ln, fence.get("bay", 2.5))] for ln in fence.get("lines_uv", [])],
        "gate": [pz(p) for p in _subdivide(fence["gate_parked_uv"], fence.get("bay", 2.5))] if fence.get("gate_parked_uv") else [],
        "flagpoles": [pz(p) for p in dims.get("flagpoles", {}).get("uv", [])],
    }
    th = dims.get("thuja")
    shrubs = []
    if th:
        a, b = np.array(th["row_uv"][0], float), np.array(th["row_uv"][1], float)
        n = th["count"]
        for k in range(n):
            t = (k + 0.5) / n + (_hash01(asset, "t", k) - 0.5) * 0.35 / n
            p = a + (b - a) * t + np.array([0.0, (_hash01(asset, "o", k) - 0.5) * 0.5])
            hh = th["h"][0] + (th["h"][1] - th["h"][0]) * _hash01(asset, "h", k)
            rr = th.get("r", [0.5, 0.78])
            shrubs.append(pz(p) + [_r(hh, 2), _r(rr[0] + (rr[1] - rr[0]) * _hash01(asset, "r", k), 2), k])
    ground["thuja"] = shrubs
    return {
        "schema": SCHEMA, "id": o["id"], "asset": asset, "region": region_id,
        "osm_way": o.get("osm_way"), "buildings": list(o["buildings"]),
        "frame": "local E, N (EPSG:2180 minus region origin), U absolute EVRF2007; metres; dims in the building "
                 "frame (u, v, z above the floor) of dims.axis",
        "anchor": [_r(A[0]), _r(A[1]), _r(floor)],
        "footprints": rings, "ground": ground, "dims": dims, "lod_ends_m": LOD_ENDS_M,
        "confidence": {"plan_and_heights": "BDOT10k footprint + GUGiK LoD2 roof planes: medium-high",
                       "facades": "by eye from CC0 / CC BY-SA photos (pattern only): medium for the street side, "
                                  "low (WORKING_VALUE) for the yard sides"},
    }


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


def rebuild_asset(asset, spec_file: Path, log) -> bool:
    exe = _blender()
    script = BLENDER_SCRIPTS.get(asset)
    if exe is None or script is None or os.environ.get("KAMION_NO_BLENDER"):
        return False
    log(f"hero building: asset stale -> blender {script.name}")
    r = subprocess.run([exe, "-b", "--factory-startup", "-P", str(script), "--", "--spec", str(spec_file)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        log("hero building: blender failed:", (r.stdout + r.stderr)[-600:])
        return False
    return True


def write_spec(region_id, spec) -> Path:
    sp = spec_path(region_id, spec["asset"])
    sp.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(spec, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
    if not sp.exists() or sp.read_text(encoding="utf-8") != text:
        sp.write_text(text, encoding="utf-8", newline="\n")
    return sp


def plan(region_id, overrides, fc, origin, zground, report, log=lambda *a: None) -> list:
    """[{override, spec, meta, sha}] of the hero buildings whose asset matches the current spec.
    fc = buildings.geojson feature collection (EPSG:2180), origin = region origin."""
    out = []
    rep = report.setdefault("hero_buildings", {"applied": [], "stale": []})
    ox, oy = origin
    rings = {f["id"]: [[x - ox, y - oy] for x, y in f["geometry"]["coordinates"][0][0]] for f in fc["features"]}
    for o in overrides:
        if o.get("kind") != KIND:
            continue
        spec = build_spec(region_id, o, rings, zground)
        if spec is None:
            rep["stale"].append({"id": o["id"], "why": "target building or dims.json missing"})
            continue
        sp = write_spec(region_id, spec)
        sha = _sha(spec)
        meta, why = _asset_meta(o["asset"], sha)
        if meta is None and why != "glb_changed" and rebuild_asset(o["asset"], sp, log):
            meta, why = _asset_meta(o["asset"], sha)
        if meta is None:
            script = BLENDER_SCRIPTS.get(o["asset"])
            rep["stale"].append({"id": o["id"], "why": f"asset {why}: run blender -b --factory-startup -P "
                                                       f"{script.relative_to(REPO).as_posix() if script else '<script>'} "
                                                       f"-- --spec {sp.relative_to(REPO).as_posix()}"})
            log("hero building", o["id"], "STALE:", why, "- generic geometry kept")
            continue
        out.append({"override": o, "spec": spec, "meta": meta, "sha": sha})
    return out


def targets(heroes) -> dict:
    """{building id: asset} of the buildings replaced by an asset."""
    return {b: h["spec"]["asset"] for h in heroes for b in h["spec"]["buildings"]}


def keepout(heroes) -> list:
    """Polygons (region-local) where generated trees must not stand: the fence lines and the shrub row."""
    import shapely
    out = []
    for h in heroes:
        g = h["spec"]["ground"]
        for ln in g["fence"] + ([g["gate"]] if g["gate"] else []):
            if len(ln) >= 2:
                out.append(shapely.LineString([p[:2] for p in ln]).buffer(1.5))
        out += [shapely.Point(t[0], t[1]).buffer(1.6) for t in g["thuja"]]
        out += [shapely.Point(t[0], t[1]).buffer(1.5) for t in g["flagpoles"]]
    return out


def fence_cut(heroes) -> list:
    """Polygons (region-local) along the authored fence lines, the parked gate and the gate opening: the generic OSM
    fence (furniture.fences) is cut there, so a surveyed barrier way is not drawn twice."""
    import shapely
    out = []
    for h in heroes:
        g, d = h["spec"]["ground"], h["spec"]["dims"]
        lines = [[p[:2] for p in ln] for ln in g["fence"] + ([g["gate"]] if g["gate"] else [])]
        op = d.get("fence", {}).get("opening_uv")
        if op:
            A = np.array(d["axis"]["origin_en"], float)
            U = np.array(d["axis"]["u"], float)
            U /= np.linalg.norm(U)
            V = np.array([-U[1], U[0]])
            lines.append([list(A + U * p[0] + V * p[1]) for p in op])
        out += [shapely.LineString(ln).buffer(1.2, cap_style="flat") for ln in lines if len(ln) >= 2]
    return out


def apply(buf, heroes, instances: list, report, log=lambda *a: None) -> dict:
    """Add the instances and the fence collision. Returns {prototype: {tris_lod0, tris_lod1, tris_lod2}}."""
    from roads import meshing as M
    rep = report.setdefault("hero_buildings", {"applied": [], "stale": []})
    tris = {}
    for h in heroes:
        o, spec, meta = h["override"], h["spec"], h["meta"]
        a = spec["anchor"]
        name = meta["prototype"]
        instances.append({"p": name, "e": _r(a[0]), "n": _r(a[1]), "z": _r(a[2]), "yaw": 0.0,
                          "src": f"override:{o['id']}"})
        tris[name] = {"tris_lod0": meta["tris"][0], "tris_lod1": meta["tris"][1], "tris_lod2": meta["tris"][2]}
        nbox = 0
        fh = spec["dims"].get("fence", {}).get("h", 1.6)
        for ln in spec["ground"]["fence"]:
            for p, q in zip(ln[:-1], ln[1:]):
                p, q = np.array(p), np.array(q)
                d = q[:2] - p[:2]
                L = float(np.linalg.norm(d))
                if L < 0.05:
                    continue
                M.box(buf, "collision", "collision_fence", (p[:2] + q[:2]) / 2, d / L, L / 2, 0.05,
                      min(p[2], q[2]) - 0.3, max(p[2], q[2]) + fh, f"hero:{o['id']}:fence")
                nbox += 1
        rep["applied"].append({
            "id": o["id"], "asset": spec["asset"], "prototype": name, "spec_sha256": h["sha"],
            "glb_sha256": meta["glb_sha256"], "buildings": spec["buildings"], "anchor": a,
            "tris": {f"lod{k}": int(meta["tris"][k]) for k in range(3)}, "materials": meta["materials"],
            "fence_collision_boxes": nbox, "confidence": spec["confidence"]})
        log(f"hero building {o['id']}: instance {name} at {a}, tris {meta['tris']}")
    return tris


def main() -> None:
    import argparse
    import sys
    sys.path.insert(0, str(REPO / "tools" / "worldgen"))
    from roads import pipeline
    ap = argparse.ArgumentParser(description="Write the spec of a hero building with flat ground (first asset build).")
    ap.add_argument("--region", required=True)
    ap.add_argument("--override", required=True)
    a = ap.parse_args()
    o = next(x for x in pipeline.load_overrides(a.region) if x.get("id") == a.override)
    reg = pipeline.load_region(a.region)
    ox, oy = reg["origin"]["x"], reg["origin"]["y"]
    fc = json.loads((pipeline.REGIONS / a.region / "buildings.geojson").read_text(encoding="utf-8"))
    rings = {f["id"]: [[x - ox, y - oy] for x, y in f["geometry"]["coordinates"][0][0]] for f in fc["features"]}
    props = {f["id"]: f["properties"] for f in fc["features"]}
    z0 = float(props[o["buildings"][0]]["ground_z_evrf2007"])
    spec = build_spec(a.region, o, rings, lambda e, n: z0)
    print(write_spec(a.region, spec), "sha", _sha(spec)[:12])


if __name__ == "__main__":
    main()
