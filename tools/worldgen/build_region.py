"""Build first derived products for a region tile (Stage 4 groundwork).

Usage (from repo root, after ingest.py):
    uv run --project tools/worldgen tools/worldgen/build_region.py --region bialystok-industrial-c

Outputs (committed, small)            Data/Regions/<id>/
    region.yaml           id, bbox, CRS, floating-origin anchor, sources (+ manifest sha256)
    roads.graph.json      OSM road graph clipped to the tile, per-field provenance/confidence
    buildings.geojson     footprints (BDOT10k + OSM-only) with height + height_source per building
    terrain.json          heightmap metadata (+ sha256 of the raw heightmap)
    ortho.json            clipped orthophoto metadata (+ sha256)
    build_manifest.json   sha256 of every output (idempotence check)
Outputs (NOT committed, big)          Data/raw/derived/<id>/
    heightmap_<n>.r16     uint16 little-endian, n x n, row 0 = north; z = offset + v * scale
    heightmap_<n>.png     same, 16-bit greyscale PNG
    ortho_0p25m.tif       RGB GeoTIFF EPSG:2180, 0.25 m, JPEG-in-TIFF (reference only, never a game texture)

Deterministic: same inputs -> byte-identical outputs (tests/gis/test_build_idempotence.py).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pyogrio
import shapely
import yaml
from PIL import Image

import buildings as bld
import osm_extract
import regions
import roadgraph
import terrain
from sources import MANIFEST_DIR, RAW_ROOT, REPO_ROOT, load_manifest, sha256_of, write_if_changed

REGIONS_DIR = REPO_ROOT / "Data" / "Regions"
DERIVED = RAW_ROOT / "derived"


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def write_json(path: Path, obj, compact=False) -> str:
    text = (json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True, allow_nan=False) if compact
            else json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True, allow_nan=False)) + "\n"
    write_if_changed(path, text)
    return sha_bytes(text.encode("utf-8"))


def manifest_files(ds_id: str) -> list[Path]:
    m = load_manifest(ds_id)
    if not m:
        raise SystemExit(f"missing manifest {ds_id}; run ingest.py first")
    return [REPO_ROOT / f["local_path"] for f in m["files"]]


def find_manifest(prefix: str, suffix: str = "") -> str:
    ids = sorted(p.stem for p in MANIFEST_DIR.glob(f"{prefix}*{suffix}.json"))
    if not ids:
        raise SystemExit(f"no manifest matching {prefix}*{suffix}; run ingest.py first")
    return ids[-1]  # latest year sorts last


def extract_from_zip(zpath: Path, member_substr: str, out_dir: Path) -> Path:
    import zipfile
    with zipfile.ZipFile(zpath) as zf:
        name = next(n for n in zf.namelist() if member_substr in n)
        dest = out_dir / Path(name).name
        if not dest.exists():
            out_dir.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(zf.read(name))
    return dest


# ---------------------------------------------------------------------------------------------
def build_terrain(region, out_dir: Path, raw_dir: Path, nmt_id: str) -> tuple[dict, np.ndarray]:
    sheets = manifest_files(nmt_id)
    z = terrain.mosaic_nodes(sheets, region.bbox)
    missing = int(np.isnan(z).sum())
    q, enc = terrain.encode_u16(z)
    n = z.shape[0]
    raw_dir.mkdir(parents=True, exist_ok=True)
    r16 = raw_dir / f"heightmap_{n}.r16"
    data = q.tobytes()
    if not r16.exists() or r16.read_bytes() != data:
        r16.write_bytes(data)
    png = raw_dir / f"heightmap_{n}.png"
    if not png.exists() or r16.stat().st_mtime > png.stat().st_mtime:
        Image.fromarray(q.astype(np.uint16)).save(png)  # PNG mode I;16 written by Pillow
    meta = {
        "source_manifest": nmt_id, "source_crs": "EPSG:2180", "height_datum": "PL-EVRF2007-NH (EPSG:9651)",
        "bbox": list(region.bbox), "samples": [z.shape[1], z.shape[0]], "spacing_m": 1.0,
        "sampling": "exact: tile nodes coincide with NMT cell centres (xllcenter at integer metres); no interpolation",
        "node_ij_to_xy": "x = bbox.xmin + i, y = bbox.ymax - j  (row 0 = north edge)",
        "encoding": {"file": f"Data/raw/derived/{region.id}/{r16.name}", "dtype": "uint16 little-endian",
                     **enc, "decode": "z_m = offset_m + value * scale_m_per_unit"},
        "unity_hint": "Unity Terrain RAW import: 16-bit, Windows byte order, flip vertically (Unity row 0 = south); "
                      "terrain size x/z = bbox width/height, y = span_m, position y = offset_m - origin_z",
        "stats_m": {"min": round(float(np.nanmin(z)), 3), "max": round(float(np.nanmax(z)), 3),
                    "mean": round(float(np.nanmean(z)), 3)},
        "missing_samples": missing,
        "sha256_r16": sha_bytes(data),
    }
    return meta, z


def build_ortho(region, raw_dir: Path, orto_id: str) -> dict:
    import rasterio
    from rasterio.merge import merge
    files = manifest_files(orto_id)
    out = raw_dir / "ortho_0p25m.tif"
    stamp = raw_dir / "ortho_0p25m.src"   # rebuild when the source manifest changes
    src_sha = sha256_of(MANIFEST_DIR / f"{orto_id}.json")
    if out.exists() and (not stamp.exists() or stamp.read_text() != src_sha):
        out.unlink()
    srcs = [rasterio.open(p) for p in sorted(files)]
    crs = {str(s.crs) for s in srcs}
    res = {s.res for s in srcs}
    try:
        if not out.exists():
            mosaic, transform = merge(srcs, bounds=region.bbox, res=0.25, nodata=0)
            prof = {"driver": "GTiff", "height": mosaic.shape[1], "width": mosaic.shape[2], "count": 3,
                    "dtype": mosaic.dtype, "crs": srcs[0].crs, "transform": transform, "tiled": True,
                    "blockxsize": 512, "blockysize": 512, "compress": "JPEG", "photometric": "YCBCR",
                    "jpeg_quality": 90}
            with rasterio.open(out, "w", **prof) as dst:
                dst.write(mosaic[:3])
            stamp.write_text(src_sha)
        with rasterio.open(out) as o:
            shape, bounds = (o.width, o.height), list(o.bounds)
    finally:
        for s in srcs:
            s.close()
    return {"source_manifest": orto_id, "source_crs": sorted(crs), "source_res_m": sorted(res),
            "file": f"Data/raw/derived/{region.id}/{out.name}", "size_px": list(shape), "bounds": bounds,
            "res_m": 0.25, "sha256": sha256_of(out), "in_git": False,
            "use": "visual reference + alignment QA only (docs/05 §3); never a game texture"}


def buildings_geojson(feats: list[dict]) -> dict:
    def ring(c):
        return [[round(x, 2), round(y, 2)] for x, y in c]

    out = []
    for f in sorted(feats, key=lambda f: f["id"]):
        g = f["geometry"]
        polys = list(g.geoms) if g.geom_type == "MultiPolygon" else [g]
        coords = [[ring(p.exterior.coords)] + [ring(i.coords) for i in p.interiors] for p in polys]
        props = {k: v for k, v in f.items() if k != "geometry"}
        props["area_m2"] = round(g.area, 1)
        out.append({"type": "Feature", "id": f["id"], "properties": props,
                    "geometry": {"type": "MultiPolygon", "coordinates": coords}})
    return {"type": "FeatureCollection", "name": "buildings",
            "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::2180"}}, "features": out}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--region", required=True)
    ap.add_argument("--skip-ortho", action="store_true")
    a = ap.parse_args()
    region = regions.get(a.region)
    out_dir = REGIONS_DIR / region.id
    raw_dir = DERIVED / region.id
    out_dir.mkdir(parents=True, exist_ok=True)
    t = region.teryt_powiat
    tile = shapely.box(*region.bbox)
    hashes: dict[str, str] = {}

    nmt_id = find_manifest("gugik-nmt-", f"-{region.id}")
    orto_id = find_manifest("gugik-orto-", f"-{region.id}")
    src_ids = ["osm-geofabrik-podlaskie", nmt_id, orto_id, f"gugik-bdot10k-{t}", f"gugik-lod1-2024-{t}",
               f"gugik-lod2-2017-{t}"]

    # --- terrain
    print("[build] terrain")
    tmeta, z = build_terrain(region, out_dir, raw_dir, nmt_id)
    hashes["terrain.json"] = write_json(out_dir / "terrain.json", tmeta)

    # --- OSM layers
    print("[build] OSM layers")
    layers = osm_extract.load_layers()

    # --- BDOT10k
    bdot_zip = manifest_files(f"gugik-bdot10k-{t}")[0]
    gpkg_dir = RAW_ROOT / "gugik" / f"bdot10k-{t}" / "gpkg"
    bdot_cols = ["LOKALNYID", "KLASADROGI", "MATERIALNAWIERZCHNI", "SZEROKOSCNAWIERZCHNI", "LICZBAJEZDNIDROGI"]
    bdot_roads = []
    for L in ("OT_SKJZ_L", "OT_SKDR_L"):
        p = extract_from_zip(bdot_zip, f"__{L}.gpkg", gpkg_dir)
        df = pyogrio.read_dataframe(p, columns=bdot_cols, bbox=tuple(tile.buffer(50).bounds))
        df["layer"] = L
        bdot_roads.append(df)
    import pandas as pd
    bdot_roads = pd.concat(bdot_roads, ignore_index=True).sort_values(["layer", "LOKALNYID"]).reset_index(drop=True)

    # --- road graph
    print("[build] road graph")
    graph = roadgraph.build(layers["roads"], layers["points"], region.bbox, bdot_roads=bdot_roads)
    for n in graph["nodes"]:
        zz = terrain.sample(z, region.bbox, n["x"], n["y"])
        n["z_terrain"] = None if np.isnan(zz) else round(zz, 2)
    graph["sources"] = {"osm": "osm-geofabrik-podlaskie", "width_fallback": f"gugik-bdot10k-{t}",
                        "z_terrain": nmt_id}
    graph["notes"] = ["z_terrain is NMT ground height at the node; on bridges/overpasses it is the ground "
                      "BELOW the deck, not the road surface (see edge attrs bridge/layer).",
                      "Database derived from OSM: ODbL 1.0, © OpenStreetMap contributors (docs/LICENSES.md)."]
    hashes["roads.graph.json"] = write_json(out_dir / "roads.graph.json", graph, compact=True)

    # --- buildings
    print("[build] buildings")
    bubd = pyogrio.read_dataframe(extract_from_zip(bdot_zip, "__OT_BUBD_A.gpkg", gpkg_dir),
                                  bbox=tuple(region.bbox))
    cache = DERIVED / "cache"
    l1m, l2m = load_manifest(f"gugik-lod1-2024-{t}"), load_manifest(f"gugik-lod2-2017-{t}")
    lod1 = bld.cached_citygml(REPO_ROOT / l1m["files"][0]["local_path"], region.bbox, 1, cache, l1m["files"][0]["sha256"])
    lod2 = bld.cached_citygml(REPO_ROOT / l2m["files"][0]["local_path"], region.bbox, 2, cache, l2m["files"][0]["sha256"])
    feats = bld.merge(bubd, lod1, lod2, layers["buildings"], region.bbox)
    gj = buildings_geojson(feats)
    gj["sources"] = {"footprints": f"gugik-bdot10k-{t}", "heights": [f"gugik-lod1-2024-{t}", f"gugik-lod2-2017-{t}"],
                     "osm_only": "osm-geofabrik-podlaskie",
                     "citygml_srs": {"lod1": sorted({s for r in lod1.values() for s in r.get("srs", [])}),
                                     "lod2": sorted({s for r in lod2.values() for s in r.get("srs", [])})}}
    hashes["buildings.geojson"] = write_json(out_dir / "buildings.geojson", gj, compact=True)

    # --- ortho
    if not a.skip_ortho:
        print("[build] ortho")
        ometa = build_ortho(region, raw_dir, orto_id)
        hashes["ortho.json"] = write_json(out_dir / "ortho.json", ometa)

    # --- region.yaml
    srcs = []
    for sid in src_ids:
        m = load_manifest(sid)
        srcs.append({"id": sid, "license": m.get("license"), "attribution": m.get("attribution"),
                     "manifest": f"Data/SourceManifests/{sid}.json",
                     "manifest_sha256": sha256_of(MANIFEST_DIR / f"{sid}.json")})
    ry = {
        "id": region.id, "title": region.title, "status": region.status, "candidate": region.candidate,
        "crs": {"horizontal": "EPSG:2180 (ETRF2000-PL / CS92)", "vertical": "PL-EVRF2007-NH (EPSG:9651)",
                "axes_unity": "X = east (EPSG:2180 x), Y = up, Z = north (EPSG:2180 y)  [ADR 0003]"},
        "bbox": {"xmin": region.bbox[0], "ymin": region.bbox[1], "xmax": region.bbox[2], "ymax": region.bbox[3],
                 "width_m": region.width, "height_m": region.height},
        "origin": {"x": region.origin[0], "y": region.origin[1],
                   "z": round(terrain.sample(z, region.bbox, *region.origin), 2),
                   "note": "floating-origin anchor: Unity (0,0,0) = this point; z = NMT height at the point (EVRF2007)"},
        "teryt_powiat": t,
        "products": {k: f"Data/Regions/{region.id}/{k}" for k in sorted(hashes)},
        "big_products_not_in_git": [tmeta["encoding"]["file"], f"Data/raw/derived/{region.id}/ortho_0p25m.tif"],
        "sources": srcs,
        "rebuild": [f"uv run --project tools/worldgen tools/worldgen/ingest.py --region {region.id}",
                    f"uv run --project tools/worldgen tools/worldgen/build_region.py --region {region.id}"],
    }
    text = yaml.safe_dump(ry, allow_unicode=True, sort_keys=False, width=120)
    write_if_changed(out_dir / "region.yaml", text)
    hashes["region.yaml"] = sha_bytes(text.encode("utf-8"))
    hashes["heightmap.r16 (not in git)"] = tmeta["sha256_r16"]
    write_json(out_dir / "build_manifest.json", {"region": region.id, "sha256": hashes})
    print(f"[build] done: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges, {len(feats)} buildings")
    for k, v in sorted(hashes.items()):
        print(f"  {v[:16]}  {k}")


if __name__ == "__main__":
    main()
