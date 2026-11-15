#!/usr/bin/env python3
"""Pokrycie bboxu R9 arkuszami ze skorowidzow (files/gugik_raw/sheets_all.csv): raster 64 m (352x320 komorek),
udzial powierzchni per produkt/rocznik/piksel oraz 'najlepsza mozaika' (najnowsza data per komorka, z warunkiem rozdzielczosci)."""
import csv, json, pathlib, collections
root = pathlib.Path(__file__).resolve().parents[1]
X0, Y0, X1, Y1 = 764683, 584959, 787211, 605439; C = 64
NX, NY = (X1 - X0) // C, (Y1 - Y0) // C
rows = list(csv.DictReader(open(root / "files/gugik_raw/sheets_all.csv")))
def cells(box):
    a, b = box.split(" "); xa, ya = map(float, a.split(",")); xb, yb = map(float, b.split(","))
    i0 = max(0, int((xa - X0) / C + .5)); i1 = min(NX, int((xb - X0) / C + .5)); j0 = max(0, int((ya - Y0) / C + .5)); j1 = min(NY, int((yb - Y0) / C + .5))
    return i0, i1, j0, j1
out = {"bbox_epsg2180": [X0, Y0, X1, Y1], "komorka_m": C, "grupy": [], "mozaiki": {}}
groups = collections.defaultdict(list)
for r in rows:
    res = r["piksel"] or r["char_przestrz"]
    groups[(r["produkt"], r["rok_warstwy"], res, r["kolor"] or r["format"], r["nr_zglosz"], r["modul_archiwizacji"])].append(r)
for k, rs in sorted(groups.items()):
    g = set()
    for r in rs:
        i0, i1, j0, j1 = cells(r["box"])
        g.update((i, j) for i in range(i0, i1) for j in range(j0, j1))
    mb = sum(float(r["wlk_pliku_mb"] or 0) for r in rs)
    out["grupy"].append({"produkt": k[0], "rok": k[1], "rozdzielczosc": k[2], "kolor_format": k[3], "nr_zglosz": k[4], "modul": k[5], "arkuszy": len(rs),
                         "akt_data_min": min(r["akt_data"] for r in rs), "akt_data_max": max(r["akt_data"] for r in rs),
                         "pokrycie_bbox_proc": round(100 * len(g) / (NX * NY), 1), "suma_wlk_pliku_mb": mb or None})
def mosaic(name, pred):
    best = {}
    for r in rows:
        if not pred(r): continue
        i0, i1, j0, j1 = cells(r["box"])
        for i in range(i0, i1):
            for j in range(j0, j1):
                if (i, j) not in best or r["akt_data"] > best[(i, j)]["akt_data"]: best[(i, j)] = r
    used = {}
    for r in best.values(): used[r["fid"]] = r
    by = collections.Counter((r["akt_data"][:4], r["piksel"] or r["char_przestrz"]) for r in best.values())
    out["mozaiki"][name] = {"pokrycie_proc": round(100 * len(best) / (NX * NY), 1), "arkuszy": len(used),
        "udzial_powierzchni_rok_rozdz_proc": {f"{a}|{b}": round(100 * n / (NX * NY), 1) for (a, b), n in sorted(by.items())},
        "suma_wlk_pliku_mb": sum(float(r["wlk_pliku_mb"] or 0) for r in used.values()) or None,
        "akt_data_min": min(r["akt_data"] for r in used.values()), "akt_data_max": max(r["akt_data"] for r in used.values())}
    return used
u1 = mosaic("ORTO_RGB_najnowsza", lambda r: r["produkt"] == "ORTO" and r["kolor"] == "RGB")
u2 = mosaic("ORTO_RGB_najnowsza_piksel<=0.10", lambda r: r["produkt"] == "ORTO" and r["kolor"] == "RGB" and float(r["piksel"]) <= 0.10)
u3 = mosaic("ORTO_RGB_najnowsza_piksel_0.05", lambda r: r["produkt"] == "ORTO" and r["kolor"] == "RGB" and float(r["piksel"]) <= 0.05)
u4 = mosaic("NMT_1m_najnowsza", lambda r: r["produkt"] == "NMT" and r["char_przestrz"].startswith("1.00") and "ARC/INFO" in r["format"])
u5 = mosaic("NMPT_najnowsza", lambda r: r["produkt"] == "NMPT")
json.dump(out, open(root / "gugik/skorowidze_coverage.json", "w"), ensure_ascii=False, indent=1)
with open(root / "gugik/skorowidze_sheets_recommended.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["mozaika", "produkt", "godlo", "akt_data", "rozdzielczosc", "nr_zglosz", "wlk_pliku_mb", "url_do_pobrania"])
    for name, u in (("ORTO_RGB_najnowsza", u1), ("NMT_1m_najnowsza", u4), ("NMPT_najnowsza", u5)):
        for r in sorted(u.values(), key=lambda r: r["godlo"]):
            w.writerow([name, r["produkt"], r["godlo"], r["akt_data"], r["piksel"] or r["char_przestrz"], r["nr_zglosz"], r["wlk_pliku_mb"], r["url_do_pobrania"]])
for g in out["grupy"]: print(g)
for k, v in out["mozaiki"].items(): print(k, v)
