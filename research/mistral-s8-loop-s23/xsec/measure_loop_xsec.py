"""Przekroje pętli S8<->DW671<->Tykocin z ortofoto GUGiK WMS — metoda jak tools/worldgen/qa/ortho_xsec.py (ADR 0272).

Wejście: ../raw/osm/loop_roads.json (OSM API 0.6, 15 kafli pętli; patrz ../raw/osm/manifest.json).
Wyjście: <group>.json w tym katalogu (jeden wiersz na stację; tylko liczby, żaden piksel nie jest zapisywany).

  uv run --project tools/worldgen python research/mistral-s8-loop-s23/xsec/measure_loop_xsec.py [grupa ...]

Grupy: s8 (motorway ref=S8, co 500 m), s8_links (motorway_link, co 150 m), dw671 (ref=671, co 250 m),
dk64 (ref=64 przy Jeżewie, co 250 m), junction_roads (drogi klas >= tertiary stykające się z łącznicą, co 200 m).
Stacja = punkt na osi way; wycinek GetMap 36x36 m przy 0,05 m/px (EPSG:2180, warstwa Raster, ten sam WMS co ADR 0272);
profil jasności/nasycenia prostopadły do osi (+-17 m, krok 0,05 m), mediana po +-6 m wzdłuż osi.
asphalt = ciągły przebieg szarych pikseli przez oś (jak w ortho_xsec.py); paved = luźniejszy próg (asfalt + pobocze
utwardzone); lines = piki jasności >= asfalt+18 wewnątrz asfaltu (linie krawędziowe); grass = pierwszy piksel zieleni
za asfaltem (krawędź pobocza gruntowego / rowu).
"""
import importlib.util, io, json, sys, time, urllib.request
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
spec = importlib.util.spec_from_file_location("ortho_xsec", REPO / "tools/worldgen/qa/ortho_xsec.py")
ox = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ox)          # WMS_URL, HALF, PX, RES z narzędzia ADR 0272
URL, HALF, PX, RES = ox.URL, ox.HALF, ox.PX, ox.RES
UA = {"User-Agent": "osm-research-client/1.0"}

GROUPS = {
    "s8": lambda r: r["tags"].get("highway") == "motorway" and "S8" in r["tags"].get("ref", "").split(";"),
    "s8_links": lambda r: r["tags"].get("highway") == "motorway_link" and r["length_m"] >= 60,
    "dw671": lambda r: "671" in r["tags"].get("ref", "").split(";"),
    "dk64": lambda r: "64" in r["tags"].get("ref", "").split(";"),
    "junction_roads": lambda r: r["tags"].get("highway") in ("primary", "secondary", "tertiary", "unclassified"),
}
STEP = {"s8": 500.0, "s8_links": 150.0, "dw671": 250.0, "dk64": 250.0, "junction_roads": 200.0}


def crop(cx, cy):
    u = URL.format(x0=cx - HALF, x1=cx + HALF, y0=cy - HALF, y1=cy + HALF, px=PX)
    for k in range(4):
        try:
            req = urllib.request.Request(u, headers=UA)
            return np.asarray(__import__("PIL.Image", fromlist=["Image"]).open(io.BytesIO(urllib.request.urlopen(req, timeout=90).read())).convert("RGB"), float)
        except Exception:
            time.sleep(2 ** (k + 1))
    raise SystemExit(f"WMS failed at {cx},{cy}")


def profile(A, c, t, n):
    lat = np.arange(-17.0, 17.0 + 1e-9, 0.05)
    al = np.arange(-6.0, 6.0 + 1e-9, 0.25)
    X = c[0] + lat[None, :] * n[0] + al[:, None] * t[0]
    Y = c[1] + lat[None, :] * n[1] + al[:, None] * t[1]
    col = np.clip(((X - (c[0] - HALF)) / RES).astype(int), 0, PX - 1)
    row = np.clip((((c[1] + HALF) - Y) / RES).astype(int), 0, PX - 1)
    med = np.median(A[row, col], axis=0)
    v = med.mean(axis=1)
    sat = (med.max(axis=1) - med.min(axis=1)) / np.maximum(med.max(axis=1), 1)
    green = med[:, 1] - 0.5 * (med[:, 0] + med[:, 2])
    return lat, v, sat, green


def runs(lat, ok):
    k0 = len(lat) // 2
    out = {}
    for sign, key in ((+1, "R"), (-1, "L")):
        k, miss, last = k0, 0, k0
        while 0 < k < len(lat) - 1 and miss < 6:
            k += sign
            if ok[k]:
                last, miss = k, 0
            else:
                miss += 1
        out[key] = lat[last]
    return out


def measure(group, ways, step, out):
    rows = []
    if out.exists():
        rows = json.loads(out.read_text())
        done = {(r["way"], r["s"]) for r in rows}
    else:
        done = set()
    for w in sorted(ways, key=lambda r: r["id"]):
        if not GROUPS[group](w):
            continue
        P = np.array(w["geometry_2180"], float)
        seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
        s = np.concatenate([[0], np.cumsum(seg)])
        if s[-1] < 50:
            continue
        for st in np.arange(25.0, s[-1] - 25.0 + 1e-6, step):
            if (w["id"], round(float(st), 1)) in done:
                continue
            i = min(np.searchsorted(s, st) - 1, len(seg) - 1)
            t = (P[i + 1] - P[i]) / seg[i]
            c = P[i] + t * (st - s[i])
            n = np.array([-t[1], t[0]])
            A = crop(*c)
            lat, v, sat, green = profile(A, c, t, n)
            k0 = len(lat) // 2
            core = slice(k0 - 40, k0 + 41)
            a_v, a_sat = np.median(v[core]), np.median(sat[core])
            ok = (sat < a_sat + 0.07) & (np.abs(v - a_v) < 38) & (green < 6)
            okl = ok | ((v > a_v + 25) & (sat < 0.12))
            okp = (sat < a_sat + 0.15) & (np.abs(v - a_v) < 60) & (green < 10)
            a = runs(lat, okl)
            p = runs(lat, okp)
            eL, eR = a["L"], a["R"]   # eL < 0 < eR (lat ujemne = lewo od kierunku jazdy)
            pk = [round(float(lat[k]), 2) for k in range(2, len(lat) - 2)
                  if v[k] > a_v + 18 and v[k] >= v[k - 2:k + 3].max() and eL - 0.1 <= lat[k] <= eR + 0.1 and sat[k] < 0.15]
            merged = []
            for q in pk:
                if merged and q - merged[-1] < 0.4:
                    continue
                merged.append(q)
            gL = next((round(float(lat[k]), 2) for k in range(k0, 0, -1) if green[k] > 6), None)
            gR = next((round(float(lat[k]), 2) for k in range(k0, len(lat)) if green[k] > 6), None)
            rows.append({"way": w["id"], "ref": w["tags"].get("ref"), "highway": w["tags"].get("highway"),
                         "lanes": w["tags"].get("lanes"), "s": round(float(st), 1),
                         "x": round(float(c[0]), 1), "y": round(float(c[1]), 1),
                         "asphalt_L": round(float(eL), 2), "asphalt_R": round(float(eR), 2), "asphalt_w": round(float(eR - eL), 2),
                         "paved_L": round(float(p["L"]), 2), "paved_R": round(float(p["R"]), 2), "paved_w": round(float(p["R"] - p["L"]), 2),
                         "lines": merged, "grass_L": gL, "grass_R": gR})
            out.write_text(json.dumps(rows, indent=1))
            print(json.dumps(rows[-1]), flush=True)
            time.sleep(0.25)
    print(group, "stations:", len(rows), flush=True)


def main():
    roads = json.loads((HERE / "../raw/osm/loop_roads.json").read_text())["ways"]
    groups = sys.argv[1:] or list(GROUPS)
    # junction_roads: only ways sharing a node with a motorway_link
    if "junction_roads" in groups:
        link_nodes = set()
        for r in roads:
            if r["tags"].get("highway") == "motorway_link":
                pass
        way_nodes = {r["id"]: r for r in roads}
        # node sharing via raw geometry is not stored per-way; approximate: links and junction roads intersect in bbox overlap
        # -> use raw API: recompute from Data/raw
        raw = REPO / "Data/raw/osm_api_s8loop"
        nodes_of = {}
        linkn = set()
        for f in sorted(raw.glob("loop_*.json")):
            d = json.loads(f.read_text())
            for e in d["elements"]:
                if e["type"] == "way" and e.get("tags", {}).get("highway") == "motorway_link":
                    linkn.update(e["nodes"])
                if e["type"] == "way":
                    nodes_of[e["id"]] = e["nodes"]
        jr = [r for r in roads if GROUPS["junction_roads"](r) and set(nodes_of.get(r["id"], [])) & linkn]
        measure("junction_roads", jr, STEP["junction_roads"], HERE / "junction_roads.json")
        groups = [g for g in groups if g != "junction_roads"]
    for g in groups:
        measure(g, roads, STEP[g], HERE / f"{g}.json")


if __name__ == "__main__":
    main()
