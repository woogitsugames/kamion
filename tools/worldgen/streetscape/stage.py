"""Streetscape stage of build_world: buildings + docks -> paved areas -> joint terrain conform -> furniture
-> vegetation -> ground-cover masks. Everything is added to w.buf (layers 'paved', 'buildings',
'buildings_low', 'furniture', 'collision') or returned as point instances."""

from __future__ import annotations

import json
import os

import numpy as np
import shapely
from scipy import ndimage

from roads import pipeline
from roads import standards as S
from terrain_mesh import conform as CF

from . import buildings_mesh as BM
from . import forest_hlod as FH
from . import frontage as FR
from . import furniture as FU
from . import fab_details as FD
from . import signs_route as SR
from . import gate as GT
from . import depot_yard as DY
from . import hero_building as HBD
from . import hero_depot as HD
from . import landmarks as LM
from . import gate3_landmarks as G3
from . import life as LF
from . import paved as PV
from . import plantings as PT
from . import plots as PLT
from . import sources as SRC
from . import vegetation as VG
from . import yard_wear as YW


def _yard_src(src, origin, overrides):
    out = [PV._poly_local(f["geometry"]["coordinates"], origin) for f in src["bdot10k"]["OT_PTPL_A"]
           if f["props"].get("materialnawierzchni") != "grunt naturalny"]
    out += [PV._poly_local(a["geometry"]["coordinates"], origin) for a in src["osm"]["areas"]
            if a["tags"].get("amenity") == "parking"]
    out += [shapely.geometry.Polygon(np.asarray(o["polygon_epsg2180"], float) - np.asarray(origin)) for o in overrides
            if o.get("kind") == "paved_area"]
    return out


def plan_plots(w, rid, blds=None):
    """House plots of the region (ADR 0114), planned on the road geometry of `w` (pass 1 of build_world: the kerb
    drops of the driveways go into pass 2; the streetscape stage reuses the plan as w.plot_plan)."""
    import os
    origin = np.array(w.origin)
    src = SRC.load(rid)
    overrides = pipeline.load_overrides(rid)
    road_parts = [p for p in w.buf.parts if p.layer == "road"]
    roads_poly = PV.road_footprint_polygon(road_parts)
    if os.environ.get("KAMION_NO_PLOTS") == "1":      # budget measurement (ADR 0114): the world without house plots
        return {"plots": [], "drops": [], "roads_poly": roads_poly}
    carriage = PV.road_footprint_polygon([p for p in road_parts if p.mat.startswith("road_")])
    if blds is None:
        fc = json.loads((pipeline.REGIONS / rid / "buildings.geojson").read_text(encoding="utf-8"))
        blds = BM.load(fc, w.origin, overrides)
    yards = [g for p in _yard_src(src, w.origin, overrides) for g in getattr(shapely.make_valid(p), "geoms", [shapely.make_valid(p)])
             if g.geom_type == "Polygon"]
    bpoly = shapely.union_all([b["poly"] for b in blds])
    rp = PLT.region_plan(blds, roads_poly, carriage, yards, src, origin, bpoly, net=w.net)
    from . import plot_canopy as PCN                 # ADR 0132: crowns read off the orthophoto (None when not built)
    rp["canopy"] = PCN.load(rid)
    return rp


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
    # house plots (ADR 0114): lawn / driveway / path are paved-area items of their own list (yard life, wear and
    # gate logic keep reading `paved` only)
    plot_plan = getattr(w, "plot_plan", None) or plan_plots(w, rid, blds)
    plot_paved = PLT.paved_items(plot_plan, roads_poly, bpoly, paved)
    pmask = PV.rasterize_polys([p["poly"] for p in paved + plot_paved], hf) & ~rmask
    pz = PV.paved_heights(hf, road_z, rmask, pmask)
    shapely.prepare(roads_poly)
    PV.build_meshes(w.buf, paved, np.where(np.isfinite(pz), pz, sm), hf, walls=bpoly.boundary, roads_poly=roads_poly)
    # ADR 0124 r2: the ground of the house plots reads the ROAD height on the nodes of the road footprint (the yards
    # above read the smoothed terrain there). A driveway that comes down from a plot 0.3-0.5 m above the street ended
    # 15-20 cm over the lowered kerb, and the terrain showed under that lip as a wedge of grass (`r16_kerb_0`).
    PV.build_meshes(w.buf, plot_paved, np.where(np.isfinite(pz), pz, np.where(rmask, road_z, sm)), hf,
                    walls=bpoly.boundary, roads_poly=roads_poly)
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
    FU.bridge_median_lamps(pl, w.net, frep)          # ADR 0123: twin-arm lamps between the decks (bridge_style `lamps`)
    lin = FU.Lin(w.buf, zsurf)
    # authored fences of hero buildings replace the generic panel fence of the same OSM way (ADR 0070 r3)
    FU.fences(lin, src, origin, shapely.union_all([roads_poly] + HBD.fence_cut(heroes)), frep,
              styles=FU.fence_styles(overrides), net=w.net)
    def znat(e, n):                              # natural ground (NMT, decks removed): embankment height
        return PV.bilinear(hf.z, hf, np.asarray(e, float), np.asarray(n, float))
    FU.guardrails(lin, w.net, znat, frep)
    FU.noise_barriers(lin, src, origin, roads_poly, frep, overrides, pl=pl, net=w.net)
    FU.power_lines(lin, src, origin, frep, pl=pl, roads_poly=roads_poly)
    GT.build(pl, lin, w.net, graph, overrides, roads_poly, bpoly, origin, frep, paved=paved)
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
             no_parking=DY.no_parking(overrides, origin) + GT.no_parking(frep), authored_trailers=DY.dock_trailers(overrides))
    FR.place_cars(pl, brep.get("frontage_props"), frep)         # display vehicles of authored frontages (ADR 0129)
    YW.apply(w.buf, overrides, origin, docks, paved, roads_poly, zsurf, frep)     # authored yard wear (ADR 0071 r11)
    FD.apply(w, pl, roads_poly, bpoly, paved, park_polys, route_P, frep, log, overrides=overrides, deck_at=deck_at)   # Fab Megascans (ADR 0084)
    carriage = PV.road_footprint_polygon([p for p in road_parts if p.mat.startswith("road_")])
    G3.build(pl, w.net, graph, overrides, origin, boards, frep, carriage=carriage,   # ADR 0125 gate 3 signs
             islands=[i for i in getattr(getattr(w, "gore_plan", None), "islands", []) if i.built])   # ADR 0128
    FU.clear_carriageway(pl, carriage, zsurf, frep)
    FU.clear_narrow_islands(pl, w.buf.parts, w.net, frep)        # ADR 0093: no lamp on a separation < ~2 m
    FU.clear_under_decks(pl, w.buf.parts, frep)
    FU.clear_level_carriageways(pl, w.buf.parts, frep)
    FU.lamp_rows(pl, w.buf.parts, pipeline.REGIONS / rid / "lamp_rows.json", frep)   # ADR 0133: authored rows
    frep["poles_reseated"] = pl.reseated
    frep["pole_footing_steps"] = {"count": len(pl.seat_log), "max_m": max([r["step_m"] for r in pl.seat_log], default=0.0),
                                  "worst": sorted(pl.seat_log, key=lambda r: -r["step_m"])[:20]}
    SR.route_audit(pl.items, route_P, w.net, w.junctions, frep)
    rep["furniture"] = frep
    log("furniture", {k: v for k, v in frep.items() if k not in ("junction_signs", "guardrail_runs")})

    # house plots (ADR 0107 / 0114): fences, gates and garden as chunk geometry in one material (`plot_kit`)
    def zplot(q):
        return float(np.asarray(zsurf(np.array([q[0]]), np.array([q[1]]))).ravel()[0])
    # ADR 0163 (G7): front hedges / shrub strips and broadleaf garden trees of the house plots are planned and meshed
    # by streetscape.plantings; KAMION_GARDENS_0163=0 reproduces the world without them (baseline ablation only)
    gardens_0163 = os.environ.get("KAMION_GARDENS_0163", "1") != "0"
    plot_plan.pop("front_green", None)
    plot_plan.pop("garden_trees", None)
    if gardens_0163:
        PT.plan_house_greenery(plot_plan, rep)
    plots = PLT.build(w.buf, plot_plan, zplot, FU.SurfaceTop([p_ for p_ in w.buf.parts if p_.layer == "road"]), rep,
                      items=pl.items)       # ADR 0124: the lamp poles of the house streets carry the overhead line
    if gardens_0163:
        PT.front_gardens(w.buf, plot_plan, zplot, rep, half=float(w.region["bbox"]["width_m"]) / 2)
        log("garden fronts", {k: v for k, v in rep["garden_fronts"].items() if k != "list"})
    log("plots", {k: v for k, v in rep["plots"].items() if k != "list"})

    # vegetation
    blocked = ndimage.binary_dilation(mask | bmask, iterations=3)
    if plots["keepout"]:
        blocked |= PV.rasterize_polys(plots["keepout"], hf)
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
    col = PLT.lawn_mask(col, plots["lawns"], hf, PV.rasterize_polys)     # no grit strip around the lawns (ADR 0114)
    # ADR 0132: grown garden trees of the house plots (orthophoto crowns) join the tree instances - same prototypes,
    # LODs and impostors as every street tree; none closer than 2.5 m to a tree the region already has there
    ptrees = plots.get("trees") or []
    if ptrees and trees:
        from scipy.spatial import cKDTree
        kd = cKDTree(np.array([[t_["e"], t_["n"]] for t_ in trees]))
        dd, _ = kd.query(np.array([[t_["e"], t_["n"]] for t_ in ptrees]))
        ptrees = [t_ for t_, d_ in zip(ptrees, dd) if d_ >= 2.5]
    if gardens_0163:
        PT.garden_trees(w.buf, plot_plan, zplot, rep, half=float(w.region["bbox"]["width_m"]) / 2, region_trees=trees)
        log("garden trees", {k: v for k, v in rep["garden_trees"].items() if k not in ("list", "conifers")})
        ptrees = VG.garden_canopies(ptrees, plot_plan, rep)
    rep["plots"]["inst_trees_kept"] = len(ptrees)
    for t_ in ptrees:
        vrep["trees"][t_["p"]] = vrep["trees"].get(t_["p"], 0) + 1
    instances = pl.items + trees + ptrees
    hero_tris = {**hero_tris, **HBD.apply(w.buf, heroes, instances, rep, log)}      # depot halls + hero buildings
    if heroes or rep.get("hero_buildings", {}).get("stale"):
        log("hero buildings", {k: [x["id"] for x in v] for k, v in rep["hero_buildings"].items()})
    return {"zc": zc, "dist": dist, "mask": mask, "rmask": rmask, "col": col, "instances": instances,
            "codes": codes, "boards": boards, "report": rep, "docks": docks, "paved": paved, "forest_hlod": hlod, "hero_tris": hero_tris}
