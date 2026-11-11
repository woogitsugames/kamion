"""Streetscape stage of build_world: buildings + docks -> paved areas -> joint terrain conform -> furniture
-> vegetation -> ground-cover masks. Everything is added to w.buf (layers 'paved', 'buildings',
'buildings_low', 'furniture', 'collision') or returned as point instances."""

from __future__ import annotations

import json

import numpy as np
import shapely
from scipy import ndimage

from roads import pipeline
from roads import standards as S
from terrain_mesh import conform as CF

from . import buildings_mesh as BM
from . import forest_hlod as FH
from . import furniture as FU
from . import signs_route as SR
from . import gate as GT
from . import depot_yard as DY
from . import hero_building as HBD
from . import hero_depot as HD
from . import landmarks as LM
from . import life as LF
from . import paved as PV
from . import plantings as PT
from . import sources as SRC
from . import vegetation as VG
from . import yard_wear as YW


def run(w, road_z, rmask, deck, deck_mask, thick, log):
    rid = w.region["id"]
    rep = {}
    origin = np.array(w.origin)
    src = SRC.load(rid)
    overrides = pipeline.load_overrides(rid)
    hf = w.hf
    road_parts = [p for p in w.buf.parts if p.layer == "road"]
    roads_poly = PV.road_footprint_polygon(road_parts)
    log(f"streetscape: road footprint polygon {roads_poly.area:.0f} m2")
    sm = ndimage.gaussian_filter(hf.z, S.PAVED_SMOOTH_M)

    def zsmooth(e, n):
        return PV.bilinear(sm, hf, np.asarray(e, float), np.asarray(n, float))

    # buildings (+ docks facing yards described by the raw paved sources)
    fc = json.loads((pipeline.REGIONS / rid / "buildings.geojson").read_text(encoding="utf-8"))
    # hero buildings (override kind: hero_building, ADR 0070): authored asset instead of the rule facade
    heroes = HBD.plan(rid, overrides, fc, w.origin, lambda e, n: float(np.asarray(zsmooth(e, n)).ravel()[0]), rep, log)
    blds = BM.load(fc, w.origin, overrides, hero=HBD.targets(heroes))
    yard_src = [PV._poly_local(f["geometry"]["coordinates"], w.origin) for f in src["bdot10k"]["OT_PTPL_A"]
                if f["props"].get("materialnawierzchni") != "grunt naturalny"]
    yard_src += [PV._poly_local(a["geometry"]["coordinates"], w.origin) for a in src["osm"]["areas"]
                 if a["tags"].get("amenity") == "parking"]
    yard_src += [shapely.geometry.Polygon(np.asarray(o["polygon_epsg2180"], float) - origin) for o in overrides
                 if o.get("kind") == "paved_area"]
    yard_union = shapely.union_all([shapely.make_valid(p) for p in yard_src] + [roads_poly])
    brep = {}
    facade_signs = []
    depots = HD.plan(w, rid, overrides, blds, zsmooth, log)      # hero depot halls (override kind: hero_depot, ADR 0071)
    docks = BM.build(w.buf, blds, hf, zsmooth, yard_union, roads_poly, brep, sign_out=facade_signs, heroes=depots)
    rep["buildings"] = brep
    log("buildings", brep["typologies"], "docks", brep["docks"])
    bpoly = shapely.union_all([b["poly"] for b in blds])

    # paved areas
    prep = {}
    truck_zone = shapely.union_all([b["poly"].buffer(40.0) for b in blds if b["typ"] == "hall"] +
                                   [d["apron"].buffer(10.0) for d in docks])
    paved = PV.collect(src, origin, overrides, docks, roads_poly, bpoly, prep, truck_zone=truck_zone)
    rep["paved_m2_by_source"] = prep
    pmask = PV.rasterize_polys([p["poly"] for p in paved], hf) & ~rmask
    pz = PV.paved_heights(hf, road_z, rmask, pmask)
    shapely.prepare(roads_poly)
    PV.build_meshes(w.buf, paved, np.where(np.isfinite(pz), pz, sm), hf, walls=bpoly.boundary, roads_poly=roads_poly)
    mats = {}
    for p in paved:
        mats[p["mat"]] = round(mats.get(p["mat"], 0) + p["poly"].area)
    rep["paved_m2_by_material"] = mats
    log("paved", len(paved), "areas", mats)

    # joint conform: roads + paved
    mask = rmask | pmask
    zjoin = np.where(rmask, road_z, np.where(pmask, pz, -np.inf))
    # grass verge / island strips (road layer, verge_grass only): terrain stays just under them (CF.conform)
    _, vmask = CF.rasterise([p for p in road_parts if p.mat == "verge_grass"], hf)
    _, hmask = CF.rasterise([p for p in road_parts if p.mat != "verge_grass"], hf)
    soft = vmask & ~hmask & ~pmask
    zc, dist = CF.conform(hf, zjoin, mask, soft=soft)
    rep["terrain_soft_nodes"] = int(soft.sum())
    zc = CF.clamp_under_decks(zc, deck, deck_mask, thick, mask)
    zc = CF.tidy(zc, zjoin, mask, dist)
    bmask = PV.rasterize_polys([b["poly"] for b in blds], hf)
    zc = np.where(bmask & ~mask, np.minimum(zc, sm), zc)        # ground under buildings never above the floor
    zsurf_g = np.where(mask, zjoin, zc)

    def zsurf(e, n):
        return PV.bilinear(zsurf_g, hf, np.asarray(e, float), np.asarray(n, float))

    def zground(e, n):
        return PV.bilinear(zc, hf, np.asarray(e, float), np.asarray(n, float))

    # terrain collider (RegionImporter: the 4 m terrain_lod2 grid of terrain_mesh.chunks, min-filtered next to roads):
    # a pole on a verge must not stand above it either (3 lamps hung 0.30 m over it at the 1 m conformed terrain)
    from terrain_mesh import chunks as CH
    z4 = CH.lod_grid(zc, mask, 4)

    def zcollider(e, n):
        e = np.asarray(e, float)
        n = np.asarray(n, float)
        fi = np.clip((e - hf.x0) / 4.0, 0, z4.shape[1] - 1.001)
        fj = np.clip((hf.y1 - n) / 4.0, 0, z4.shape[0] - 1.001)
        i0, j0 = np.floor(fi).astype(int), np.floor(fj).astype(int)
        fx, fy = fi - i0, fj - j0
        za, zb = z4[j0, i0], z4[j0, i0 + 1]
        zd, ze = z4[j0 + 1, i0], z4[j0 + 1, i0 + 1]
        # chunks.grid_mesh diagonal a -> e: triangles (a, d, e) and (a, e, b)
        return np.where(fx >= fy, za + fx * (zb - za) + fy * (ze - zb), za + fy * (zd - za) + fx * (ze - zd))

    def zground_col(e, n):
        return np.minimum(zground(e, n), zcollider(e, n))

    # authored plantings (hedges traced from the orthophoto, kerb-enclosed islands filled to the kerb top; r6 W-N12)
    def deck_at(e, n):
        i, j = int(round(e - hf.x0)), int(round(hf.y1 - n))
        return bool(0 <= j < deck_mask.shape[0] and 0 <= i < deck_mask.shape[1] and deck_mask[j, i])
    plant_blocked = PT.build(w.buf, overrides, origin, roads_poly, road_parts, zground, deck_at, rep)
    if rep.get("plantings", {}).get("hedges") or rep.get("plantings", {}).get("islands"):
        log("plantings", {k: v for k, v in rep["plantings"].items() if k != "islands"})
    # OSM barrier=hedge (fence hedges, gaps at gates); none in tile C
    PT.osm_hedges(w.buf, src, origin, roads_poly, zground, rep)

    # furniture
    pl = FU.Placer(zsurf, zground_col, surf=FU.SurfaceTop(w.buf.parts),
                   col=FU.SurfaceTop(w.buf.parts, collision=True))
    codes, boards = set(), {}
    frep = {}
    graph = json.loads((pipeline.REGIONS / rid / "roads.graph.json").read_text(encoding="utf-8"))
    attrs = {e["id"]: e["attrs"] for e in graph["edges"]}
    FU.signals(pl, w.net, w.junctions, frep)
    FU.junction_signs(pl, w.net, w.junctions, w.ctx["points"], frep, codes)
    FU.speed_signs(pl, w.net, frep, codes)
    FU.crossing_signs(pl, w.net, w.ctx["points"], frep, codes)
    FU.direction_boards(pl, w.net, attrs, frep, boards)
    SR.osm_signs(pl, w.net, src, origin, w.junctions, frep, codes)
    SR.roundabout_signs(pl, w.net, w.junctions, attrs, frep, codes, boards, src=src, origin=origin)
    LM.build(pl, w.net, graph, overrides, origin, boards, frep)
    FU.misc_points(pl, w.net, src, origin, frep, codes)
    FU.lamps(pl, w.net, src["osm"]["nodes"], origin, frep)
    lin = FU.Lin(w.buf, zsurf)
    # authored fences of hero buildings replace the generic panel fence of the same OSM way (ADR 0070 r3)
    FU.fences(lin, src, origin, shapely.union_all([roads_poly] + HBD.fence_cut(heroes)), frep)
    def znat(e, n):                              # natural ground (NMT, decks removed): embankment height
        return PV.bilinear(hf.z, hf, np.asarray(e, float), np.asarray(n, float))
    FU.guardrails(lin, w.net, znat, frep)
    FU.noise_barriers(lin, src, origin, roads_poly, frep, overrides, pl=pl)
    FU.power_lines(lin, src, origin, frep, pl=pl, roads_poly=roads_poly)
    GT.build(pl, lin, w.net, graph, overrides, roads_poly, bpoly, origin, frep)
    DY.apply(pl, overrides, origin, None, frep)                 # authored depot yards (override kind: depot_yard)
    pl.items.extend(facade_signs)
    hero_tris = HD.apply(w, depots, pl, log)
    rep["hero_depots"] = w.stats.get("hero_depots", {})
    from roads import build_world as BW
    try:
        route_P = BW.route_polyline(rid, w)[0]
    except Exception as e:                      # no candidate route for this region: no corridor
        log("life: no start route", e)
        route_P = None
    park_polys = [PV._poly_local(a["geometry"]["coordinates"], w.origin) for a in src["osm"]["areas"]
                  if a["tags"].get("amenity") == "parking" and a["geometry"]["type"] == "Polygon"]
    park_polys += [PV._poly_local(f["geometry"]["coordinates"], w.origin) for f in src["bdot10k"]["OT_KUKO_A"]
                   if f["props"].get("rodzaj") == "parking" and f["geometry"]["type"] == "Polygon"]
    LF.place(pl, docks, paved, blds, roads_poly, bpoly, route_P, frep, buf=w.buf, zsurf=zsurf, park_polys=park_polys,
             no_parking=DY.no_parking(overrides, origin), authored_trailers=DY.dock_trailers(overrides))
    YW.apply(w.buf, overrides, origin, docks, paved, roads_poly, zsurf, frep)     # authored yard wear (ADR 0071 r11)
    carriage = PV.road_footprint_polygon([p for p in road_parts if p.mat.startswith("road_")])
    FU.clear_carriageway(pl, carriage, zsurf, frep)
    FU.clear_under_decks(pl, w.buf.parts, frep)
    FU.clear_level_carriageways(pl, w.buf.parts, frep)
    frep["poles_reseated"] = pl.reseated
    frep["pole_footing_steps"] = {"count": len(pl.seat_log), "max_m": max([r["step_m"] for r in pl.seat_log], default=0.0),
                                  "worst": sorted(pl.seat_log, key=lambda r: -r["step_m"])[:20]}
    SR.route_audit(pl.items, route_P, w.net, w.junctions, frep)
    rep["furniture"] = frep
    log("furniture", {k: v for k, v in frep.items() if k != "junction_signs"})

    # vegetation
    blocked = ndimage.binary_dilation(mask | bmask, iterations=3)
    if plant_blocked:
        blocked |= PV.rasterize_polys(plant_blocked, hf)
    hero_keepout = HBD.keepout(heroes)
    if hero_keepout:
        blocked |= PV.rasterize_polys(hero_keepout, hf)
    vrep = {}
    trees, forests = VG.place(src, origin, hf, zc, blocked, vrep, overrides)
    forest_mix = vrep.pop("_forest_mix")
    rep["vegetation"] = vrep
    log("trees", vrep["trees"])
    # forest HLOD cells (canopy + edge walls) replacing far stands
    no_forest = shapely.union_all([roads_poly, bpoly] + [p["poly"] for p in paved]).buffer(2.5)
    half = w.region["bbox"]["width_m"] / 2
    hlod = FH.build(trees, forest_mix, no_forest, zground, half, vrep)
    log("forest hlod", vrep["forest_hlod"])
    col = VG.ground_masks(src, origin, hf, dist, forests)
    instances = pl.items + trees
    hero_tris = {**hero_tris, **HBD.apply(w.buf, heroes, instances, rep, log)}      # depot halls + hero buildings
    if heroes or rep.get("hero_buildings", {}).get("stale"):
        log("hero buildings", {k: [x["id"] for x in v] for k, v in rep["hero_buildings"].items()})
    return {"zc": zc, "dist": dist, "mask": mask, "rmask": rmask, "col": col, "instances": instances,
            "codes": codes, "boards": boards, "report": rep, "docks": docks, "paved": paved, "forest_hlod": hlod, "hero_tris": hero_tris}
