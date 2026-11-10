r"""Per-object open references (D43, ADR 0066): Kwadrat Park, nearest fire station, dusk/sodium lighting.

Sources (all open, no keys): KartaView + Panoramax street-level around the object, Wikimedia Commons (geosearch +
text search, licence from extmetadata), Openverse (CC0/BY/BY-SA queries), GUGiK ortho crops, plan view of our own
building data. Licence gate = refs_common.normalize_license (NC/ND/unknown rejected). Raw: Data/raw/refs/objects/<obj>/
(outside git), contact sheets + INDEX.md: artifacts/refs/<obj>/.

  uv run --project tools/refs python tools/refs/object_refs.py --object kwadrat-park fire-station dusk-sodium
  uv run --project tools/refs python tools/refs/object_refs.py --object fire-station --index-only
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import refs_common as rc  # noqa: E402
import open_sources as osrc  # noqa: E402
import gugik_ortho as go  # noqa: E402

# OSM way 211035271 "Jednostka Ratowniczo-Gasnicza Nr 2", ul. gen. Andersa (centroid from podlaskie-261108.osm.pbf)
FIRE_STATION = {"lat": 53.157322, "lon": 23.156306, "osm": "way/211035271"}

OBJECTS = {
    "kwadrat-park": {
        "title": "Kwadrat Park (hale, brama, portiernia, rampy, plac)",
        # points from docs/owner/PHOTO-LIST.md shots 1, 3, 7, 10 (+ centre); private area -> public road + Commons only
        "points": [
            {"nr": 1, "type": "plac", "place": "plac przy rampach (start trasy)", "lat": 53.154483, "lon": 23.170276, "azimuth": 209.0},
            {"nr": 3, "type": "hala", "place": "najwieksza hala", "lat": 53.154241, "lon": 23.170017, "azimuth": 277.0},
            {"nr": 7, "type": "rampy", "place": "rampy zaladunkowe", "lat": 53.153523, "lon": 23.168977, "azimuth": 341.0},
            {"nr": 10, "type": "brama", "place": "wjazd z drogi publicznej", "lat": 53.152772, "lon": 23.168427, "azimuth": 35.0},
            {"nr": 11, "type": "centrum", "place": "srodek kompleksu", "lat": 53.1540, "lon": 23.1700, "azimuth": None},
        ],
        "street_radius": 120, "commons_radius": 500,
        "commons_search": ["Kwadrat Park Białystok", "Kwadrat Park", "Generała Władysława Andersa Białystok magazyn",
                           "Białystok hala magazynowa Andersa", "Białystok Andersa 40"],
        "openverse": ["Kwadrat Park Białystok", "Białystok magazyn Andersa"],
        "ortho_windows": [(400, "ogolny"), (160, "kompleks"), (70, "brama-rampy")],
        "plan_radius": 220,
    },
    "fire-station": {
        "title": "JRG nr 2 Białystok, ul. gen. Andersa (OSM " + FIRE_STATION["osm"] + ")",
        "points": [{"nr": 1, "type": "JRG 2", "place": "Jednostka Ratowniczo-Gasnicza Nr 2", "lat": FIRE_STATION["lat"],
                    "lon": FIRE_STATION["lon"], "azimuth": None}],
        "street_radius": 150, "commons_radius": 400,
        "commons_search": ["Jednostka Ratowniczo-Gaśnicza nr 2 Białystok", "Straż pożarna Białystok Andersa",
                           "JRG 2 Białystok", "Komenda Miejska Państwowej Straży Pożarnej w Białymstoku",
                           "Fire station Białystok"],
        "openverse": ["Białystok straż pożarna", "Straż pożarna Andersa Białystok"],
        "ortho_windows": [(300, "otoczenie"), (110, "obiekt")],
        "plan_radius": 160,
        "footer": ["Pozycja: OSM way/211035271, centroid 53.157322, 23.156306 (podlaskie-261108.osm.pbf), nazwa \"Jednostka Ratowniczo-Gasnicza Nr 2\", "
                   "ul. gen. Andersa, operator KM PSP Bialystok; odleglosc ok. 1,0 km od Kwadrat Park, przy trasie Andersa.",
                   "Kontrola krzyzowa: dane otwarte Miasta Bialystok (straz_pozarna.geojson): punkt 53.157380, 23.155985, ul. Andersa 46 (rozbieznosc ok. 25 m).",
                   "Z ortofotomapy (okno 110 m): budynek dowodzenia z niebieskimi dachami blaszanymi (kilka bryl), hala garazowa z szarym dachem, "
                   "plac manewrowy z kostki/asfaltu, wozy czerwone na placu, parking po polnocy; plan: `plan_budynki.jpg` (straz 6,55 m wg LoD1)."],
    },
    "dusk-sodium": {
        "title": "Zmierzch / światła sodowe w Białymstoku (nastrój, barwa, kontrast)",
        "points": [{"nr": 1, "type": "trasa", "place": "Andersa / Rondo Putry (kontrola)", "lat": 53.1549, "lon": 23.1633, "azimuth": None}],
        "street_radius": 0, "commons_radius": 0,
        "commons_search": ["Białystok nocą", "Białystok wieczór", "Białystok zmierzch", "Białystok ulica noc latarnie",
                           "Białystok night street", "Białystok dusk", "Białystok oświetlenie uliczne", "Białystok zachód słońca ulica"],
        "openverse": ["Białystok noc", "Białystok wieczór ulica", "Białystok zmierzch", "Bialystok night"],
        "ortho_windows": [], "plan_radius": 0,
    },
}


def load_curation(name, root):
    """Optional tools/refs/curation/<name>.json (in git): {"reject": {id: reason}, "notes": {id: text}} (reviewed by eye)."""
    import json
    f = Path(__file__).resolve().parent / "curation" / f"{name}.json"
    if not f.exists():
        return {}, {}
    d = json.loads(f.read_text(encoding="utf-8"))
    return d.get("reject", {}), d.get("notes", {})


def ref_point(name):
    pts = OBJECTS[name]["points"]
    return pts[-1] if name == "kwadrat-park" else pts[0]


def bearing(lat1, lon1, lat2, lon2):
    y = math.sin(math.radians(lon2 - lon1)) * math.cos(math.radians(lat2))
    x = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - \
        math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(math.radians(lon2 - lon1))
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def commons_text(http, query, limit=30):
    """list=search (File: namespace) -> imageinfo/extmetadata candidates."""
    body = http.get_json(osrc.CM_API, {"action": "query", "format": "json", "list": "search", "srsearch": query,
                                       "srnamespace": 6, "srlimit": limit})
    titles = [h["title"] for h in (body.get("query") or {}).get("search", [])]
    infos = osrc._commons_imageinfo(http, titles)
    out = []
    for t in titles:
        c = osrc._commons_cand(t, infos[t]) if t in infos else None
        if c:
            out.append(c)
    return out


def fetch_object(name, http, root, now=None, log=print):
    obj = OBJECTS[name]
    pts = obj["points"]
    base = Path(root) / name
    if obj["street_radius"]:
        for src, fn in (("kartaview", lambda p, h: osrc.kartaview_all(p, h, obj["street_radius"])),
                        ("panoramax", lambda p, h: osrc.panoramax_candidates(p, h, obj["street_radius"])),
                        ("commons-geo", lambda p, h: osrc.commons_candidates(p, h, obj["commons_radius"]))):
            try:
                rc.fetch_for_points(src, pts, fn, http, base / src, per_point=8, max_total=80, now=now, log=log)
            except rc.SourceError as e:
                log(f"[{name}/{src}] {e}")
    items = [(q, lambda h, q=q: commons_text(h, q)) for q in obj["commons_search"]]
    try:
        osrc.fetch_text_source("commons-search", items, None, http, base / "commons-search", per_item=10, max_total=80, now=now, log=log)
    except rc.SourceError as e:
        log(f"[{name}/commons-search] {e}")
    ov = [(q, lambda h, q=q: osrc.openverse_candidates_for_query(h, q)) for q in obj["openverse"]]
    try:
        osrc.fetch_text_source("openverse", ov, None, http, base / "openverse", per_item=8, max_total=40, now=now, log=log)
    except rc.SourceError as e:
        log(f"[{name}/openverse] {e}")


def ortho_crops(name, http, root, now=None, log=print):
    obj = OBJECTS[name]
    out = Path(root) / name / "gugik-ortho"
    c = ref_point(name)
    for w, label in obj["ortho_windows"]:
        p = {"nr": int(w), "type": label, "place": f"{name} {label} ({w} m)", "lat": c["lat"], "lon": c["lon"], "azimuth": None}
        go.fetch([p], http, out, window=float(w), px=800, now=now, log=log)


def plan_view(name, art):
    """2D plan of our own region building data (heights, function) around the object; no external service."""
    import json
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from pyproj import Transformer
    from shapely.geometry import shape, Point
    obj = OBJECTS[name]
    c = ref_point(name)
    x0, y0 = Transformer.from_crs("EPSG:4326", "EPSG:2180", always_xy=True).transform(c["lon"], c["lat"])
    R = obj["plan_radius"]
    gj = json.loads((rc.REPO / "Data/Regions/bialystok-industrial-c/buildings.geojson").read_text(encoding="utf-8"))
    fig, ax = plt.subplots(figsize=(9, 9))
    n = 0
    for f in gj["features"]:
        g = shape(f["geometry"])
        if g.distance(Point(x0, y0)) > R:
            continue
        n += 1
        pr = f["properties"]
        for poly in (g.geoms if hasattr(g, "geoms") else [g]):
            xs, ys = poly.exterior.xy
            ax.fill([a - x0 for a in xs], [b - y0 for b in ys], color="#8a99a8", ec="#222", lw=0.6)
        if pr.get("area_m2", 0) > 400:
            ax.text(g.centroid.x - x0, g.centroid.y - y0, f"{pr.get('height_m') or '?'} m\n{pr.get('function') or ''}",
                    fontsize=6, ha="center", va="center")
    ax.plot(0, 0, "r+", ms=14)
    ax.set_xlim(-R, R)
    ax.set_ylim(-R, R)
    ax.set_aspect("equal")
    ax.grid(alpha=0.3)
    ax.set_title(f"{name}: BDOT10k footprints + LoD1/LoD2 heights (EPSG:2180, N up), {n} buildings; + = {c['lat']:.5f},{c['lon']:.5f}", fontsize=8)
    p = Path(art) / "plan_budynki.jpg"
    p.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(p, dpi=100, format="jpg")
    plt.close(fig)
    return p, n


def collect(name, root):
    rows = []
    for mf in sorted((Path(root) / name).glob("*/manifest.jsonl")):
        for e in rc.load_manifest(mf).values():
            rows.append((mf.parent.name, mf.parent, e))
    return rows


def build_index(name, root, art, tile_h=300):
    from PIL import Image, ImageDraw, ImageFont
    obj = OBJECTS[name]
    ref = ref_point(name)
    reject, notes = load_curation(name, root)
    allrows = [r for r in collect(name, root) if r[0] != "gugik-ortho"]
    rows, seen_sha = [], set()
    for r in allrows:
        if r[2]["id"] in reject or r[2].get("sha256") in seen_sha:
            continue
        seen_sha.add(r[2].get("sha256"))
        rows.append(r)

    def dist(e):
        return 1e9 if e.get("lat") is None else rc.haversine_m(ref["lon"], ref["lat"], e["lon"], e["lat"])

    rows.sort(key=lambda r: (dist(r[2]), r[2]["id"]))
    art = Path(art)
    art.mkdir(parents=True, exist_ok=True)
    for old in art.glob("montaz_*.jpg"):
        old.unlink()
    font = ImageFont.load_default()
    cols, per_sheet = 4, 12
    sheets = []
    for si in range(0, len(rows), per_sheet):
        tiles = []
        for j, (src, d, e) in enumerate(rows[si:si + per_sheet]):
            try:
                im = Image.open(d / e["file"]).convert("RGB")
            except Exception:
                continue
            tiles.append((im.resize((max(1, round(im.width * tile_h / im.height)), tile_h)), src, e, si + j + 1))
        if not tiles:
            continue
        cw = max(t[0].width for t in tiles)
        nr = math.ceil(len(tiles) / cols)
        sh = Image.new("RGB", (cols * (cw + 6) + 6, nr * (tile_h + 40) + 6), (24, 24, 24))
        d = ImageDraw.Draw(sh)
        for i, (im, src, e, idx) in enumerate(tiles):
            x, y = 6 + (i % cols) * (cw + 6), 6 + (i // cols) * (tile_h + 40)
            sh.paste(im, (x, y))
            d.text((x, y + tile_h + 3), f"#{idx} {src} {e['license']}", fill=(220, 220, 220), font=font)
            d.text((x, y + tile_h + 17), f"(c) {str(e.get('author'))[:46]}", fill=(150, 150, 150), font=font)
        f = art / f"montaz_{si // per_sheet + 1:02d}.jpg"
        sh.save(f, "JPEG", quality=84)
        sheets.append(f)
    lines = [f"# Referencje: {obj['title']}", "",
             "Zrodla otwarte (D43, ADR 0066): tylko CC0/PD/CC BY/CC BY-SA; BY-SA = referencja wizualna, nie tekstura (docs/LICENSES.md).",
             f"Pliki surowe: `Data/raw/refs/objects/{name}/<zrodlo>/` (poza gitem). # = numer kafla na montazu `montaz_NN.jpg` (12 na arkusz).", "",
             "| # | plik | zrodlo | licencja | autor | URL | kierunek / pozycja |", "|---|---|---|---|---|---|---|"]
    for i, (src, d, e) in enumerate(rows, 1):
        if e.get("lat") is not None:
            pos = f"{e['lat']:.5f},{e['lon']:.5f}"
            if e.get("heading") is not None:
                pos += f", kier. {float(e['heading']):.0f} deg"
            pos += f", {dist(e):.0f} m od obiektu, namiar na obiekt {bearing(e['lat'], e['lon'], ref['lat'], ref['lon']):.0f} deg"
        else:
            pos = "brak wspolrzednych (zapytanie: %s)" % (e.get("query") or e.get("title") or "?")
        if e["id"] in notes:
            pos += " | " + notes[e["id"]]
        a = str(e.get("author") or "?").replace("|", "/")
        lines.append(f"| {i} | `{src}/{e['file']}` | {src} | {e['license']} | {a[:60]} | {e.get('page_url')} | {pos} |")
    ortho_rows = [e for s, d, e in collect(name, root) if s == "gugik-ortho"]
    if ortho_rows:
        lines += ["", "## Ortofotomapa GUGiK (EPSG:2180, N u gory)", "", "| plik | okno | rozdz. | licencja | URL |", "|---|---|---|---|---|"]
        for e in sorted(ortho_rows, key=lambda e: -e["window_m"]):
            lines.append(f"| `gugik-ortho/{e['file']}` (art: `ortho/{Path(e['file']).stem}.jpg`) | {e['window_m']:.0f} m | {e['resolution_m_per_px']} m/px | GUGiK open data | {e['page_url']} |")
    if obj.get("footer"):
        lines += ["", "## Obiekt"] + ["- " + t for t in obj["footer"]]
    if reject:
        lines += ["", "## Odrzucone po przegladzie (pliki zostaja w Data/raw)", ""] + [f"- `{k}`: {v}" for k, v in sorted(reject.items())]
    lines += ["", f"Lacznie obrazow: {len(rows)} (zrodla: " + ", ".join(sorted({r[0] for r in rows})) + ").", ""]
    (art / "INDEX.md").write_text("\n".join(lines), encoding="utf-8")
    return len(rows), sheets


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--object", nargs="+", required=True, choices=sorted(OBJECTS))
    ap.add_argument("--interval", type=float, default=1.2)
    ap.add_argument("--index-only", action="store_true")
    ap.add_argument("--root", help=argparse.SUPPRESS)
    ap.add_argument("--art", help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    root = Path(a.root) if a.root else rc.RAW_ROOT / "objects"
    artroot = Path(a.art) if a.art else rc.ART_ROOT
    for name in a.object:
        http = rc.Http(cache_dir=root / name / ".cache", min_interval=a.interval)
        art = artroot / name
        try:
            if not a.index_only:
                fetch_object(name, http, root)
                if OBJECTS[name]["ortho_windows"]:
                    ortho_crops(name, http, root)
        except rc.SourceError as e:
            print(f"error: {e}")
        if OBJECTS[name]["plan_radius"]:
            print(plan_view(name, art))
        from PIL import Image
        for f in (root / name / "gugik-ortho").glob("shot_*.png"):
            (art / "ortho").mkdir(parents=True, exist_ok=True)
            Image.open(f).convert("RGB").resize((800, 800)).save(art / "ortho" / (f.stem + ".jpg"), quality=85)
        print(name, build_index(name, root, art))


if __name__ == "__main__":
    main()
