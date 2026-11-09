"""Building footprints + heights for a tile.

Footprints : BDOT10k OT_BUBD_A (GUGiK, 2024-09 version for powiat 2061; geometry source mostly EGiB).
Heights    : joined by BDOT10k LOKALNYID == CityGML `buildingId`:
               1. GUGiK LoD1 2024 `measuredHeight`            -> height_source "gugik_lod1_2024"
               2. GUGiK LoD2 2017 (max roof z - ground z)     -> "gugik_lod2_2017"
               3. BDOT10k LICZBAKONDYGNACJI * 3.0 m (+1.0)    -> "bdot10k_storeys"   (WORKING_VALUE factor)
               4. default 6.0 m                               -> "default"
Extra      : OSM buildings with < 30 % overlap with any BDOT10k footprint are added (newer than BDOT
             or missing there) with height from OSM `height` / `building:levels` * 3.0 + 1.0 / default.
LoD2 heights are relative (roof z - ground z), so the KRON86 vs EVRF2007 datum difference of the
2017 models cancels out; absolute LoD2 z is NOT used anywhere.
"""

from __future__ import annotations

import hashlib
import pickle
import re
import zipfile
from pathlib import Path
from xml.etree.ElementTree import iterparse

import numpy as np
import shapely

BLDG = "{http://www.opengis.net/citygml/building/2.0}"
GML = "{http://www.opengis.net/gml}"
GEN = "{http://www.opengis.net/citygml/generics/2.0}"
STOREY_M = 3.0          # WORKING_VALUE: typical storey height
BASE_M = 1.0            # WORKING_VALUE: plinth + roof allowance
DEFAULT_H = 6.0         # WORKING_VALUE: unknown building


def _coords(el) -> np.ndarray:
    vals = []
    for p in el.iter():
        if p.tag in (f"{GML}pos", f"{GML}posList") and p.text:
            vals.extend(p.text.split())
    if not vals:
        return np.zeros((0, 3))
    return np.asarray(vals, dtype=np.float64).reshape(-1, 3)


def _rings(el) -> list[np.ndarray]:
    out = []
    for ring in el.iter(f"{GML}LinearRing"):
        c = _coords(ring)
        if len(c) >= 4:
            out.append(c)
    return out


def _envelope_hits(head: bytes, bbox) -> bool:
    m = re.search(rb"<gml:lowerCorner>([^<]+)</gml:lowerCorner>\s*<gml:upperCorner>([^<]+)</gml:upperCorner>", head)
    if not m:
        return True
    lo = [float(v) for v in m.group(1).split()]
    hi = [float(v) for v in m.group(2).split()]
    return not (hi[0] < bbox[0] or lo[0] > bbox[2] or hi[1] < bbox[1] or lo[1] > bbox[3])


def parse_citygml_zip(zpath: Path, bbox, lod: int) -> dict[str, dict]:
    tile = shapely.box(*bbox)
    out: dict[str, dict] = {}
    srs = set()
    with zipfile.ZipFile(zpath) as zf:
        for name in sorted(n for n in zf.namelist() if n.lower().endswith(".gml")):
            with zf.open(name) as f:
                head = f.read(6000)
            if not _envelope_hits(head, bbox):
                continue
            m = re.search(rb'srsName="([^"]+)"', head)
            if m:
                srs.add(m.group(1).decode())
            with zf.open(name) as f:
                for _, el in iterparse(f, events=("end",)):
                    if el.tag != f"{BLDG}Building":
                        continue
                    rec = _building_record(el, lod)
                    el.clear()
                    if rec and rec["footprint"] is not None and rec["footprint"].intersects(tile):
                        out[rec["id"]] = rec
    for r in out.values():
        r["srs"] = sorted(srs)
    return out


def _building_record(el, lod: int) -> dict | None:
    bid = None
    for a in el.iter(f"{GEN}stringAttribute"):
        if a.get("name") == "buildingId":
            v = a.find(f"{GEN}value")
            bid = v.text.strip() if v is not None and v.text else None
    if not bid:
        return None
    allc = _coords(el)
    if len(allc) == 0:
        return None
    zmin, zmax = float(allc[:, 2].min()), float(allc[:, 2].max())
    rec = {"id": bid, "zmin": zmin, "zmax": zmax}
    mh = el.find(f"{BLDG}measuredHeight")
    rec["measured_height"] = float(mh.text) if mh is not None and mh.text else None
    rt = el.find(f"{BLDG}roofType")
    rec["roof_type"] = rt.text if rt is not None else None
    # footprint: horizontal rings at the lowest z (LoD1 bottom face / LoD2 GroundSurface)
    if lod == 2:
        grounds = [r for gs in el.iter(f"{BLDG}GroundSurface") for r in _rings(gs)]
        roofs = [r for rs in el.iter(f"{BLDG}RoofSurface") for r in _rings(rs)]
        rec["eave_z"] = float(min(r[:, 2].min() for r in roofs)) if roofs else None
    else:
        grounds = [r for r in _rings(el) if np.ptp(r[:, 2]) < 0.01 and abs(r[0, 2] - zmin) < 0.01]
    polys = [shapely.Polygon(r[:, :2]) for r in grounds]
    polys = [p if p.is_valid else p.buffer(0) for p in polys if p.area > 0.5]
    rec["footprint"] = shapely.union_all(polys) if polys else None
    return rec


def cached_citygml(zpath: Path, bbox, lod: int, cache_dir: Path, sha: str) -> dict[str, dict]:
    key = hashlib.sha1(f"{sha}{bbox}{lod}v1".encode()).hexdigest()[:16]
    p = cache_dir / f"citygml_lod{lod}_{key}.pkl"
    if p.exists():
        return pickle.loads(p.read_bytes())
    print(f"[buildings] parsing {zpath.name} (LoD{lod}) for tile")
    res = parse_citygml_zip(zpath, bbox, lod)
    cache_dir.mkdir(parents=True, exist_ok=True)
    p.write_bytes(pickle.dumps(res))
    return res


def _num(v):
    try:
        f = float(str(v).replace(",", ".").replace("m", "").strip())
        return f if np.isfinite(f) else None
    except (TypeError, ValueError):
        return None


def _s(v):
    """NaN/None -> None (JSON must not contain NaN)."""
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return None
    return v


CONFIDENCE = {"gugik_lod1_2024": "high", "gugik_lod2_2017": "medium", "bdot10k_storeys": "medium",
              "osm_height": "medium", "osm_levels": "low", "default": "low"}


def merge(bdot, lod1: dict, lod2: dict, osm, bbox) -> list[dict]:
    tile = shapely.box(*bbox)
    feats: list[dict] = []
    bdot = bdot[bdot.geometry.intersects(tile)].sort_values("LOKALNYID")
    for r in bdot.itertuples():
        bid = r.LOKALNYID
        l1, l2 = lod1.get(bid), lod2.get(bid)
        h1 = l1["measured_height"] if l1 else None
        if l1 and h1 is None:
            h1 = l1["zmax"] - l1["zmin"]
        h2 = (l2["zmax"] - l2["zmin"]) if l2 else None
        storeys = None if r.LICZBAKONDYGNACJI is None or np.isnan(r.LICZBAKONDYGNACJI) else int(r.LICZBAKONDYGNACJI)
        if h1 is not None and h1 > 0.5:
            h, src = h1, "gugik_lod1_2024"
        elif h2 is not None and h2 > 0.5:
            h, src = h2, "gugik_lod2_2017"
        elif storeys:
            h, src = storeys * STOREY_M + BASE_M, "bdot10k_storeys"
        else:
            h, src = DEFAULT_H, "default"
        feats.append({
            "id": f"bdot:{bid}", "footprint_source": "bdot10k", "geometry": r.geometry,
            "height_m": round(h, 2), "height_source": src,
            "height_lod1_2024_m": None if h1 is None else round(h1, 2),
            "height_lod2_2017_m": None if h2 is None else round(h2, 2),
            "lod2_eave_rel_m": None if not l2 or l2.get("eave_z") is None else round(l2["eave_z"] - l2["zmin"], 2),
            "roof_type_lod2": l2["roof_type"] if l2 else None,
            "ground_z_evrf2007": None if not l1 else round(l1["zmin"], 2),
            "storeys": storeys, "function": _s(r.PRZEWAZAJACAFUNKCJABUDYNKU), "name": _s(r.NAZWA),
            "state": _s(r.KATEGORIAISTNIENIA), "height_confidence": CONFIDENCE[src],
        })
    # OSM buildings not represented in BDOT10k
    bgeoms = [f["geometry"] for f in feats]
    tree = shapely.STRtree(bgeoms)
    osm = osm[osm.geometry.intersects(tile)].sort_values(["osm_type", "osm_id"])
    for r in osm.itertuples():
        g = r.geometry
        if not g.is_valid:
            g = g.buffer(0)
        cov = 0.0
        for j in tree.query(g):
            cov += g.intersection(bgeoms[int(j)]).area
        if g.area <= 0 or cov / g.area >= 0.3:
            continue
        ht, lv = _num(r.height), _num(r.levels)
        if ht:
            h, src = ht, "osm_height"
        elif lv:
            h, src = lv * STOREY_M + BASE_M, "osm_levels"
        else:
            h, src = DEFAULT_H, "default"
        feats.append({
            "id": f"osm:{r.osm_type}/{r.osm_id}", "footprint_source": "osm", "geometry": g,
            "height_m": round(h, 2), "height_source": src, "height_lod1_2024_m": None,
            "height_lod2_2017_m": None, "lod2_eave_rel_m": None, "roof_type_lod2": None,
            "ground_z_evrf2007": None, "storeys": int(lv) if lv else None, "function": _s(r.building),
            "name": _s(r.name), "state": "construction" if r.building == "construction" else None,
            "osm_overlap_with_bdot": round(cov / g.area, 3), "height_confidence": CONFIDENCE[src],
            # building=roof is a canopy (fuel station, carport): no walls; importer must not extrude a block
            "is_roof_only": r.building == "roof",
        })
    return feats
