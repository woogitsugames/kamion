"""ADR 0339: canopy height model (CHM) of the forests of a region tile = GUGiK NMPT (digital surface model, airborne
laser scanning, read through the public WCS at 1 m) minus the NMT of the tile (heightmap of build_region.py, the same
vertical datum PL-EVRF2007-NH). The stands of streetscape.vegetation take their heights, gaps and young growth from
it instead of one class range per species (a wall of crowns of one height, critic s24 build 5 # 7).

    uv run --project tools/worldgen python tools/worldgen/streetscape/forest_chm.py --region dk65-04 [--refetch]

Product (in git, small, so the world build needs no network and is reproducible):
  Data/Regions/<id>/forest_chm.png    8-bit, 2 channels (PNG mode LA), CELL_M cells, row 0 = north edge:
                                      L = top of the crowns in the cell (max of the 1 m samples) / STEP_M
                                      A = share of the 1 m samples of the cell >= COVER_MIN_M above ground * 255
                                      both 0 outside the BDOT10k forest polygons + MASK_BUFFER_M
  Data/Regions/<id>/forest_chm.json   georeference, source, date of the request, sha256 of the PNG, statistics
Raw surface model (not in git): Data/raw/gugik/gugik-nmpt-wcs-<id>/dsm_1m.npz (the parsed WCS replies).

The service does not state the survey date of a cell: UNVERIFIED (as in ADR 0242; the sheet index lists NMPT of
2019-2025 for Podlasie). Accuracy of a crown top: laser returns miss the leading shoot, a surface model reads
conifer tops ~0.5-1.5 m low (WORKING_VALUE, not corrected here). Licence: open data of GUGiK (Pgik art. 40a),
attribution in docs/LICENSES.md. No other source (no Google, ADR 0002).
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import io
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
SCHEMA = "truck-sim-pl/forest-chm/1"
WCS = ("https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMPT/GRID1/WCS/DigitalSurfaceModel?SERVICE=WCS&VERSION=2.0.1"
       "&REQUEST=GetCoverage&COVERAGEID=DSM_PL-EVRF2007-NH&FORMAT=image/x-aaigrid")
UA = "osm-research-client/1.0"
SRC_M = 0.5             # native cell of the coverage
FETCH_M = 1.0           # requested cell (SCALEFACTOR = SRC_M / FETCH_M)
FETCH_BLOCK_M = 1024.0  # one request (1024 x 1024 cells, ~21 MB of text)
CELL_M = 4.0            # product cell
STEP_M = 0.25           # height quantum of the product (255 -> 63.75 m)
COVER_MIN_M = 5.0       # a 1 m sample this high above ground counts as tree cover
MASK_BUFFER_M = 40.0
H_MAX_M = 60.0          # above this a sample is no tree (mast, crane, bird): dropped


def parse_aaigrid(raw: bytes):
    """(header dict, array rows north -> south) of an Arc/Info ASCII grid, also inside a multipart WCS reply."""
    if b"ncols" not in raw:
        raise ValueError("no grid in the WCS reply: " + raw[:300].decode("utf-8", "replace"))
    txt = raw[raw.index(b"ncols"):]
    end = txt.find(b"\n--")
    lines = (txt[:end] if end > 0 else txt).split(b"\n")
    hdr, k = {}, 0
    while lines[k].split() and re.match(rb"[A-Za-z_]+$", lines[k].split()[0]):
        hdr[lines[k].split()[0].decode().lower()] = float(lines[k].split()[1])
        k += 1
    body = b"\n".join(lines[k:k + int(hdr["nrows"])])
    return hdr, np.loadtxt(io.BytesIO(body), dtype=np.float32, ndmin=2)


def fetch_dsm(bbox, log=print, tries=6):
    """1 m surface model of bbox (xmin, ymin, xmax, ymax; EPSG:2180), rows north -> south, cell centres at
    xmin + 0.5 + i. Returns (z float32 with NaN where the service has no data, [sha256 of every reply])."""
    x0, y0, x1, y1 = (float(v) for v in bbox)
    W, H = int(round((x1 - x0) / FETCH_M)), int(round((y1 - y0) / FETCH_M))
    z = np.full((H, W), np.nan, np.float32)
    shas = []
    xs = np.arange(x0, x1, FETCH_BLOCK_M)
    ys = np.arange(y0, y1, FETCH_BLOCK_M)
    for bx in xs:
        for by in ys:
            ex, ey = min(bx + FETCH_BLOCK_M, x1), min(by + FETCH_BLOCK_M, y1)
            url = f"{WCS}&SUBSET=x({bx},{ex})&SUBSET=y({by},{ey})&SCALEFACTOR={SRC_M / FETCH_M}"
            for k in range(tries):
                try:
                    raw = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=300).read()
                    hdr, g = parse_aaigrid(raw)
                    break
                except Exception as ex_:      # noqa: BLE001 - network / service hiccup: retry, then fail loudly
                    if k == tries - 1:
                        raise
                    log(f"  retry {k + 1}: {type(ex_).__name__}")
                    time.sleep(10 * (k + 1))
            nod = hdr.get("nodata_value")
            if nod is not None:
                g = np.where(g == np.float32(nod), np.nan, g)
            if abs(hdr["cellsize"] - FETCH_M) > 1e-6 or abs(hdr["xllcorner"] - bx) > 1e-3 or abs(hdr["yllcorner"] - by) > 1e-3:
                raise ValueError(f"unexpected grid of the WCS reply: {hdr}")
            i0 = int(round((bx - x0) / FETCH_M))
            j0 = int(round((y1 - ey) / FETCH_M))          # row 0 = north
            z[j0:j0 + g.shape[0], i0:i0 + g.shape[1]] = g
            shas.append(hashlib.sha256(raw).hexdigest())
            log(f"  dsm block x {bx:.0f} y {by:.0f}: {g.shape[1]} x {g.shape[0]}, {len(raw) / 1e6:.1f} MB")
    return z, shas


def reduce_chm(dsm, ground_nodes):
    """dsm: [H, W] 1 m cells (centres between the NMT nodes); ground_nodes: [H + 1, W + 1] NMT nodes, both row 0 =
    north. Returns (top [H/k, W/k] m, cover [H/k, W/k] 0..1), k = CELL_M / FETCH_M."""
    g = ground_nodes
    ground = 0.25 * (g[:-1, :-1] + g[:-1, 1:] + g[1:, :-1] + g[1:, 1:])
    chm = dsm.astype(np.float64) - ground
    chm[~np.isfinite(chm)] = 0.0
    chm[chm > H_MAX_M] = 0.0
    chm = np.clip(chm, 0.0, None)
    k = int(round(CELL_M / FETCH_M))
    H, W = chm.shape[0] // k, chm.shape[1] // k
    blocks = chm[:H * k, :W * k].reshape(H, k, W, k)
    return blocks.max(axis=(1, 3)), (blocks >= COVER_MIN_M).mean(axis=(1, 3))


def forest_mask(region_id, bbox, shape):
    """Cells within MASK_BUFFER_M of a BDOT10k forest polygon (streetscape_sources.json) or of an authored
    `tree_stand`; None when the region has no source file (then nothing is masked)."""
    import shapely
    f = REPO / "Data" / "Regions" / region_id / "generated" / "streetscape_sources.json"
    if not f.exists():
        return None
    src = json.loads(f.read_text(encoding="utf-8"))
    polys = []
    for ft in src["bdot10k"].get("OT_PTLZ_A", []):
        co = ft["geometry"]["coordinates"]
        for rings in (co if ft["geometry"]["type"] == "MultiPolygon" else [co]):
            p = shapely.Polygon(rings[0], rings[1:])
            polys.append(p if p.is_valid else shapely.make_valid(p))
    if not polys:
        return np.zeros(shape, bool)
    u = shapely.union_all(polys).buffer(MASK_BUFFER_M)
    shapely.prepare(u)
    x0, _, _, y1 = bbox
    xs = x0 + (np.arange(shape[1]) + 0.5) * CELL_M
    ys = y1 - (np.arange(shape[0]) + 0.5) * CELL_M
    xx, yy = np.meshgrid(xs, ys)
    return shapely.contains_xy(u, xx, yy)


def build(region_id, refetch=False, log=print):
    import yaml
    from PIL import Image
    sys.path.insert(0, str(REPO / "tools" / "worldgen"))
    from roads.profile import load_heightfield
    rdir = REPO / "Data" / "Regions" / region_id
    reg = yaml.safe_load((rdir / "region.yaml").read_text(encoding="utf-8"))
    bb = reg["bbox"]
    bbox = (float(bb["xmin"]), float(bb["ymin"]), float(bb["xmax"]), float(bb["ymax"]))
    tm = json.loads((rdir / "terrain.json").read_text(encoding="utf-8"))
    hf = load_heightfield(tm, REPO, (float(reg["origin"]["x"]), float(reg["origin"]["y"])))
    raw_dir = REPO / "Data" / "raw" / "gugik" / f"gugik-nmpt-wcs-{region_id}"
    cache = raw_dir / "dsm_1m.npz"
    if cache.exists() and not refetch:
        d = np.load(cache)
        dsm, shas, fetched = d["dsm"], [str(s) for s in d["sha256"]], str(d["fetched"])
        log(f"{region_id}: surface model from {cache.relative_to(REPO).as_posix()}")
    else:
        log(f"{region_id}: fetching the surface model (GUGiK WCS, {FETCH_M} m)")
        dsm, shas = fetch_dsm(bbox, log)
        fetched = datetime.date.today().isoformat()
        raw_dir.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(cache, dsm=dsm, sha256=np.array(shas), fetched=np.array(fetched), bbox=np.array(bbox))
    if hf.z.shape != (dsm.shape[0] + 1, dsm.shape[1] + 1):
        raise ValueError(f"NMT nodes {hf.z.shape} do not frame the surface model {dsm.shape}")
    missing = float(np.mean(~np.isfinite(dsm)))
    top, cover = reduce_chm(dsm, hf.z)
    mask = forest_mask(region_id, bbox, top.shape)
    if mask is not None:
        top = np.where(mask, top, 0.0)
        cover = np.where(mask, cover, 0.0)
    L = np.clip(np.rint(top / STEP_M), 0, 255).astype(np.uint8)
    A = np.clip(np.rint(cover * 255.0), 0, 255).astype(np.uint8)
    png = rdir / "forest_chm.png"
    Image.fromarray(np.dstack([L, A]), "LA").save(png, optimize=True)
    inside = L[mask] * STEP_M if mask is not None and mask.any() else L.ravel() * STEP_M
    grown = inside[inside >= COVER_MIN_M]
    q = (lambda p: round(float(np.percentile(grown, p)), 1)) if len(grown) else (lambda p: None)
    doc = {
        "schema": SCHEMA, "adr": "0339", "region": region_id, "bbox": list(bbox), "crs": "EPSG:2180",
        "vertical": "height above the NMT of the tile, both PL-EVRF2007-NH",
        "cell_m": CELL_M, "step_m": STEP_M, "cover_min_m": COVER_MIN_M, "size": [int(L.shape[1]), int(L.shape[0])],
        "layout": "row 0 = north edge; cell (j, i) covers x = xmin + i * cell_m .., y = ymax - j * cell_m ..",
        "channels": {"L": "top of the crowns [step_m]", "A": "share of 1 m samples >= cover_min_m [1/255]"},
        "mask": f"BDOT10k OT_PTLZ_A + {MASK_BUFFER_M:.0f} m" if mask is not None else "none",
        "source": {"provider": "Główny Urząd Geodezji i Kartografii", "product": "NMPT (DSM) 0.5 m, WCS",
                   "service": WCS, "request_cell_m": FETCH_M, "fetched": fetched, "survey_date": "UNVERIFIED",
                   "reply_sha256": shas, "missing_share": round(missing, 5),
                   "ground": tm.get("source_manifest"), "ground_sha256_r16": tm.get("sha256_r16"),
                   "license": "GUGiK open data (Pgik art. 40a ust. 2 pkt 1)",
                   "attribution": "Źródło danych: Główny Urząd Geodezji i Kartografii (www.geoportal.gov.pl)"},
        "stats": {"forest_cells": int(mask.sum()) if mask is not None else int(L.size),
                  "cells_ge_cover_min": int(len(grown)),
                  "top_m": {"p10": q(10), "p50": q(50), "p90": q(90), "p99": q(99)}},
        "sha256_png": hashlib.sha256(png.read_bytes()).hexdigest(),
    }
    (rdir / "forest_chm.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8",
                                          newline="\n")
    log(f"{region_id}: {png.relative_to(REPO).as_posix()} {png.stat().st_size / 1024:.0f} kB, {doc['stats']}")
    return doc


class Chm:
    """Sampler of the product in region-local metres (E, N). `top` / `cover`: [rows, cols], row 0 = north."""

    def __init__(self, top, cover, x0, y1, cell_m=CELL_M, meta=None):
        self.top = np.asarray(top, np.float64)
        self.cover = np.asarray(cover, np.float64)
        self.x0, self.y1, self.cell = float(x0), float(y1), float(cell_m)
        self.meta = meta or {}
        from scipy import ndimage
        # dominant height: the tallest crown top within one cell either side (a 12 m window; M68 measured stand
        # heights as "h30_max", the maximum in 30 m - a single cell also holds crown flanks and gaps)
        self.dom = ndimage.maximum_filter(self.top, size=3, mode="nearest")
        self.cov3 = ndimage.uniform_filter(self.cover, size=3, mode="nearest")
        # stand height: what the neighbourhood of ~28 m has reached (90th percentile of the cell tops)
        self.stand = ndimage.percentile_filter(self.top, 90, size=7, mode="nearest")

    def _ij(self, P):
        P = np.asarray(P, float).reshape(-1, 2)
        i = np.floor((P[:, 0] - self.x0) / self.cell).astype(int)
        j = np.floor((self.y1 - P[:, 1]) / self.cell).astype(int)
        inside = (i >= 0) & (j >= 0) & (i < self.top.shape[1]) & (j < self.top.shape[0])
        return np.clip(j, 0, self.top.shape[0] - 1), np.clip(i, 0, self.top.shape[1] - 1), inside

    def sample(self, P):
        """(dominant height, stand height, cover, inside the grid) at points P [k, 2]."""
        j, i, inside = self._ij(P)
        return self.dom[j, i], self.stand[j, i], self.cov3[j, i], inside

    def gaps(self, poly, min_h, min_area):
        """Openings of a stand: parts of `poly` (region-local shapely geometry) where no crown reaches min_h within
        one cell either side, each at least min_area. Cell-aligned polygons, None when there is none."""
        import shapely
        from scipy import ndimage
        x0, y0, x1, y1 = poly.bounds
        i0, i1 = int(np.floor((x0 - self.x0) / self.cell)), int(np.ceil((x1 - self.x0) / self.cell))
        j0, j1 = int(np.floor((self.y1 - y1) / self.cell)), int(np.ceil((self.y1 - y0) / self.cell))
        i0, j0 = max(i0, 0), max(j0, 0)
        i1, j1 = min(i1, self.top.shape[1]), min(j1, self.top.shape[0])
        if i1 <= i0 or j1 <= j0:
            return None
        low = self.dom[j0:j1, i0:i1] < min_h
        if not low.any():
            return None
        lab, n = ndimage.label(low)
        need = int(np.ceil(min_area / (self.cell * self.cell)))
        boxes = []
        for k, sl in enumerate(ndimage.find_objects(lab), start=1):
            part = lab[sl] == k
            if int(part.sum()) < need:
                continue
            for dj, di in zip(*np.nonzero(part)):
                e = self.x0 + (i0 + sl[1].start + di) * self.cell
                n_ = self.y1 - (j0 + sl[0].start + dj) * self.cell
                boxes.append(shapely.box(e, n_ - self.cell, e + self.cell, n_))
        if not boxes:
            return None
        g = shapely.intersection(shapely.union_all(boxes), poly)
        return None if g.is_empty else g


def load(region_id, origin, root=None):
    """Chm of a region in region-local metres, or None when the region has no forest_chm.png (class defaults)."""
    rdir = (root or REPO) / "Data" / "Regions" / str(region_id)
    png, meta_p = rdir / "forest_chm.png", rdir / "forest_chm.json"
    if not png.exists() or not meta_p.exists():
        return None
    from PIL import Image
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    if meta.get("schema") != SCHEMA:
        raise ValueError(f"{meta_p}: schema {meta.get('schema')} != {SCHEMA}")
    if hashlib.sha256(png.read_bytes()).hexdigest() != meta["sha256_png"]:
        raise ValueError(f"{png}: sha256 differs from forest_chm.json (rebuild with forest_chm.py)")
    a = np.asarray(Image.open(png).convert("LA"), np.float64)
    bbox = meta["bbox"]
    return Chm(a[..., 0] * meta["step_m"], a[..., 1] / 255.0, bbox[0] - float(origin[0]), bbox[3] - float(origin[1]),
               meta["cell_m"], meta)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True, nargs="+")
    ap.add_argument("--refetch", action="store_true", help="ignore Data/raw/gugik/gugik-nmpt-wcs-<id>/dsm_1m.npz")
    a = ap.parse_args()
    for rid in a.region:
        build(rid, a.refetch)
    return 0


if __name__ == "__main__":
    sys.exit(main())
