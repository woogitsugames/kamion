r"""Referencje posesji jednorodzinnych (ADR 0114): wybiera z Mapillary klatki z widokiem z ulicy na domy jednorodzinne
regionu (BDOT10k `budynek jednorodzinny` z buildings.geojson), jedno zapytanie bbox (cache), pobiera <= --max klatek.
Wyniki: Data/raw/mapillary/posesje/<id>.jpg + manifest.jsonl (poza gitem). Token czyta mapillary_fetch (nigdy go nie wypisuje).

  uv run --project tools/refs python tools/refs/posesje_fetch.py --region bialystok-industrial-c --max 60
"""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mapillary_fetch as mf  # noqa: E402

REPO = mf.REPO


def house_centroids(region):
    d = json.loads((REPO / "Data/Regions" / region / "buildings.geojson").read_text(encoding="utf-8"))
    out = []
    for f in d["features"]:
        if f["properties"].get("function") == "budynek jednorodzinny":
            ring = f["geometry"]["coordinates"][0][0]
            out.append((sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="bialystok-industrial-c")
    ap.add_argument("--max", type=int, default=60)
    ap.add_argument("--dmin", type=float, default=8.0)
    ap.add_argument("--dmax", type=float, default=40.0)
    ap.add_argument("--dev", type=float, default=50.0)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--osm-cells", nargs="*", metavar="LAT,LON", help="komorki 0,01 deg z domami OSM (Data/raw/mapillary/posesje/osm_houses.json: building=house|detached|semidetached_house z podlaskie-*.osm.pbf, plik lokalny) zamiast BDOT regionu")
    ap.add_argument("--per-cell", type=int, default=10)
    ap.add_argument("--spacing", type=float, default=25.0)
    a = ap.parse_args()
    from pyproj import Transformer
    to_ll = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
    to_pl = Transformer.from_crs("EPSG:4326", "EPSG:2180", always_xy=True)
    if a.osm_cells:
        return run_osm(a, mf, to_pl)
    houses = house_centroids(a.region)
    xs, ys = [h[0] for h in houses], [h[1] for h in houses]
    # robust cluster box (5-95 percentile) +60 m
    xs.sort(); ys.sort()
    q = lambda v, p: v[int(p * (len(v) - 1))]
    x0, x1, y0, y1 = q(xs, .03) - 60, q(xs, .97) + 60, q(ys, .03) - 60, q(ys, .97) + 60
    lo = to_ll.transform(x0, y0); hi = to_ll.transform(x1, y1)
    bbox = (lo[0], lo[1], hi[0], hi[1])
    print("bbox 2180", [round(v) for v in (x0, y0, x1, y1)], "houses", len(houses))
    outdir = REPO / "Data/raw/mapillary/posesje"
    token = mf.resolve_token()
    if not token:
        raise SystemExit(mf.TOKEN_HELP)
    client = mf.MapillaryClient(token, cache_dir=outdir / ".cache")
    recs = []
    for tb in mf.tile_bbox(bbox):
        recs += client.images_in_bbox(tb)
    seen = {}
    for r in recs:
        seen[str(r["id"])] = r
    print("records", len(seen))
    cand = []
    for r in seen.values():
        if r.get("is_pano") or not r.get("thumb_2048_url"):
            continue
        ll = mf.record_lonlat(r); ca = r.get("compass_angle")
        if ll is None or ca is None:
            continue
        px, py = to_pl.transform(*ll)
        score = 0
        for hx, hy in houses:
            dx, dy = hx - px, hy - py
            d = math.hypot(dx, dy)
            if not a.dmin <= d <= a.dmax:
                continue
            az = math.degrees(math.atan2(dx, dy)) % 360
            if mf.angle_diff(az, float(ca)) <= a.dev / 2:
                score += 1
        if score:
            cand.append((score, str(r["id"]), px, py, r))
    print("candidates", len(cand))
    # greedy spatial diversity: >= 25 m apart, higher score first
    cand.sort(key=lambda t: (-t[0], t[1]))
    chosen = []
    for s, i, px, py, r in cand:
        if all(math.hypot(px - c[2], py - c[3]) >= 25 for c in chosen):
            chosen.append((s, i, px, py, r))
        if len(chosen) >= a.max:
            break
    print("chosen", len(chosen))
    if a.dry:
        return
    man_path = outdir / "manifest.jsonl"
    man = mf.load_manifest(man_path)
    for s, i, px, py, r in chosen:
        if i in man:
            continue
        sha = client.download(r["thumb_2048_url"], outdir / f"{i}.jpg")
        e = mf.make_entry(r, sha, [])
        e["houses_in_view"] = s
        e["x2180"], e["y2180"] = round(px, 1), round(py, 1)
        e["purpose"] = "posesje-r7 (ADR 0114): referencja plotow/bram/podjazdow; tylko referencja"
        man[i] = e
        mf.write_manifest(man_path, man)
    print("manifest", len(man))


def score_records(recs, houses, a, to_pl):
    cand = []
    for r in recs:
        if r.get("is_pano") or not r.get("thumb_2048_url"):
            continue
        ll = mf.record_lonlat(r); ca = r.get("compass_angle")
        if ll is None or ca is None:
            continue
        px, py = to_pl.transform(*ll)
        score = 0
        for hx, hy in houses:
            dx, dy = hx - px, hy - py
            d = math.hypot(dx, dy)
            if a.dmin <= d <= a.dmax and mf.angle_diff(math.degrees(math.atan2(dx, dy)) % 360, float(ca)) <= a.dev / 2:
                score += 1
        if score:
            cand.append((score, str(r["id"]), px, py, r))
    cand.sort(key=lambda t: (-t[0], t[1]))
    return cand


def run_osm(a, mf, to_pl):
    outdir = REPO / "Data/raw/mapillary/posesje"
    houses = [(h[0], h[1]) for h in json.loads((outdir / "osm_houses.json").read_text())]
    token = mf.resolve_token()
    if not token:
        raise SystemExit(mf.TOKEN_HELP)
    client = mf.MapillaryClient(token, cache_dir=outdir / ".cache")
    man_path = outdir / "manifest.jsonl"
    man = mf.load_manifest(man_path)
    for cell in a.osm_cells:
        la, lo = (float(v) for v in cell.split(","))
        bbox = (lo - 0.002, la - 0.002, lo + 0.012, la + 0.012)
        recs = {}
        for tb in mf.tile_bbox(bbox):
            for r in client.images_in_bbox(tb):
                recs[str(r["id"])] = r
        cand = score_records(recs.values(), houses, a, to_pl)
        chosen = []
        for c in cand:
            if all(math.hypot(c[2] - o[2], c[3] - o[3]) >= a.spacing for o in chosen):
                chosen.append(c)
            if len(chosen) >= a.per_cell:
                break
        print(cell, "records", len(recs), "cand", len(cand), "chosen", len(chosen))
        if a.dry:
            continue
        for s, i, px, py, r in chosen:
            if i in man:
                continue
            sha = client.download(r["thumb_2048_url"], outdir / f"{i}.jpg")
            e = mf.make_entry(r, sha, [])
            e["houses_in_view"] = s
            e["x2180"], e["y2180"] = round(px, 1), round(py, 1)
            e["cell"] = cell
            e["purpose"] = "posesje-r7 (ADR 0114): referencja plotow/bram/podjazdow; tylko referencja"
            man[i] = e
            mf.write_manifest(man_path, man)
    print("manifest", len(man))


main()
