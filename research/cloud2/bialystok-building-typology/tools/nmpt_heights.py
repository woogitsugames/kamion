#!/usr/bin/env python3
"""Wysokosci budynkow z GUGiK WCS: NMPT (DSM 0,5 m) - NMT (DTM), dla probki budynkow OSM.
Metoda (ESTIMATED): h_med = mediana(NMPT wewnatrz obrysu zwezonego o 1 m) - p10(NMT w pierscieniu 1..4 m wokol obrysu);
h_p95 = percentyl 95 NMPT wewnatrz obrysu - to samo odniesienie (kalenica / attyka / nadbudowki).
Probka: random.Random(20261114), warstwy wg tagu building OSM i obszaru. Porownanie z LoD1 2024 (buildings.geojson repo), gdy centroid trafia w obrys.
"""
import json, random, time, io, csv, pathlib, sys
import numpy as np, requests
from pyproj import Transformer
from shapely.geometry import Polygon, Point, shape
from shapely import contains_xy
ROOT = pathlib.Path(__file__).resolve().parent.parent
REPO = ROOT.parents[2]
T = Transformer.from_crs(4326, 2180, always_xy=True)
WCS = {"dsm": ("https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMPT/GRID1/WCS/DigitalSurfaceModel", "DSM_PL-EVRF2007-NH"),
       "dtm": ("https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/GRID1/WCS/DigitalTerrainModel", "DTM_PL-EVRF2007-NH")}
GROUPS = {"blok": {"apartments", "residential"}, "hala": {"industrial", "warehouse"},
          "dom": {"house", "detached", "semidetached_house", "terrace", "bungalow"},
          "biuro_uslugi": {"office", "retail", "commercial", "supermarket", "public", "school", "hospital", "university"}}
QUOTA = {("trasa_c", "blok"): 9, ("trasa_c", "hala"): 7, ("trasa_c", "dom"): 7, ("trasa_c", "biuro_uslugi"): 7,
         ("dojlidy", "blok"): 4, ("dojlidy", "hala"): 8, ("dojlidy", "dom"): 8, ("dojlidy", "biuro_uslugi"): 6}

def grid(kind, x0, y0, x1, y1):
    url, cov = WCS[kind]
    p = [("SERVICE", "WCS"), ("VERSION", "2.0.1"), ("REQUEST", "GetCoverage"), ("COVERAGEID", cov), ("FORMAT", "image/x-aaigrid"),
         ("SUBSET", f"x({x0},{x1})"), ("SUBSET", f"y({y0},{y1})"), ("SUBSETTINGCRS", "http://www.opengis.net/def/crs/EPSG/0/2180")]
    for i in range(5):
        try:
            r = requests.get(url, params=p, timeout=90)
            if r.status_code == 200 and b"ncols" in r.content: break
        except requests.RequestException: pass
        time.sleep(3 * 2**i)
    else: raise RuntimeError(f"WCS {kind} failed")
    body = r.content
    a = body.index(b"ncols"); txt = body[a:].split(b"\r\n--wcs")[0].split(b"\n--wcs")[0].decode("ascii", "ignore")
    lines = txt.strip().splitlines(); hdr = {}; k = 0
    while lines[k].split()[0].lower() in ("ncols", "nrows", "xllcorner", "yllcorner", "xllcenter", "yllcenter", "cellsize", "nodata_value", "dx", "dy"):
        a_, b_ = lines[k].split()[:2]; hdr[a_.lower()] = float(b_); k += 1
    arr = np.array(" ".join(lines[k:]).split(), dtype=float).reshape(int(hdr["nrows"]), int(hdr["ncols"]))
    arr[arr == hdr.get("nodata_value", -9999)] = np.nan
    cs = hdr.get("cellsize", hdr.get("dx"))
    xs = hdr.get("xllcorner", hdr.get("xllcenter", 0) - cs / 2) + (np.arange(arr.shape[1]) + 0.5) * cs
    ys = hdr.get("yllcorner", hdr.get("yllcenter", 0) - cs / 2) + (arr.shape[0] - np.arange(arr.shape[0]) - 0.5) * cs
    return arr, xs, ys

def main():
    rng = random.Random(20261114)
    lod = []
    for reg in ("bialystok-industrial-c", "bialystok-dojlidy"):
        for f in json.load(open(REPO / "Data/Regions" / reg / "buildings.geojson"))["features"]:
            lod.append((shape(f["geometry"]), f["properties"]))
    rows = []
    for area in ("trasa_c", "dojlidy"):
        els = [e for e in json.load(open(ROOT / "data" / f"overpass_{area}.json"))["elements"] if e["type"] == "way" and "geometry" in e]
        for g, tags in GROUPS.items():
            cand = sorted((e for e in els if e["tags"].get("building") in tags), key=lambda e: e["id"])
            for e in rng.sample(cand, min(QUOTA[(area, g)], len(cand))):
                poly = Polygon([T.transform(p["lon"], p["lat"]) for p in e["geometry"]])
                if not poly.is_valid or poly.area < 30: continue
                x0, y0, x1, y1 = poly.bounds; b = 6
                bb = (round(x0 - b), round(y0 - b), round(x1 + b), round(y1 + b))
                dsm, xs, ys = grid("dsm", *bb); dtm, xs2, ys2 = grid("dtm", *bb)
                X, Y = np.meshgrid(xs, ys); inner = poly.buffer(-1.0)
                if inner.is_empty: inner = poly
                m_in = contains_xy(inner, X, Y)
                X2, Y2 = np.meshgrid(xs2, ys2)
                ring = poly.buffer(4.0).difference(poly.buffer(1.0)); m_ring = contains_xy(ring, X2, Y2)
                if m_in.sum() < 20 or np.isfinite(dtm[m_ring]).sum() < 10: continue
                z0 = float(np.nanpercentile(dtm[m_ring], 10)); v = dsm[m_in]; v = v[np.isfinite(v)]
                c = poly.representative_point(); l1 = l2 = st = fn = rt = None
                for gpoly, pr in lod:
                    if gpoly.contains(c):
                        l1, l2, st, fn, rt = pr.get("height_lod1_2024_m"), pr.get("height_lod2_2017_m"), pr.get("storeys"), pr.get("function"), pr.get("roof_type_lod2"); break
                lon = sum(p["lon"] for p in e["geometry"][:-1]) / (len(e["geometry"]) - 1); lat = sum(p["lat"] for p in e["geometry"][:-1]) / (len(e["geometry"]) - 1)
                mr = poly.minimum_rotated_rectangle; cs = list(mr.exterior.coords)
                s1 = Point(cs[0]).distance(Point(cs[1])); s2 = Point(cs[1]).distance(Point(cs[2]))
                rows.append(dict(area=area, grupa=g, way=e["id"], building=e["tags"].get("building"), levels_osm=e["tags"].get("building:levels", ""),
                    addr=(e["tags"].get("addr:street", "") + " " + e["tags"].get("addr:housenumber", "")).strip(), name=e["tags"].get("name", ""),
                    lat=round(lat, 6), lon=round(lon, 6), area_m2=round(poly.area), dl_m=round(max(s1, s2), 1), szer_m=round(min(s1, s2), 1),
                    h_med=round(float(np.median(v)) - z0, 2), h_p95=round(float(np.percentile(v, 95)) - z0, 2), z_teren=round(z0, 2), n_px=int(m_in.sum()),
                    lod1_2024=l1 or "", lod2_2017=l2 or "", bdot_storeys=st or "", bdot_function=fn or "", roof_lod2=rt or ""))
                print(rows[-1], flush=True)
    with open(ROOT / "data" / "nmpt_sample.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(len(rows))
main()
