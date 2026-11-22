"""Surface water stage (ADR 0210): rivers, streams, canals, ponds and lakes as a carved bed + a flat water sheet.

Opt-in per region (`regions.py` Region.water -> `water: {enabled: true}` in region.yaml, written by build_region).
A region without the key is built exactly as before: no array is touched, no material / node / manifest key is
added (ADR 0210, determinism of tiles C and Dojlidy - both DO contain water: the Biała and streams in C, streams
and a retention basin in Dojlidy).

Sources (written once by build_region to Data/Regions/<id>/generated/water_sources.json, small, committed):
  BDOT10k OT_PTWP_A  water surface polygons (RODZAJ woda płynąca / stojąca), traced on the orthophoto - the river
                     outline (matches the dark water of the 2024 orthophoto at the Supraśl / Biała confluence).
  BDOT10k OT_SWRS_L  river / stream centre lines with SZEROKOSC (m) - flow direction and width of rivers without
                     a polygon.
  OSM (ODbL)         waterway=river|stream|canal (not tunnel=culvert) centre lines with `width`;
                     natural=water / waterway=riverbank / landuse=reservoir areas (not intermittent=yes) - ponds.
Ditches and drains (hundreds of field drains, mostly dry on the orthophoto) are not water bodies here.

Geometry (all WORKING_VALUE until checked against a survey / owner photo):
  - water level: rivers - per 5 m centre-line station, the 30th percentile of the NMT inside the water polygon
    within 8 m, smoothed and made non-increasing downstream; still water - 30th percentile of the polygon's NMT.
    The GUGiK NMT over water is the (interpolated) water surface, so this is the surface of the survey day.
  - bed: level - min(DEPTH, BED0 + BED_SLOPE * distance inside the shore); bank: the terrain within BANK_M of the
    shore is capped at level + FREEBOARD + BANK_SLOPE * distance (shallow 1:3 bank) and lifted to level + LIP within
    LIP_M, so the sheet (extended SHEET_OVERLAP_M under the bank) never shows a gap at the shore.
  - roads / paved areas (`mask`) are never carved; bridge decks are not in that mask, so the bed runs under them.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import shapely
from scipy import ndimage

SCHEMA = "truck-sim-pl/water-sources/1"
REPO = Path(__file__).resolve().parents[3]

FLOW_WATERWAYS = ("river", "stream", "canal")
DEFAULT_WIDTH_M = {"river": 8.0, "stream": 2.0, "canal": 4.0}     # WORKING_VALUE when neither OSM nor BDOT has one
DEPTH_M = {"river": 1.2, "stream": 0.45, "canal": 0.8, "still": 1.0}    # WORKING_VALUE (bed below the level)
BED0_M = 0.12            # bed just inside the shore (m below the level)
BED_SLOPE = 0.35         # m per m inside the shore (about 1:3)
BANK_M = 10.0            # bank band outside the shore that may be lowered
FREEBOARD_M = 0.18       # bank top at the shore above the level
BANK_SLOPE = 1.0 / 3.0   # shallow bank
LIP_M = 2.5              # within this band outside the shore the ground is at least level + LIP_Z_M (ADR 0324: 1.5 -> 2.5, bays reach 1.5)
LIP_Z_M = 0.04
SHEET_OVERLAP_M = 1.0    # the water sheet extends this far under the bank (hidden by the lip)
ROAD_KEEP_M = 2.0        # terrain this close to a road / paved node is not lowered (conformed embankments stay)
STATION_M = 5.0
LEVEL_PCT = 30.0
MIN_AREA_M2 = 30.0
FLOW_SMOOTH_M = 6.0      # gaussian sigma of the flow direction field (m)
SEAM_BLEND_M = 120.0     # ADR 0213: water crossing a tile edge is pulled to the shared edge level over this distance
# ADR 0324 (critic s24 wave 6 # 3.2: "the grass / water boundary is ruler-straight, no scarp, no mud"). WORKING_VALUE.
# The shore of a lowland river is not the BDOT outline: bays, mud spits and a wet margin. A smooth noise (SHORE_NOISE_M
# correlation, deterministic per absolute EPSG:2180 node) moves the ground in the first metre either side of the outline
# through the water level, so the visible water line wanders by up to ~1 m; behind it lies a band of wet mud / sand
# MUD_BAND_M wide (ground mask A = bare soil, shader: darker, no sward) that the same noise breaks up.
SHORE_NOISE_M = 3.0      # gaussian sigma of the shore noise (m)
SHORE_DIP_M = 0.10       # land nodes within 1 m of the outline may dip this far below the level (bays; sheet overlap 1 m)
SHORE_BAR_M = 0.07       # bed nodes within 2 m of the outline may rise this far above the level (mud spits)
MUD_BAND_M = (0.6, 2.6)  # width range of the wet mud / sand margin outside the water line
MUD_A = 0.70             # bare-soil mask in the margin (r2: 0.85 read as a beige road along the shore)
BAY_SHEET_M = 1.3        # half size of the sheet patch around a bay node (crossing <= 0.72 x 1.41 m from the node)


# ------------------------------------------------------------------------------------------------ extraction
def _round_coords(g):
    if g.geom_type == "LineString":
        return {"type": "LineString", "coordinates": [[round(x, 2), round(y, 2)] for x, y in g.coords]}
    if g.geom_type == "Polygon":
        return {"type": "Polygon", "coordinates": [[[round(x, 2), round(y, 2)] for x, y in r.coords]
                                                  for r in [g.exterior, *g.interiors]]}
    raise ValueError(g.geom_type)


def _parts(g):
    if g.is_empty:
        return []
    if hasattr(g, "geoms"):
        out = []
        for p in g.geoms:
            out += _parts(p)
        return out
    return [g]


def extract_osm(bbox, pbf: Path) -> dict:
    import osmium
    from pyproj import Transformer
    from shapely import wkb
    tr = Transformer.from_crs("EPSG:4326", "EPSG:2180", always_xy=True)
    inv = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
    lo = inv.transform(bbox[0] - 100, bbox[1] - 100)
    hi = inv.transform(bbox[2] + 100, bbox[3] + 100)
    llbox = shapely.box(lo[0], lo[1], hi[0], hi[1])
    tile = shapely.box(*bbox).buffer(60.0, join_style="mitre")     # a little beyond the tile: levels at the seams

    def proj(g):
        return shapely.transform(g, lambda xy: np.column_stack(tr.transform(xy[:, 0], xy[:, 1])))

    keep = ("waterway", "natural", "water", "name", "width", "intermittent", "tunnel", "layer", "landuse", "basin")
    wkbf = osmium.geom.WKBFactory()
    lines, areas = [], []
    fp = (osmium.FileProcessor(str(pbf)).with_locations()
          .with_areas(osmium.filter.KeyFilter("natural", "waterway", "landuse"))
          .with_filter(osmium.filter.KeyFilter("waterway", "natural", "landuse")))
    for obj in fp:
        t = obj.tags
        tags = {k: t.get(k) for k in keep if t.get(k) is not None}
        if obj.is_way():
            if t.get("waterway") not in FLOW_WATERWAYS or t.get("tunnel") in ("culvert", "yes"):
                continue
            try:
                pts = [(n.location.lon, n.location.lat) for n in obj.nodes]
            except osmium.InvalidLocationError:
                continue
            if len(pts) < 2:
                continue
            ll = shapely.LineString(pts)
            if not ll.intersects(llbox):
                continue
            g = proj(ll).intersection(tile)
            for k, part in enumerate(_parts(g)):
                if part.geom_type == "LineString" and part.length >= 1.0:
                    lines.append({"osm_way": obj.id, "part": k, "tags": tags,
                                  "geometry": _round_coords(part.simplify(0.2))})
        elif obj.is_area():
            water = (t.get("natural") == "water" or t.get("waterway") == "riverbank"
                     or t.get("landuse") == "reservoir")
            if not water:
                continue
            try:
                g = wkb.loads(wkbf.create_multipolygon(obj), hex=True)
            except Exception:
                continue
            if not g.intersects(llbox):
                continue
            g = shapely.make_valid(proj(g)).intersection(tile)
            for k, part in enumerate(_parts(g)):
                if part.geom_type == "Polygon" and part.area >= 4.0:
                    areas.append({"osm_id": obj.orig_id(), "osm_type": "way" if obj.from_way() else "relation",
                                  "part": k, "tags": tags, "geometry": _round_coords(part.simplify(0.1))})
    lines.sort(key=lambda d: (d["osm_way"], d["part"]))
    areas.sort(key=lambda d: (d["osm_type"], d["osm_id"], d["part"]))
    return {"lines": lines, "areas": areas}


def extract_bdot(bbox, gpkg_zip: Path, gdir: Path) -> dict:
    import pyogrio
    import sys
    sys.path.insert(0, str(REPO / "tools" / "worldgen"))
    from build_region import extract_from_zip
    tile = shapely.box(*bbox).buffer(60.0, join_style="mitre")
    out = {}
    for layer, cols in (("OT_PTWP_A", ("RODZAJ", "NAZWA")), ("OT_SWRS_L", ("RODZAJ", "NAZWA", "SZEROKOSC", "POLOZENIE"))):
        try:
            gp = extract_from_zip(gpkg_zip, f"__{layer}.gpkg", gdir)
        except StopIteration:
            out[layer] = []
            continue
        df = pyogrio.read_dataframe(gp, bbox=tuple(tile.bounds))
        df = df.sort_values("LOKALNYID").reset_index(drop=True)
        feats = []
        for r in df.itertuples():
            g = shapely.make_valid(r.geometry).intersection(tile)
            props = {}
            for c in cols:
                v = getattr(r, c, None)
                if v is None or (isinstance(v, float) and math.isnan(v)):
                    continue
                props[c.lower()] = v.item() if hasattr(v, "item") else v
            for k, part in enumerate(_parts(g)):
                if part.geom_type not in ("LineString", "Polygon"):
                    continue
                if part.geom_type == "Polygon" and part.area < 4.0:
                    continue
                feats.append({"id": f"{r.LOKALNYID}:{k}", "props": props,
                              "geometry": _round_coords(part.simplify(0.1))})
        out[layer] = feats
    return out


def extract(region: dict) -> dict:
    import sys
    sys.path.insert(0, str(REPO / "tools" / "worldgen"))
    from build_region import manifest_files
    from fetch_osm import download
    b = region["bbox"]
    bbox = (b["xmin"], b["ymin"], b["xmax"], b["ymax"])
    # ADR 0219 (coordination point with 0213): every powiat the tile overlaps, not only region["teryt_powiat"];
    # one powiat -> the same call and output as before.
    from powiaty import merge_layers, powiaty_for_bbox
    pw = powiaty_for_bbox(bbox)
    bdot = None
    for t in pw:
        more = extract_bdot(bbox, manifest_files(f"gugik-bdot10k-{t}")[0],
                            REPO / "Data" / "raw" / "gugik" / f"bdot10k-{t}" / "gpkg")
        bdot = more if bdot is None else merge_layers(bdot, more)
    return {"schema": SCHEMA, "crs": "EPSG:2180", "bbox": list(bbox), "margin_m": 60.0,
            "license": {"osm": "ODbL 1.0, © OpenStreetMap contributors",
                        "bdot10k": "GUGiK BDOT10k (powiat %s), free use, art. 40a ust. 2 pkt 1 Pgik" % ", ".join(pw)},
            "osm": extract_osm(bbox, download()), "bdot10k": bdot}


def sources_path(region_id: str) -> Path:
    return REPO / "Data" / "Regions" / region_id / "generated" / "water_sources.json"


def write(region_id: str, data: dict) -> Path:
    p = sources_path(region_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    if not p.exists() or p.read_text(encoding="utf-8") != text:
        p.write_text(text, encoding="utf-8", newline="\n")
    return p


def enabled(region: dict) -> bool:
    """The stage runs only for regions that opted in (region.yaml `water: {enabled: true}`)."""
    wt = region.get("water")
    return bool(isinstance(wt, dict) and wt.get("enabled"))


def load(region_id: str) -> dict | None:
    p = sources_path(region_id)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


# ------------------------------------------------------------------------------------------------ plan
def _local(g, origin):
    return shapely.transform(shapely.geometry.shape(g), lambda xy: xy - np.asarray(origin, float))


def _flowing_area(tags: dict) -> bool:
    return tags.get("waterway") == "riverbank" or tags.get("water") in ("river", "stream", "canal", "oxbow")


def _width(line: dict) -> float:
    try:
        w_ = float(str(line["tags"].get("width", "")).replace(",", ".").split()[0])
        if 0.3 <= w_ <= 200:
            return w_
    except (ValueError, IndexError):
        pass
    return DEFAULT_WIDTH_M.get(line["tags"].get("waterway"), 2.0)


class Plan:
    """Water bodies of one region in local metres (E, N) + level / depth fields on the 1 m terrain grid."""

    def __init__(self, src: dict, origin, hf, tile_local, road_poly):
        self.hf = hf
        self.report = {"bodies": [], "skipped": []}
        bd = src["bdot10k"]
        osm = src["osm"]
        flow_polys, still_polys = [], []
        for f in bd.get("OT_PTWP_A", []):
            g = _local(f["geometry"], origin)
            (flow_polys if f["props"].get("rodzaj") == "woda płynąca" else still_polys).append(g)
            self.report["bodies"].append({"src": "bdot10k:OT_PTWP_A:" + f["id"], "kind": f["props"].get("rodzaj"),
                                          "name": f["props"].get("nazwa"), "area_m2": round(g.area)})
        bdot_flow = shapely.union_all([shapely.make_valid(p) for p in flow_polys]) if flow_polys else None
        for a in osm["areas"]:
            t = a["tags"]
            sid = f"osm:{a['osm_type']}/{a['osm_id']}:{a['part']}"
            if t.get("intermittent") == "yes":
                self.report["skipped"].append({"src": sid, "why": "intermittent=yes"})
                continue
            g = _local(a["geometry"], origin)
            if _flowing_area(t) and bdot_flow is not None and g.intersects(bdot_flow):
                # BDOT10k traced the same river on the 2024 orthophoto and follows the dark water more closely
                # (dk65-02: OSM riverbank juts 3-5 m onto the meadow SE of the bridge); a union would widen it
                self.report["skipped"].append({"src": sid, "why": "river outline also in BDOT10k OT_PTWP_A"})
                continue
            (flow_polys if _flowing_area(t) else still_polys).append(g)
            self.report["bodies"].append({"src": sid, "kind": t.get("water") or t.get("waterway") or "water",
                                          "name": t.get("name"), "area_m2": round(g.area)})
        flow_u = shapely.union_all([shapely.make_valid(p) for p in flow_polys]) if flow_polys else shapely.Polygon()
        # centre lines (flow direction): OSM waterway ways are drawn downstream; BDOT SWRS direction is checked
        lines = []
        for ln in osm["lines"]:
            lines.append({"src": f"osm:way/{ln['osm_way']}:{ln['part']}", "kind": ln["tags"]["waterway"],
                          "name": ln["tags"].get("name"), "g": _local(ln["geometry"], origin),
                          "width": _width(ln), "osm": True})
        for f in bd.get("OT_SWRS_L", []):
            wd = f["props"].get("szerokosc")
            lines.append({"src": "bdot10k:OT_SWRS_L:" + f["id"],
                          "kind": "river" if f["props"].get("rodzaj") == "rzeka" else "stream",
                          "name": f["props"].get("nazwa"), "g": _local(f["geometry"], origin), "osm": False,
                          "width": float(wd) if wd else DEFAULT_WIDTH_M["stream"]})
        # OSM channels outside every outline become buffered channels (streams without a polygon)
        chan = []
        for ln in lines:
            if not ln["osm"]:
                continue
            rest = ln["g"].difference(flow_u.buffer(1.0)) if not flow_u.is_empty else ln["g"]
            if rest.length >= 3.0:
                chan.append(rest.buffer(ln["width"] / 2.0, cap_style="flat", join_style="round"))
        if chan:
            flow_u = shapely.union_all([flow_u] + chan)
        still_u = shapely.union_all([shapely.make_valid(p) for p in still_polys]) if still_polys else shapely.Polygon()
        still_u = still_u.difference(flow_u) if not still_u.is_empty else still_u
        clip = tile_local.buffer(2.0, join_style="mitre")
        self.flow = flow_u.intersection(clip) if not flow_u.is_empty else flow_u
        sp = [p for p in _parts(still_u.intersection(clip)) if p.area >= MIN_AREA_M2] if not still_u.is_empty else []
        self.still = shapely.union_all(sp) if sp else shapely.Polygon()
        self.lines = [ln for ln in lines if ln["g"].length >= STATION_M]
        self.road_poly = road_poly
        self.tile = tile_local
        self._fields()

    # -------------------------------------------------------------------------------------------- fields
    def _raster(self, g):
        from streetscape import paved as PV
        return PV.rasterize_polys([p for p in _parts(g) if p.geom_type == "Polygon"], self.hf)

    def _fields(self):
        from scipy.spatial import cKDTree
        from streetscape import paved as PV
        hf = self.hf
        H, W_ = hf.z.shape
        z = hf.z
        fmask = self._raster(self.flow) if not self.flow.is_empty else np.zeros((H, W_), bool)
        smask = self._raster(self.still) if not self.still.is_empty else np.zeros((H, W_), bool)
        smask &= ~fmask
        level = np.full((H, W_), np.nan)
        depth = np.zeros((H, W_))
        # still water: one level per connected body
        lab, n = ndimage.label(smask)
        still_rep = []
        for k in range(1, n + 1):
            m = lab == k
            core = ndimage.binary_erosion(m, iterations=1)
            vals = z[core] if core.sum() >= 4 else z[m]
            lv = float(np.percentile(vals, LEVEL_PCT))
            level[m] = lv
            depth[m] = DEPTH_M["still"]
            jj_, ii_ = np.nonzero(m)
            still_rep.append({"nodes": int(m.sum()), "level_m": round(lv, 2),
                              "at_local_en": [round(float(hf.x0 + ii_.mean()), 1), round(float(hf.y1 - jj_.mean()), 1)]})
        # flowing water: levels along the centre lines
        st_xy, st_z, st_d, prof = [], [], [], []
        jj, ii = np.nonzero(fmask)
        fe = hf.x0 + ii
        fn = hf.y1 - jj
        kd = cKDTree(np.column_stack([fe, fn])) if len(fe) else None
        for ln in self.lines:
            g = ln["g"]
            s = np.arange(0.0, g.length + 1e-6, STATION_M)
            P = np.array([[g.interpolate(x).x, g.interpolate(x).y] for x in s])
            lv = np.full(len(P), np.nan)
            if kd is not None:
                for q, p in enumerate(P):
                    idx = kd.query_ball_point(p, 8.0)
                    if len(idx) >= 3:
                        lv[q] = np.percentile(z[jj[idx], ii[idx]], LEVEL_PCT)
            if np.isfinite(lv).sum() < 2:
                # line far from every outline: lowest NMT within the half width + 1 m
                r_ = ln["width"] / 2.0 + 1.0
                ee, nn = np.meshgrid(np.arange(-r_, r_ + 0.1, 1.0), np.arange(-r_, r_ + 0.1, 1.0))
                for q, p in enumerate(P):
                    lv[q] = float(np.min(PV.bilinear(z, hf, p[0] + ee.ravel(), p[1] + nn.ravel())))
            ok = np.isfinite(lv)
            if ok.sum() < 2:
                continue
            raw = np.interp(s, s[ok], lv[ok])
            lv = ndimage.median_filter(raw, size=7, mode="nearest")
            flipped = False
            if not ln["osm"]:
                k3 = max(1, len(lv) // 3)
                if lv[:k3].mean() < lv[-k3:].mean():        # BDOT line drawn upstream: flow = falling level
                    lv, P, raw, flipped = lv[::-1], P[::-1], raw[::-1], True
            lv = np.minimum.accumulate(lv)                  # water never flows uphill
            st_xy.append(P)
            st_z.append(lv)
            st_d.append(np.full(len(lv), DEPTH_M.get(ln["kind"], DEPTH_M["stream"])))
            prof.append({"src": ln["src"], "name": ln["name"], "kind": ln["kind"], "len_m": round(g.length),
                         "level_first_m": round(float(lv[0]), 2), "level_last_m": round(float(lv[-1]), 2),
                         "raw_min_max_m": [round(float(raw.min()), 2), round(float(raw.max()), 2)],
                         "reversed": flipped, "stations": len(lv)})
        if st_xy and fmask.any():
            SP, SZ, SD = np.concatenate(st_xy), np.concatenate(st_z), np.concatenate(st_d)
            d, k = cKDTree(SP).query(np.column_stack([fe, fn]), k=min(6, len(SP)))
            d, k = d.reshape(len(fe), -1), k.reshape(len(fe), -1)
            wgt = 1.0 / np.maximum(d, 1.0) ** 2
            level[jj, ii] = (SZ[k] * wgt).sum(1) / wgt.sum(1)
            depth[jj, ii] = SD[k[:, 0]]
        elif fmask.any():
            lab, n = ndimage.label(fmask)
            for k_ in range(1, n + 1):
                m = lab == k_
                level[m] = float(np.percentile(z[m], LEVEL_PCT))
                depth[m] = DEPTH_M["river"]
        self.report["seams"] = self._seam_levels(level, fmask | smask)
        self._stations = st_xy
        self._fmask = fmask
        self.mask = np.isfinite(level)
        self.level = level
        self.depth = depth
        self.report["still_levels"] = still_rep
        self.report["profiles"] = prof
        self.report["water_nodes"] = int(self.mask.sum())

    def _seam_levels(self, level, wmask):
        """ADR 0213: a river that crosses a tile edge gets the SAME level on both tiles. Each tile derives its levels
        from its own stations (median window and the downstream running minimum start at its own end of the line), so
        two neighbours differed by ~3 cm on the shared edge (dk65-02 | dk65-03). The edge column / row of the NMT is
        shared by both tiles, so the 30th percentile of the NMT on the crossing nodes is a value both compute alike:
        the level there is set to it exactly and the correction fades linearly over SEAM_BLEND_M inside the tile."""
        from scipy.spatial import cKDTree
        z = self.hf.z
        H, W_ = z.shape
        rep = []
        jj, ii = np.nonzero(wmask)
        if not len(jj):
            return rep
        corr = np.zeros(len(jj))
        for name, j_, i_ in (("W", np.arange(H), np.zeros(H, int)), ("E", np.arange(H), np.full(H, W_ - 1)),
                             ("N", np.zeros(W_, int), np.arange(W_)), ("S", np.full(W_, H - 1), np.arange(W_))):
            m = wmask[j_, i_]
            lab, n = ndimage.label(m)
            for k in range(1, n + 1):
                sel = lab == k
                if sel.sum() < 3:
                    continue
                cj, ci = j_[sel], i_[sel]
                target = float(np.percentile(z[cj, ci], LEVEL_PCT))
                own = level[cj, ci]
                d, q = cKDTree(np.column_stack([ci, cj])).query(np.column_stack([ii, jj]))
                wgt = np.clip(1.0 - d / SEAM_BLEND_M, 0.0, 1.0)
                corr += wgt * (target - own[q])
                rep.append({"edge": name, "nodes": int(sel.sum()), "level_m": round(target, 3),
                            "own_m": [round(float(np.nanmin(own)), 3), round(float(np.nanmax(own)), 3)]})
        level[jj, ii] = level[jj, ii] + corr
        return rep

    # -------------------------------------------------------------------------------------------- terrain
    def carve(self, zc, mask, log=print):
        """Bed inside the water, a shallow bank outside, a lip at the shore; roads / paved nodes untouched."""
        W = self.mask
        if not W.any():
            self.lfill = np.full(zc.shape, np.nan)
            self.d_in = np.zeros(zc.shape)
            self.d_out = np.full(zc.shape, np.inf)
            return zc
        keep = ndimage.binary_dilation(mask, iterations=int(ROAD_KEEP_M))
        d_in = ndimage.distance_transform_edt(W)
        d_out, (jn, in_) = ndimage.distance_transform_edt(~W, return_indices=True)
        L = self.level[jn, in_]
        Dp = self.depth[jn, in_]
        bed = L - np.minimum(Dp, BED0_M + BED_SLOPE * np.maximum(d_in - 0.5, 0.0))
        z = zc.copy()
        inw = W & ~keep
        z[inw] = np.minimum(z[inw], bed[inw])
        band = ~W & (d_out <= BANK_M) & ~keep
        cap = L + FREEBOARD_M + BANK_SLOPE * np.maximum(d_out - 1.0, 0.0)
        lowered = band & (z > cap)
        z[band] = np.minimum(z[band], cap[band])
        lip = ~W & (d_out <= LIP_M) & ~keep
        raised = lip & (z < L + LIP_Z_M)
        z[lip] = np.maximum(z[lip], L[lip] + LIP_Z_M)
        # ADR 0324: irregular water line (see SHORE_NOISE_M). Only nodes the sheet covers (overlap 1 m) may dip.
        nz = self._shore_noise()
        self.shore_nz = nz
        bay = ~W & (d_out <= 1.5) & ~keep & (nz < 0.0)      # r3: + diagonal neighbours (<= 1.0 dipped every other node of a diagonal shore = 1 m stairs)
        z[bay] = np.minimum(z[bay], L[bay] + LIP_Z_M + np.clip(nz[bay] * 2.0, -1.0, 0.0) * (SHORE_DIP_M + LIP_Z_M))
        bar = inw & (d_in <= 2.0) & (nz > 0.25)
        z[bar] = np.maximum(z[bar], np.minimum(L[bar] + np.clip((nz[bar] - 0.25) * 4.0, 0.0, 1.0) * SHORE_BAR_M
                                                 - 0.03 * (d_in[bar] - 1.0), L[bar] + SHORE_BAR_M))
        self.bay_mask = bay & (z < L + LIP_Z_M - 1e-6)
        self.report["shore"] = {"bay_nodes": int(self.bay_mask.sum()), "bar_nodes": int((bar & (z > L)).sum())}
        self.lfill = np.where(d_out <= BANK_M + 4.0, L, np.nan)
        self.d_in, self.d_out = d_in, d_out
        self.report["carve"] = {"bed_nodes": int(inw.sum()), "bed_lowered_m_max": round(float((zc - z)[inw].max()), 2),
                                "bank_nodes_lowered": int(lowered.sum()), "lip_nodes_raised": int(raised.sum()),
                                "water_nodes_kept_by_road": int((W & keep).sum())}
        log("water carve", self.report["carve"])
        return z

    def _shore_noise(self):
        """Smooth deterministic noise in [-1, 1] per terrain node (hash of the local node), 0 at the tile edge."""
        H, W_ = self.mask.shape
        hf = self.hf
        e0 = int(round(getattr(hf, "x0", 0.0)))
        n0 = int(round(getattr(hf, "y1", 0.0)))
        ee = (np.arange(W_, dtype=np.int64) + e0)[None, :]
        nn = (n0 - np.arange(H, dtype=np.int64))[:, None]
        hsh = (ee * 73856093) ^ (nn * 19349663) ^ 0x5F3759DF
        hsh = (hsh ^ (hsh >> 13)) * 1274126177
        r = ((hsh ^ (hsh >> 16)) & 0xFFFF).astype(np.float64) / 65535.0 - 0.5
        g = ndimage.gaussian_filter(r, SHORE_NOISE_M, mode="reflect")
        g = np.clip(g / max(float(np.std(g)), 1e-9) / 2.0, -1.0, 1.0)
        # no shore relief within 8 m of the tile edge: the neighbour tile computes its own noise (local node
        # indices), the terrain of the seam column must stay the plain ADR 0210 bank on both
        x0, y0, x1, y1 = self.tile.bounds
        E = hf.x0 + np.arange(W_)[None, :]
        N = hf.y1 - np.arange(H)[:, None]
        edge = np.minimum(np.minimum(E - x0, x1 - E), np.minimum(N - y0, y1 - N))
        return g * np.clip(edge / 8.0, 0.0, 1.0)

    def blocked(self):
        return ndimage.binary_dilation(self.mask, iterations=1)

    def lod_mask(self):
        """Water core for the coarse terrain LODs: min-filtered like the road footprint (bed never above the sheet)."""
        return ndimage.binary_erosion(self.mask, iterations=2)

    def bank_colours(self, col):
        """Ground masks (R road, G forest floor, B unmown, A bare soil): long grass on the banks, a mud line at the
        water, mud on the bed (seen only where a coarse LOD dips under the sheet edge)."""
        if not self.mask.any():
            return col
        c = col.copy()
        d = self.d_out
        bank = np.clip(1.0 - d / 6.0, 0.0, 1.0)
        c[..., 2] = np.maximum(c[..., 2], 0.85 * bank)
        c[..., 1] = c[..., 1] * (1.0 - bank)
        mud = np.clip(1.0 - d / 0.8, 0.0, 1.0) * 0.15      # thin wet line only: the orthophoto banks are green
        c[..., 3] = np.maximum(c[..., 3], mud)
        # ADR 0324: wet mud / sand margin, MUD_BAND_M wide by the shore noise (0 where the reed belt will hide it anyway
        # is not known here: the belt stands ON it, like on the Narew), fading over its outer 40 %
        nz = getattr(self, "shore_nz", None)
        if nz is not None:
            wband = MUD_BAND_M[0] + (MUD_BAND_M[1] - MUD_BAND_M[0]) * np.clip(nz * 0.5 + 0.5, 0.0, 1.0)
            m2 = np.clip((wband - d) / np.maximum(0.4 * wband, 0.2), 0.0, 1.0) * MUD_A
            m2 = np.where(self.mask, 0.0, m2)
            # r2: softened (sigma 1 node) - per-node steps of the mask drew triangle "stairs" along the bank (r1)
            m2 = np.where(self.mask, 0.0, ndimage.gaussian_filter(m2, 1.0))
            c[..., 3] = np.maximum(c[..., 3], m2)
            c[..., 2] = np.where(m2 > 0.3, c[..., 2] * (1.0 - 0.6 * m2), c[..., 2])
        c[..., 3] = np.where(self.mask, 0.7, c[..., 3])
        return c.astype(np.float32)

    # -------------------------------------------------------------------------------------------- sheet
    def sheet(self, buf, chunk_m, log=print):
        """Flat water sheet: outline + SHEET_OVERLAP_M (under the bank lip), minus the ground road footprint,
        split per chunk and on a 4 m world grid. COL = (shore distance / 8 m, depth / 1.5 m, flow E, flow N) * 0.5 + .5
        for the flow pair; UV0 = local metres (E, N)."""
        from streetscape import paved as PV
        if not self.mask.any():
            return 0
        bodies = [g for g in (self.flow, self.still) if not g.is_empty]
        sheet = shapely.union_all(bodies).buffer(SHEET_OVERLAP_M, join_style="round")
        bay = getattr(self, "bay_mask", None)
        if bay is not None and bay.any():
            # ADR 0324: a bay node lies below the level; the ground reaches the level again before its neighbours
            # (>= level + LIP_Z_M, 1-1.41 m away) - the sheet must cover that crossing: + a BAY_SHEET_M square per node
            jb, ib = np.nonzero(bay)
            eb, nb = self.hf.x0 + ib, self.hf.y1 - jb
            sheet = shapely.union_all(np.concatenate([[sheet], shapely.box(eb - BAY_SHEET_M, nb - BAY_SHEET_M,
                                                                          eb + BAY_SHEET_M, nb + BAY_SHEET_M)]))
        if not self.road_poly.is_empty:
            sheet = sheet.difference(self.road_poly.buffer(0.3))
        sheet = sheet.intersection(self.tile)
        x0, y0, x1, y1 = self.tile.bounds
        lf = np.where(np.isfinite(self.lfill), self.lfill, np.nanmean(self.level[self.mask]))
        dsh = np.where(self.mask, self.d_in, -self.d_out)
        flow_e, flow_n = self._flow_field()
        ntri = 0
        for cy in np.arange(y0, y1, chunk_m):
            for cx in np.arange(x0, x1, chunk_m):
                piece = sheet.intersection(shapely.box(cx, cy, cx + chunk_m, cy + chunk_m))
                for pg in _parts(piece):
                    if pg.geom_type != "Polygon" or pg.area < 1.0:
                        continue
                    T2 = PV.triangulate(pg, cell=4.0)
                    if not len(T2):
                        continue
                    P = T2.reshape(-1, 2)
                    q = np.round(P * 1000).astype(np.int64)
                    _, first, inv = np.unique(q, axis=0, return_index=True, return_inverse=True)
                    P = P[first]
                    Z = PV.bilinear(lf, self.hf, P[:, 0], P[:, 1])
                    sh = PV.bilinear(dsh, self.hf, P[:, 0], P[:, 1])
                    dp = PV.bilinear(np.where(self.mask, self.depth, 0.0), self.hf, P[:, 0], P[:, 1])
                    fe = PV.bilinear(flow_e, self.hf, P[:, 0], P[:, 1])
                    fn = PV.bilinear(flow_n, self.hf, P[:, 0], P[:, 1])
                    COL = np.column_stack([np.clip(sh / 8.0, 0, 1), np.clip(dp / 1.5, 0, 1),
                                           np.clip(fe * 0.5 + 0.5, 0, 1), np.clip(fn * 0.5 + 0.5, 0, 1)])
                    V = np.column_stack([P, Z])
                    T = inv.ravel().reshape(-1, 3)
                    buf.add("water", "water", V, P.copy(), T, src="water:sheet", COL=COL)
                    ntri += len(T)
        self.report["sheet"] = {"area_m2": round(sheet.area), "triangles": ntri}
        log("water sheet", self.report["sheet"])
        return ntri

    def _flow_field(self):
        """Unit flow direction (E, N) on the flowing-water nodes from the downstream tangent of the nearest centre-line
        station; zero on still water."""
        from scipy.spatial import cKDTree
        H, W_ = self.mask.shape
        fe = np.zeros((H, W_))
        fn = np.zeros((H, W_))
        if not self._stations or not self._fmask.any():
            return fe, fn
        P = np.concatenate(self._stations)
        D = np.concatenate([np.gradient(s_, axis=0) if len(s_) > 1 else np.zeros_like(s_) for s_ in self._stations])
        D /= np.maximum(np.linalg.norm(D, axis=1, keepdims=True), 1e-6)
        jj, ii = np.nonzero(self._fmask)
        _, k = cKDTree(P).query(np.column_stack([self.hf.x0 + ii, self.hf.y1 - jj]))
        fe[jj, ii] = D[k, 0]
        fn[jj, ii] = D[k, 1]
        # smooth across the switch from one centre line to the next (confluence): no seam in the ripple advection
        m = self._fmask.astype(float)
        den = np.maximum(ndimage.gaussian_filter(m, FLOW_SMOOTH_M), 1e-6)
        fe = np.where(self._fmask, ndimage.gaussian_filter(fe, FLOW_SMOOTH_M) / den, 0.0)
        fn = np.where(self._fmask, ndimage.gaussian_filter(fn, FLOW_SMOOTH_M) / den, 0.0)
        ln_ = np.maximum(np.hypot(fe, fn), 1e-6)
        return np.where(self._fmask, fe / ln_, 0.0), np.where(self._fmask, fn / ln_, 0.0)

    # -------------------------------------------------------------------------------------------- banks (ADR 0213)
    def bank_vegetation(self, buf, zground, keep_out, trees, blocked, rep, log=print):
        """Reed / tall-herb belt ribbons (layers `banks` High, `banks_low` Low / Medium) and willow / alder shrub
        instances from Data/Regions/<id>/water_banks.json (self.banks_doc; None = banks as in ADR 0210)."""
        from streetscape import paved as PV
        from streetscape import reeds as RD
        doc = getattr(self, "banks_doc", None)
        if doc is None or not self.mask.any():
            return []
        lv = np.where(self.mask, self.level, np.nan)

        def zlevel(e, n):
            i = np.clip(np.round(np.asarray(e, float) - self.hf.x0).astype(int), 0, lv.shape[1] - 1)
            j = np.clip(np.round(self.hf.y1 - np.asarray(n, float)).astype(int), 0, lv.shape[0] - 1)
            return lv[j, i]
        brep = {}
        RD.build(buf, doc, zground, zlevel, keep_out, brep, layer="banks", low=False)
        RD.build(buf, doc, zground, zlevel, keep_out, brep, layer="banks_low", low=True)

        def blocked_fn(e, n):
            i, j = int(round(e - self.hf.x0)), int(round(self.hf.y1 - n))
            if not (0 <= j < blocked.shape[0] and 0 <= i < blocked.shape[1]):
                return True
            return bool(blocked[j, i]) or bool(shapely.contains_xy(keep_out, e, n))
        out = RD.shrubs(doc, zground, trees, blocked_fn, brep)
        self.report["banks"] = brep
        log("water banks", brep)
        return out

    def export_textures(self, tex_dir):
        """water_reeds.png next to the region's other generated textures (only regions with the water stage)."""
        import io
        from streetscape import reeds as RD
        tex_dir = Path(tex_dir)
        tex_dir.mkdir(parents=True, exist_ok=True)
        for k, im in RD.textures().items():
            b = io.BytesIO()
            im.save(b, format="PNG", optimize=False)
            p = tex_dir / f"{k}.png"
            if not p.exists() or p.read_bytes() != b.getvalue():
                p.write_bytes(b.getvalue())

