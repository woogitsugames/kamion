"""Optional Fab detail placement (ADR 0084).

Only locally prepared, reviewed assets are used. All distances, densities, sizes and
caps below are WORKING_VALUE art hypotheses; these are not surveyed utility data.
The absence of Fab leaves the public-clone world unchanged.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import Point, LineString

from roads.decals import _surf, hf, LIFT_PATCH
from roads.markings import lane_layout
from roads.network import side_params, side_extent

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "art-source/world/megascans/_generated/manifest.json"
MAX_PROPS = 320  # region cap, WORKING_VALUE; final budget is gated by visual-QA
MANHOLE_SPACING_M = 90.0  # WORKING_VALUE, longitudinal utility run
GROUND_IDS = ("grass-clumps", "wild-grass", "boxwood", "elderberry", "granite-rock", "small-granite-rock")


def key(asset_id):
    return "fab_" + asset_id.replace("-", "_")


def load_ready(path=MANIFEST, root=ROOT, review=None, sources=None):
    """Fail closed unless output, current approval and source pin all agree.

    Consumption needs prepared outputs, not the original ZIP. ``review`` and
    ``sources`` optionally inject id-keyed records for isolated tests; production
    always rereads the owning tracked review and source manifest on each load.
    """
    if os.environ.get("KAMION_DISABLE_FAB") == "1":
        return {}
    try:
        root = Path(root)
        if review is None:
            review_data = json.loads((root / "tools/worldgen/fab/review.json").read_text(encoding="utf-8"))
            if review_data.get("schema") != 1:
                return {}
            review = review_data.get("items", {})
        if sources is None:
            source_data = json.loads((root / "Data/SourceManifests/fab-megascans-2026-11-10.json").read_text(encoding="utf-8"))
            sources = {item["id"]: item for item in source_data["items"]}
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if data.get("schema") != 1:
            raise ValueError("unsupported schema")
        ready = {}
        for aid, item in data.get("items", {}).items():
            approval = review.get(aid, {})
            source = sources.get(aid, {})
            pin = source.get("sha256")
            if (item.get("status") != "ready" or approval.get("status") != "approved"
                    or not isinstance(pin, str) or len(pin) != 64
                    or approval.get("source_sha256") != pin or item.get("source_sha256") != pin):
                continue
            color = item.get("textures", {}).get("Low", {}).get("basecolor")
            if not color or not _output_file(root, color):
                continue
            models = item.get("models", [])
            if models:
                lods = models[0].get("lods", [])
                if {v.get("lod") for v in lods} != {0, 1, 2}:
                    continue
                if not all(_output_file(root, v.get("path", "")) for v in lods):
                    continue
            ready[aid] = item
        return ready
    except (OSError, ValueError, TypeError, AttributeError, KeyError):
        return {}


def _output_file(root, name):
    """Generated files may never be read through arbitrary manifest paths."""
    root = Path(root).resolve()
    p = (root / name).resolve()
    safe = (root / "art-source/world/megascans/_generated").resolve()
    return p.is_relative_to(safe) and p.is_file()


def _atlas(assets=None, path=None, root=ROOT):
    """Use an atlas only while every contributing source remains approved/pinned."""
    if os.environ.get("KAMION_DISABLE_FAB") == "1":
        return None
    assets = load_ready() if assets is None else assets
    path = Path(path) if path is not None else Path(root) / "art-source/world/megascans/_generated/drainage_atlas_manifest.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("schema") != 1:
            return None
        atlas = data["materials"]["fab_drainage"]
        sources = atlas["sources"]
        ids = {source["id"] for source in sources}
        if not ids or len(ids) != len(sources):
            return None
        for source in sources:
            pin = source.get("sha256")
            if not pin or assets.get(source["id"], {}).get("source_sha256") != pin:
                return None
        rects = atlas["uv_rects"]
        if set(rects) != ids:
            return None
        for rect in rects.values():
            if len(rect) != 4 or not all(math.isfinite(float(v)) for v in rect):
                return None
            u0, v0, u1, v1 = rect
            if not (0 <= u0 < u1 <= 1 and 0 <= v0 < v1 <= 1):
                return None
        for tier in ("Low", "High"):
            maps = atlas["textures"][tier]
            if not maps.get("basecolor") or not all(_output_file(root, name) for name in maps.values()):
                return None
            # Geometry UVs must address exactly the same cells on both tiers.
            if atlas.get("uv_rects_by_tier", {}).get(tier, rects) != rects:
                return None
        return atlas
    except (OSError, ValueError, TypeError, AttributeError, KeyError):
        return None


def _decal_uv(aid, uv, atlas):
    uv = np.asarray(uv, float)
    if atlas is not None and aid in atlas["uv_rects"]:
        u0, v0, u1, v1 = atlas["uv_rects"][aid]
        return "fab_drainage", np.array([u0, v0]) + uv * np.array([u1 - u0, v1 - v0])
    return key(aid), uv


def materials(assets=None):
    """Manifest material descriptors; Unity FabMaterials resolves local texture maps.

    Keep white factors because albedo is already photographed; no invented colour
    calibration. Decals have their authored 0..1 UVs and retain the normal lift.
    """
    assets = load_ready() if assets is None else assets
    result = {}
    for aid in sorted(assets):
        is_decal = aid in ("round-manhole-cover", "metal-manhole-cover", "round-drain-cover", "square-rusty-drain")
        result[key(aid)] = {"color": [1., 1., 1.], "rough": 0.85, "fab_asset": aid,
                            "surface": "steel" if is_decal else "detail"}
        if is_decal:
            result[key(aid)].update({"decal": True, "depth_offset_m": LIFT_PATCH})
    if _atlas(assets) is not None:
        result["fab_drainage"] = {"color": [1., 1., 1.], "rough": 0.85, "surface": "steel",
                                   "decal": True, "depth_offset_m": LIFT_PATCH}
    return result


def prototype_stats(assets=None):
    """Measured triangle counts for the first imported variant, not estimates."""
    assets = load_ready() if assets is None else assets
    result = {}
    for aid, item in assets.items():
        models = item.get("models", [])
        if not models:
            continue
        stats = {f"tris_lod{lod['lod']}": int(lod["triangles"])
                 for lod in models[0].get("lods", [])
                 if lod.get("lod") in (0, 1, 2) and isinstance(lod.get("triangles"), (int, float))}
        if len(stats) == 3:
            result[key(aid)] = stats
    return result


def drainage(buf, net, assets, report):
    """Reuse existing 35 m gully quads; add covers on a lane's centre line.

    Replacing a material avoids duplicate coplanar grate geometry. Native gully
    rules retain 35 m spacing, kerb and low-side constraints. Covers skip bridge
    decks, roundabouts, junction trims and non-asphalt/concrete streets.
    """
    drains = [a for a in ("square-rusty-drain", "round-drain-cover") if a in assets]
    covers = [a for a in ("round-manhole-cover", "metal-manhole-cover") if a in assets]
    atlas = _atlas(assets)
    count = {"gully_replacements": 0, "manholes": 0, "drainage_atlas": atlas is not None}
    if drains:
        for p in buf.parts:
            if p.mat == "drain_grate" and p.src.startswith("gully:"):
                aid = drains[int(hf(p.src, "fab") * len(drains)) % len(drains)]
                p.mat, p.UV = _decal_uv(aid, p.UV, atlas)
                count["gully_replacements"] += 1
    if covers:
        for c in sorted(net.chains, key=lambda c: c.id):
            if c.meta.get("absorbed") or c.roundabout:
                continue
            s0, s1 = c.t_a + 8.0, c.length - c.t_b - 8.0
            # Stagger chain phases; don't imply a surveyed utility position.
            for s in np.arange(s0 + 20.0 + 35.0 * hf(c.id, "cover-phase"), s1, MANHOLE_SPACING_M):
                s = float(s)
                if c.bridge[c.idx(s)]:
                    continue
                sec = c.section(s, net.sec_list)
                if sec.surface_mat not in ("road_asphalt", "road_asphalt_new", "road_concrete"):
                    continue
                hw = float(c.hw_at(s))
                lanes = lane_layout(sec, hw, float(c.interp(c.dirn, s)))[2]
                centres = lanes["fwd"] + lanes["bwd"]
                if not centres:
                    continue
                lat = centres[int(hf(c.id, "cover-lane") * len(centres)) % len(centres)]
                r = 0.32  # 640 mm cover footprint, WORKING_VALUE
                if abs(lat) + r > hw - 0.1:
                    continue
                aid = covers[int(hf(c.id, round(s, 2), "cover-kind") * len(covers)) % len(covers)]
                ss = s + np.array([-r, r, r, -r])
                ll = lat + np.array([-r, -r, r, r])
                mat, uv = _decal_uv(aid, [[0, 0], [1, 0], [1, 1], [0, 1]], atlas)
                buf.add("markings", mat, _surf(c, ss, ll, LIFT_PATCH),
                        uv, [[0, 1, 2], [0, 2, 3]],
                        src=f"fab:manhole:{c.id}:{s:.2f}:WORKING_VALUE")
                count["manholes"] += 1
    report.update(count)


def _ground_height(pl, p, radius, terrain_only=False):
    """Lowest of five support samples, rejecting steep/invalid support."""
    offsets = np.array([[0, 0], [radius, 0], [-radius, 0], [0, radius], [0, -radius]])
    points = p + offsets
    zfun = pl.zground if terrain_only and pl.zground is not None else pl.zsurf
    z = np.asarray(zfun(points[:, 0], points[:, 1]), float)
    if not terrain_only and pl.surf is not None:
        for i, q in enumerate(points):
            zs = pl.surf.top(float(q[0]), float(q[1]))
            if math.isfinite(zs):
                z[i] = zs
    if not np.all(np.isfinite(z)) or np.ptp(z) > 0.12:
        return None
    return float(np.min(z))


def props(pl, net, assets, roads_poly, bpoly, paved, park_polys, route, report, islands=(), deck_at=None):
    """Small bounded detail groups, outside carriageways/buildings/driving corridor.

    No uniform region-wide scatter: litter needs an existing bus-stop/gate/bin or
    a mapped car park; grass/shrubs/rocks follow roadside soft ground only.
    """
    # build_world.route_polyline returns a numpy Nx2/Nx3 array, while small
    # unit/synthetic callers may already pass a Shapely line.
    if route is not None and not hasattr(route, "buffer"):
        points = np.asarray(route, float)
        route = LineString(points[:, :2]) if points.ndim == 2 and len(points) >= 2 else None
    ready = {a for a, item in assets.items() if item.get("models")}
    if not ready:
        report["props"] = {}
        return
    block = shapely.union_all([roads_poly.buffer(0.15), bpoly.buffer(0.3),
                              route.buffer(2.5) if route is not None else Point().buffer(0)])
    paved_union = shapely.union_all([p["poly"] for p in paved])
    shapely.prepare(block)
    shapely.prepare(paved_union)
    def footprint_radius(aid, minimum):
        models = assets.get(aid, {}).get("models", [])
        dims = models[0].get("dimensions_m", []) if models else []
        if len(dims) == 3 and all(math.isfinite(float(x)) and float(x) > 0 for x in dims):
            return max(minimum, 0.5 * math.hypot(float(dims[0]), float(dims[1])))
        return minimum

    def occupied_radius(proto):
        # Conservative footprints for large existing point objects, not just the
        # point at their origin (notably gatehouses and parked trailers).
        if proto in ("gatehouse", "bus_shelter"):
            return 3.5
        if proto.startswith(("trailer_", "tractor_")):
            return 15.0  # some trailer origins are at the rear, not the centre
        if proto.startswith(("car_", "van_")):
            return 3.5
        return 0.6

    occupied = [(np.array([it["e"], it["n"]]), occupied_radius(it["p"])) for it in pl.items]
    counts = {}
    total = 0

    def place(aid, p, radius, seed, natural=False, island=None):
        nonlocal total
        if aid not in ready or total >= MAX_PROPS:
            return False
        radius = footprint_radius(aid, radius)
        p = np.asarray(p, float)
        footprint = Point(*p).buffer(radius)
        if block.intersects(footprint):
            return False
        if island is not None and not island.covers(footprint):
            return False
        if deck_at is not None and island is not None and deck_at(float(p[0]), float(p[1])):
            return False
        if natural and paved_union.intersects(footprint):
            return False
        if not natural and island is None and not paved_union.covers(footprint):
            return False
        if any(np.linalg.norm(p - q) < radius + qr for q, qr in occupied):
            return False
        z = _ground_height(pl, p, radius, terrain_only=natural)
        if z is None:
            return False
        pl.add(key(aid), p, hf(seed, "yaw") * 2 * math.pi, z=z, src=f"fab:{seed}:WORKING_VALUE")
        occupied.append((p, radius))
        counts[aid] = counts.get(aid, 0) + 1
        total += 1
        return True

    # Existing bins already have tested positions. Swap only when the scan fits
    # the same small footprint; the processor normalises its intended dimensions.
    if "trash-can" in ready:
        for it in pl.items:
            if it["p"] == "waste_bin":
                it["p"] = key("trash-can")
                counts["trash-can"] = counts.get("trash-can", 0) + 1
    anchors = [it for it in pl.items if it["p"] in ("bus_shelter", "gatehouse", "waste_bin", key("trash-can"))]
    for i, it in enumerate(anchors):
        for aid, radius in (("trash-bag-pack", 0.45), ("urban-trash", 0.5)):
            theta = hf(it.get("src", ""), i, aid) * 2 * math.pi
            centre = np.array([it["e"], it["n"]])
            distance = occupied_radius(it["p"]) + footprint_radius(aid, radius) + 0.3
            for j in range(4):
                a = theta + j * math.pi / 2
                if place(aid, centre + np.array([math.cos(a), math.sin(a)]) * distance,
                         radius, f"anchor:{i}:{aid}"):
                    break
    for i, park in enumerate(park_polys):
        if park.is_empty:
            continue
        boundary = park.exterior if park.geom_type == "Polygon" else park.boundary
        q = boundary.interpolate(boundary.length * hf(i, "park"))
        centre = park.representative_point()
        vector = np.array([centre.x - q.x, centre.y - q.y])
        if np.linalg.norm(vector) > 0:
            p = np.array([q.x, q.y]) + vector / np.linalg.norm(vector) * 1.1
            place("trash-bag-pack", p, 0.45, f"parking:{i}")
            # Clipped boxwood belongs to managed parking landscaping, not a wild
            # highway verge. The five-point ground/road checks still apply.
            outside = np.array([q.x, q.y]) - vector / np.linalg.norm(vector) * 1.5
            place("boxwood", outside, 0.65, f"parking-landscaping:{i}", natural=True)
    # Authored Fab planting plans only. In particular never put greenery into
    # Bie?e?stwa's gravel island: the reference explicitly shows no shrubs there.
    for plan in islands:
        poly = plan["poly"].buffer(-0.35)
        choices = [a for a in plan["assets"] if a in ready and a in GROUND_IDS]
        if not choices or poly.is_empty:
            continue
        x0, y0, x1, y1 = poly.bounds
        island_count = 0
        for x in np.arange(x0 + 1.0, x1, 3.5):
            for y in np.arange(y0 + 1.0, y1, 3.5):
                if island_count >= 12:  # per-island cap, WORKING_VALUE
                    break
                seed = f"island:{plan['id']}:{x:.2f}:{y:.2f}"
                if hf(seed, "share") > 0.45:
                    continue
                aid = choices[int(hf(seed, "kind") * len(choices)) % len(choices)]
                radius = 0.35 if "grass" in aid else 0.65
                p = np.array([x + (hf(seed, "jx") - .5), y + (hf(seed, "jy") - .5)])
                if place(aid, p, radius, seed, island=poly):
                    island_count += 1
    for c in sorted(net.chains, key=lambda c: c.id):
        if c.meta.get("absorbed") or c.roundabout:
            continue
        for s in np.arange(c.t_a + 12 + 20 * hf(c.id, "natural-phase"), c.length - c.t_b - 12, 40.0):
            s = float(s)
            if c.bridge[c.idx(s)]:
                continue
            for side, sign in (("L", 1), ("R", -1)):
                kind, h, w, depth, mat = side_params(c, side, s)
                outer = side_extent(kind, h, w, depth, mat)
                seed = f"verge:{c.id}:{side}:{s:.2f}"
                u = hf(seed, "family")
                family = ("grass-clumps", "wild-grass") if u < 0.7 else (("elderberry",) if u < 0.86 else ("granite-rock", "small-granite-rock"))
                choices = [a for a in family if a in ready]
                if not choices:
                    continue
                aid = choices[int(hf(seed, "asset") * len(choices)) % len(choices)]
                radius = 0.35 if "grass" in aid else 0.65
                lat = sign * (float(c.hw_at(s)) + outer + radius + 0.35 + hf(seed, "offset") * 1.5)
                p = c.line.offset_point(s, lat)
                place(aid, p, radius, seed, natural=True)
    report["props"] = counts
    report["added_props"] = total
    report["region_prop_cap_WORKING_VALUE"] = MAX_PROPS


def apply(w, pl, roads_poly, bpoly, paved, park_polys, route, report, log, overrides=(), deck_at=None):
    """Called after ordinary street props, before their final audits."""
    assets = load_ready()
    rep = {"available": sorted(assets), "placement_status": "WORKING_VALUE"}
    if not assets:
        message = "Fab Megascans unavailable/unreviewed; retaining existing world materials and props"
        log("WARNING:", message)
        rep["fallback"] = True
    else:
        drainage(w.buf, w.net, assets, rep)
        # Read shape from the successfully generated island mesh, not the raw
        # override point. Only explicit fab_plants is authority to change its flora.
        islands = []
        for override in overrides:
            if override.get("kind") != "plantings":
                continue
            for i, island in enumerate(override.get("islands", [])):
                choices = island.get("fab_plants", [])
                if not isinstance(choices, list) or not choices or island.get("fill", "soil") == "paving":
                    continue
                src = f"override:{override['id']}:island{i}"
                polygons = [shapely.geometry.Polygon(tri[:, :2]) for part in w.buf.parts
                            if part.layer == "paved" and part.src == src
                            for tri in part.V[part.T]]
                if polygons:
                    islands.append({"id": src, "poly": shapely.union_all(polygons), "assets": choices})
        props(pl, w.net, assets, roads_poly, bpoly, paved, park_polys, route, rep, islands=islands, deck_at=deck_at)
    report["megascans"] = rep
