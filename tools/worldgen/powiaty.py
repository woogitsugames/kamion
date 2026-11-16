"""Which powiaty (TERYT county codes) a bbox touches — the one selector of GUGiK per-powiat packages (ADR 0219).

GUGiK ships BDOT10k, LoD1 and LoD2 per powiat. A region tile, a far-field ring (±4200 m around the anchor) or a
LoD2 lookup window can cross a powiat boundary; every stage that reads those packages asks this module instead of
hard-coding "2061" or reading only `region.teryt_powiat` (ADR 0208 „Otwarte” pkt 6).

Boundaries: Państwowy Rejestr Granic (PRG, GUGiK), WFS layer `ms:A02_Granice_powiatow`, clipped to an AOI and
simplified (SIMPLIFY_M), committed as Data/Admin/powiaty_prg.geojson (small; manifest gugik-prg-powiaty.json).
Re-fetch (also to grow the AOI for a new region):

    uv run --project tools/worldgen python tools/worldgen/powiaty.py --fetch [--aoi 740000 575000 800000 635000]
    uv run --project tools/worldgen python tools/worldgen/powiaty.py --report        # every region: tile + ring

A bbox that leaves the AOI raises (never a silent "no powiat").
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import xml.etree.ElementTree as ET
from functools import lru_cache
from pathlib import Path

import shapely
from shapely.geometry import Polygon, box, mapping, shape

REPO = Path(__file__).resolve().parents[2]
BOUNDARIES = REPO / "Data" / "Admin" / "powiaty_prg.geojson"
MANIFEST = REPO / "Data" / "SourceManifests" / "gugik-prg-powiaty.json"
WFS = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/PRG/WFS/AdministrativeBoundaries"
LAYER = "ms:A02_Granice_powiatow"
DEFAULT_AOI = (740000.0, 575000.0, 800000.0, 635000.0)   # EPSG:2180; all regions' far-field rings + >= 5 km
SIMPLIFY_M = 2.0                  # WORKING_VALUE: << any bbox we ask about (LoD2 window 120 m, tile 2048 m)
USER_AGENT = "Mozilla/5.0 (compatible; open-data GIS client)"
RING_MAX_M = 4200.0               # = streetscape.far_field.RING_MAX_M (asserted in tests)

GML = "{http://www.opengis.net/gml/3.2}"
MS = "{http://mapserver.gis.umn.edu/mapserver}"


# ------------------------------------------------------------------------------------------------ selection
def powiat_shares(bbox, boundaries: dict | None = None, aoi=None) -> dict[str, float]:
    """{teryt: share of the bbox area inside that powiat} for every powiat the bbox overlaps with positive area,
    ordered by share (desc), then code. bbox = (xmin, ymin, xmax, ymax) EPSG:2180."""
    if boundaries is None:
        aoi, boundaries = load()
    b = box(*bbox)
    if b.area <= 0:
        raise ValueError(f"empty bbox {bbox}")
    if aoi is not None and not box(*aoi).contains(b):
        raise ValueError(f"bbox {tuple(bbox)} leaves the powiat AOI {tuple(aoi)}: re-run "
                         f"`tools/worldgen/powiaty.py --fetch --aoi ...` with a larger AOI (ADR 0219)")
    out = {}
    for code in sorted(boundaries):
        a = boundaries[code].intersection(b).area
        if a > 0.0:
            out[code] = a / b.area
    return dict(sorted(out.items(), key=lambda kv: (-round(kv[1], 9), kv[0])))


def powiaty_for_bbox(bbox, boundaries: dict | None = None, aoi=None) -> tuple[str, ...]:
    """ADR 0219: every powiat the bbox overlaps (largest share first). Raises when nothing covers the bbox."""
    shares = powiat_shares(bbox, boundaries, aoi)
    if not shares:
        raise ValueError(f"no powiat polygon overlaps bbox {tuple(bbox)}")
    return tuple(shares)


def ring_bbox(origin, ring_max_m: float = RING_MAX_M):
    ox, oy = origin
    return (ox - ring_max_m, oy - ring_max_m, ox + ring_max_m, oy + ring_max_m)


def package_files(product: str, teryt: str) -> list[Path] | None:
    """Local files of a GUGiK per-powiat package from its manifest (product: 'bdot10k', 'lod1-2024', 'lod2-2017');
    None when the package was never ingested (no manifest) — callers record it as missing, never guess a path."""
    p = REPO / "Data" / "SourceManifests" / f"gugik-{product}-{teryt}.json"
    if not p.exists():
        return None
    return [REPO / f["local_path"] for f in json.loads(p.read_text(encoding="utf-8"))["files"]]


def merge_layers(first: dict, more: dict) -> dict:
    """{layer: [feature{id, ...}]} of several powiaty: `first` unchanged, `more` adds only new ids, sorted by id
    (the ADR 0208 rule of streetscape/sources.py: a feature on the boundary can be in both packages)."""
    out = {}
    for layer in sorted(set(first) | set(more)):
        a = first.get(layer, [])
        seen = {f["id"] for f in a}
        out[layer] = sorted(a + [f for f in more.get(layer, []) if f["id"] not in seen], key=lambda f: f["id"])
    return out


# ------------------------------------------------------------------------------------------------ data
@lru_cache(maxsize=4)
def load(path: Path = BOUNDARIES):
    """(aoi, {teryt: geometry}) from the committed PRG extract."""
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    geoms = {f["properties"]["teryt"]: shape(f["geometry"]) for f in d["features"]}
    for g in geoms.values():
        shapely.prepare(g)
    return tuple(d["aoi_epsg2180"]), geoms


def names(path: Path = BOUNDARIES) -> dict[str, str]:
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    return {f["properties"]["teryt"]: f["properties"]["name"] for f in d["features"]}


def parse_gml(xml: bytes) -> list[dict]:
    """PRG GML 3.2 (EPSG:2180 axis order = northing, easting) -> [{teryt, name, geometry (x = E, y = N)}]."""
    root = ET.fromstring(xml)
    out = []
    for f in root.iter(f"{MS}A02_Granice_powiatow"):
        polys = []
        for p in f.iter(f"{GML}Polygon"):
            rings = []
            for lr in p.iter(f"{GML}LinearRing"):
                v = [float(t) for t in lr.find(f"{GML}posList").text.split()]
                rings.append([(v[i + 1], v[i]) for i in range(0, len(v) - 1, 2)])
            polys.append(Polygon(rings[0], rings[1:]))
        out.append({"teryt": f.find(f"{MS}JPT_KOD_JE").text.strip(), "name": f.find(f"{MS}JPT_NAZWA_").text.strip(),
                    "geometry": shapely.union_all(polys)})
    return out


def fetch(aoi=DEFAULT_AOI) -> None:
    import requests
    x0, y0, x1, y1 = aoi
    params = {"SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetFeature", "TYPENAMES": LAYER,
              "SRSNAME": "EPSG:2180", "BBOX": f"{y0},{x0},{y1},{x1},urn:ogc:def:crs:EPSG::2180"}
    r = requests.get(WFS, params=params, headers={"User-Agent": USER_AGENT}, timeout=300)
    r.raise_for_status()
    time.sleep(1.0)
    feats = parse_gml(r.content)
    clip = box(*aoi)
    out = []
    for f in sorted(feats, key=lambda f: f["teryt"]):
        g = shapely.make_valid(f["geometry"]).intersection(clip).simplify(SIMPLIFY_M, preserve_topology=True)
        if g.is_empty:
            continue
        g = shapely.set_precision(g, 0.1)
        out.append({"type": "Feature", "properties": {"teryt": f["teryt"], "name": f["name"]},
                    "geometry": mapping(g)})
    BOUNDARIES.parent.mkdir(parents=True, exist_ok=True)
    doc = {"type": "FeatureCollection", "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::2180"}},
           "aoi_epsg2180": list(aoi), "simplify_m": SIMPLIFY_M, "source": "gugik-prg-powiaty", "features": out}
    BOUNDARIES.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8",
                          newline="\n")
    man = {
        "id": "gugik-prg-powiaty",
        "name": "GUGiK PRG — granice powiatów (WFS AdministrativeBoundaries, A02_Granice_powiatow)",
        "provider": "Główny Urząd Geodezji i Kartografii",
        "product": "PRG",
        "request": r.url,
        "crs": "EPSG:2180 (PL-1992); GML axis order northing, easting -> stored as x = E, y = N",
        "aoi_epsg2180": list(aoi),
        "processing": f"clip to AOI, simplify {SIMPLIFY_M} m (preserve topology), precision 0.1 m",
        "license": "GUGiK open data (PRG): free of charge, Pgik art. 40a ust. 2 pkt 1 — LEGAL_REVIEW_REQUIRED",
        "attribution": "Źródło danych: Główny Urząd Geodezji i Kartografii (www.geoportal.gov.pl)",
        "used_by": ["tools/worldgen/powiaty.py (far_field, lod2_extract, water — ADR 0219)"],
        "in_git": True,
        "response_sha256": hashlib.sha256(r.content).hexdigest(),
        "files": [{"local_path": str(BOUNDARIES.relative_to(REPO)).replace("\\", "/"),
                   "sha256": hashlib.sha256(BOUNDARIES.read_bytes()).hexdigest(),
                   "downloaded_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}],
        "powiaty": {f["properties"]["teryt"]: f["properties"]["name"] for f in out},
    }
    MANIFEST.write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    load.cache_clear()
    print(f"{len(out)} powiaty -> {BOUNDARIES.relative_to(REPO)} ({BOUNDARIES.stat().st_size} B)")


def report() -> list[dict]:
    sys.path.insert(0, str(REPO / "tools" / "worldgen"))
    import regions
    rows = []
    for rid, r in regions.REGIONS.items():
        tile = {k: round(v * 100, 2) for k, v in powiat_shares(r.bbox).items()}
        ring = {k: round(v * 100, 2) for k, v in powiat_shares(ring_bbox(r.origin)).items()}
        rows.append({"region": rid, "registry": list(r.powiaty), "tile_pct": tile, "ring_pct": ring})
        print(f"{rid:24s} registry {','.join(r.powiaty):10s} tile {tile}  ring {ring}")
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--aoi", type=float, nargs=4, default=DEFAULT_AOI)
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.fetch:
        fetch(tuple(a.aoi))
    if a.report or not a.fetch:
        report()


if __name__ == "__main__":
    main()
