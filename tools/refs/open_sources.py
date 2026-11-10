r"""Open image sources for route references (D43, ADR 0066): KartaView, Panoramax, Wikimedia Commons, Openverse.

No keys, no accounts. Only CC0 / public domain / CC BY / CC BY-SA are downloaded; NC/ND/unknown are rejected and
counted. Results: Data/raw/refs/<source>/ (outside git) + manifest.jsonl; montages artifacts/refs/<source>/shot_NN.jpg.

  uv run --project tools/refs python tools/refs/open_sources.py --source kartaview [--only-weak] [--max 150]
  uv run --project tools/refs python tools/refs/open_sources.py --source commons --categories
  uv run --project tools/refs python tools/refs/open_sources.py --source openverse
  uv run --project tools/refs python tools/refs/open_sources.py --source panoramax
"""

from __future__ import annotations

import argparse
import re
import sys
from html import unescape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import refs_common as rc  # noqa: E402

KV_API = "https://api.kartaview.org/2.0/photo/"
KV1_API = "https://api.kartaview.org/1.0/list/nearby-photos/"
PX_API = "https://api.panoramax.xyz/api/search"
CM_API = "https://commons.wikimedia.org/w/api.php"
OV_API = "https://api.openverse.org/v1/images/"

# Commons categories checked for the route (existence verified at runtime; unknown ones are logged, not guessed).
COMMONS_CATEGORIES = [
    "Białystok Power Plant (Andersa Street)",
    "Roads in Białystok",
    "Fire stations in Białystok",
    "Bridges in Białystok",
    "Roundabouts in Białystok",
    "Streets in Białystok",
    "Generała Władysława Andersa Street in Białystok",
    "Aleja Jana Pawła II in Białystok",
    "Aleja Tysiąclecia Państwa Polskiego in Białystok",
    "Rondo Pamięci Bieżeństwa",
    "Viaducts in Białystok",
    "Bus stops in Białystok",
    "Street lights in Białystok",
    "Road signs in Białystok",
    "Trees in Białystok",
    "Industrial buildings in Białystok",
    "Warehouses in Poland",
    "Roads in Podlaskie Voivodeship",
    "Droga krajowa nr 8 (Polska)",
    "Droga krajowa nr 19 (Polska)",
]

OPENVERSE_QUERIES = [
    "Białystok Andersa", "Białystok rondo", "Białystok wiadukt", "Białystok ulica", "Białystok Aleja Tysiąclecia",
    "Białystok przystanek", "Białystok straż pożarna", "Białystok latarnia", "Białystok droga krajowa",
    "Białystok hala magazyn", "Białystok blok osiedle", "Białystok jesień ulica", "Białystok skrzyżowanie",
    "Bialystok street", "Bialystok roundabout",
]


def _strip_html(s):
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", "", s or ""))).strip()


# ---------------------------------------------------------------- KartaView (CC BY-SA 4.0)

def kartaview_candidates(p, http, radius=60):
    """GET api.kartaview.org/2.0/photo (no key; radius max 500 m). Skips blurred/spherical/hidden photos."""
    body = http.get_json(KV_API, {"lat": f"{p['lat']:.6f}", "lng": f"{p['lon']:.6f}", "radius": min(int(radius), 500)})
    out = []
    for r in (body.get("result") or {}).get("data", []) or []:
        if r.get("status", "active") != "active" or r.get("visibility", "public") != "public":
            continue
        if r.get("autoImgProcessingResult") == "BLURRED" or r.get("projection", "PLANE") != "PLANE":
            continue
        url = r.get("fileurlProc") or r.get("fileurl")
        if not url or "{{sizeprefix}}" in url:
            url = r.get("fileurlProc") or ""
        if not url:
            continue
        user = r.get("user")
        author = (user.get("name") or user.get("username")) if isinstance(user, dict) else None
        out.append({
            "id": f"kv{r['id']}", "title": r.get("name"),
            "lat": float(r["lat"]), "lon": float(r["lng"]),
            "heading": float(r["heading"]) if r.get("heading") not in (None, "") else None,
            "date": (r.get("shotDate") or r.get("dateAdded") or "")[:10] or None,
            "author": author or "KartaView contributor (sequence %s)" % r.get("sequenceId"),
            "license": "CC BY-SA 4.0", "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
            "page_url": f"https://kartaview.org/details/{r.get('sequenceId')}/{r.get('sequenceIndex')}/track-info",
            "file_url": url, "ext": ".jpg",
        })
    return out


def kartaview_v1_candidates(p, http, radius=80):
    """Legacy POST /1.0/list/nearby-photos/ (still keyless, returns far more history than v2): storageN paths."""
    body = http.post_json(KV1_API, {"lat": f"{p['lat']:.6f}", "lng": f"{p['lon']:.6f}", "radius": int(radius)})
    out = []
    for r in body.get("currentPageItems", []) or []:
        if r.get("projection", "PLANE") != "PLANE":
            continue
        name = r.get("name") or ""
        m = re.match(r"(storage\d+)/(files/photo/.+)", name)
        if not m:
            continue
        out.append({
            "id": f"kv{r['id']}", "title": name.rsplit("/", 1)[-1],
            "lat": float(r["lat"]), "lon": float(r["lng"]),
            "heading": float(r["heading"]) if r.get("heading") not in (None, "", "0.00") else None,
            "date": (r.get("shot_date") or r.get("date_added") or "")[:10] or None,
            "author": r.get("username") or "KartaView contributor",
            "license": "CC BY-SA 4.0", "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
            "page_url": f"https://kartaview.org/details/{r.get('sequence_id')}/{r.get('sequence_index')}/track-info",
            "file_url": f"https://{m.group(1)}.openstreetcam.org/{m.group(2)}", "ext": ".jpg",
        })
    return out


def kartaview_all(p, http, radius=80):
    seen, out = set(), []
    for fn in (kartaview_v1_candidates, kartaview_candidates):
        try:
            cs = fn(p, http, radius)
        except rc.SourceError:
            continue
        for c in cs:
            if c["id"] not in seen:
                seen.add(c["id"])
                out.append(c)
    return out


# ---------------------------------------------------------------- Panoramax (licence per picture/instance)

def panoramax_candidates(p, http, radius=80):
    """GET api.panoramax.xyz/api/search?bbox= (federated meta-catalogue, STAC). Licence read per feature."""
    b = rc.bbox_around(p["lon"], p["lat"], radius)
    body = http.get_json(PX_API, {"bbox": ",".join(f"{v:.6f}" for v in b), "limit": 100})
    out = []
    for f in body.get("features", []):
        pr = f.get("properties") or {}
        lic = pr.get("license")
        lic_url = next((l.get("href") for l in f.get("links", []) if l.get("rel") == "license"), None)
        assets = f.get("assets") or {}
        href = (assets.get("sd") or assets.get("hd") or {}).get("href")
        if not href or "geometry" not in f:
            continue
        lon, lat = f["geometry"]["coordinates"][:2]
        prov = next((x.get("name") for x in f.get("providers", []) if "producer" in x.get("roles", [])), None)
        via = next((l.get("href") for l in f.get("links", []) if l.get("rel") == "via"), None)
        az = pr.get("view:azimuth")
        if az is None:
            d = (pr.get("exif") or {}).get("Exif.GPSInfo.GPSImgDirection", "")
            try:
                n, m = d.split("/")
                az = float(n) / float(m)
            except (ValueError, ZeroDivisionError):
                az = None
        out.append({
            "id": f"px{f['id']}", "title": f["id"], "lat": lat, "lon": lon, "heading": az,
            "date": (pr.get("datetime") or "")[:10] or None, "author": prov or "Panoramax contributor",
            "license": lic, "license_url": lic_url,
            "page_url": f"https://api.panoramax.xyz/#focus=pic&pic={f['id']}" + (f" (instance {via})" if via else ""),
            "file_url": href, "ext": ".jpg",
        })
    return out


# ---------------------------------------------------------------- Wikimedia Commons (licence from extmetadata)

def _commons_imageinfo(http, titles):
    out = {}
    for i in range(0, len(titles), 40):
        chunk = titles[i:i + 40]
        body = http.get_json(CM_API, {
            "action": "query", "format": "json", "titles": "|".join(chunk), "prop": "imageinfo",
            "iiprop": "url|extmetadata|size|mime", "iiurlwidth": 2048, "iiextmetadatafilter":
            "LicenseShortName|LicenseUrl|Artist|DateTimeOriginal|DateTime|Credit|UsageTerms|Restrictions",
        })
        for pg in ((body.get("query") or {}).get("pages") or {}).values():
            ii = (pg.get("imageinfo") or [None])[0]
            if ii:
                out[pg["title"]] = ii
    return out


def _commons_cand(title, ii, lat=None, lon=None, pageid=None):
    if not str(ii.get("mime", "")).startswith("image/jpeg") and not str(ii.get("mime", "")).startswith("image/png"):
        return None
    md = ii.get("extmetadata") or {}
    g = lambda k: _strip_html((md.get(k) or {}).get("value"))
    lic = g("LicenseShortName") or g("UsageTerms")
    if g("Restrictions"):
        lic = f"restricted {g('Restrictions')}"  # personality/trademark restrictions: not auto-accepted
    ext = ".png" if "png" in ii["mime"] else ".jpg"
    return {
        "id": f"cm{pageid}" if pageid else "cm" + rc.safe_name(title),
        "title": title, "lat": lat, "lon": lon, "heading": None,
        "date": (g("DateTimeOriginal") or g("DateTime"))[:10] or None,
        "author": g("Artist") or "unknown", "license": lic, "license_label": lic or None,
        "license_url": g("LicenseUrl") or None, "page_url": ii.get("descriptionurl"),
        "file_url": ii.get("thumburl") or ii.get("url"), "ext": ext,
    }


def commons_candidates(p, http, radius=700):
    """list=geosearch around the shot (File: namespace) + imageinfo/extmetadata per file."""
    body = http.get_json(CM_API, {
        "action": "query", "format": "json", "list": "geosearch", "gscoord": f"{p['lat']:.6f}|{p['lon']:.6f}",
        "gsradius": min(int(radius), 10000), "gslimit": 50, "gsnamespace": 6})
    hits = (body.get("query") or {}).get("geosearch", [])
    infos = _commons_imageinfo(http, [h["title"] for h in hits])
    out = []
    for h in hits:
        ii = infos.get(h["title"])
        c = _commons_cand(h["title"], ii, h.get("lat"), h.get("lon"), h.get("pageid")) if ii else None
        if c:
            out.append(c)
    return out


def commons_category_candidates(http, category, limit=200):
    """Files of Category:<name> (cmtype=file), licence from extmetadata. Returns (exists, [cand])."""
    titles, cont = [], {}
    while len(titles) < limit:
        body = http.get_json(CM_API, {"action": "query", "format": "json", "list": "categorymembers",
                                      "cmtitle": f"Category:{category}", "cmtype": "file", "cmlimit": 100, **cont})
        titles += [m["title"] for m in (body.get("query") or {}).get("categorymembers", [])]
        cont = body.get("continue") or {}
        if not cont:
            break
    infos = _commons_imageinfo(http, titles[:limit])
    pid = {}
    out = [c for t in titles[:limit] if t in infos and (c := _commons_cand(t, infos[t])) and pid.setdefault(c["id"], 1)]
    return bool(titles), out


# ---------------------------------------------------------------- Openverse (CC only)

def openverse_candidates_for_query(http, q, page_size=20):
    """GET api.openverse.org/v1/images (anonymous). Server-side filter + client-side re-check of the licence."""
    body = http.get_json(OV_API, {"q": q, "license": "cc0,pdm,by,by-sa", "page_size": page_size})
    out = []
    for r in body.get("results", []):
        lic = f"{r.get('license')} {r.get('license_version') or ''}".strip()
        lic = "CC " + lic.upper() if r.get("license") not in ("cc0", "pdm") else r.get("license")
        out.append({
            "id": f"ov{r['id']}", "title": r.get("title"), "lat": None, "lon": None, "heading": None,
            "date": None, "author": r.get("creator") or "unknown", "license": lic,
            "license_url": r.get("license_url"), "page_url": r.get("foreign_landing_url"),
            "file_url": r.get("url"), "ext": ".jpg", "provider": r.get("provider"),
        })
    return out


# ---------------------------------------------------------------- text-driven sources (no coordinates)

def fetch_text_source(source, items, fn, http, outdir, per_item=8, max_total=150, now=None, log=print):
    """items: [(label, fn(http) -> [cand])]. Pseudo shots (nr 100+i) = query/category; manifest as usual."""
    entries = rc.load_manifest(Path(outdir) / "manifest.jsonl")
    pseudo, n_rej, n_new = [], 0, 0
    for i, (label, getter) in enumerate(items):
        shot = {"nr": 100 + i, "type": "query", "place": label}
        pseudo.append(shot)
        try:
            cands = getter(http)
        except rc.SourceError as e:
            log(f"[{source}] {label}: {e}")
            continue
        taken = 0
        for c in cands:
            key = rc.normalize_license(c.get("license"))
            if key is None:
                n_rej += 1
                continue
            if taken >= per_item or n_new >= max_total:
                break
            taken += 1
            c["file"] = f"{rc.safe_name(c['id'])}{c.get('ext', '.jpg')}"
            dest = Path(outdir) / c["file"]
            if c["id"] in entries and dest.exists():
                entries[c["id"]]["shots"] = sorted(set(entries[c["id"]].get("shots", [])) | {shot["nr"]})
                continue
            try:
                sha, size = http.download(c["file_url"], dest)
            except rc.SourceError as e:
                log(f"[{source}] skip {c['id']}: {e}")
                continue
            entries[c["id"]] = rc.make_entry(source, c, key, sha, size, {shot["nr"]}, now)
            entries[c["id"]]["query"] = label
            n_new += 1
    rc.write_manifest(Path(outdir) / "manifest.jsonl", entries)
    log(f"[{source}] licence-rejected {n_rej}, new downloads {n_new}, requests {http.requests_made}")
    return entries, pseudo


# ---------------------------------------------------------------- CLI

def run(args, http=None, points=None, now=None):
    src = args.source
    outdir = Path(args.out) if args.out else rc.RAW_ROOT / src
    art = Path(args.art) if args.art else rc.ART_ROOT / src
    http = http or rc.Http(cache_dir=outdir / ".cache", min_interval=args.interval)
    pts = points if points is not None else rc.parse_photo_list()
    if args.only_weak:
        weak = rc.weak_shots()
        if weak is None:
            print("no artifacts/refs/coverage.json: processing the whole route")
        else:
            pts = [p for p in pts if p["nr"] in weak]
    if src in ("kartaview", "panoramax", "commons"):
        fn = {"kartaview": lambda p, h: kartaview_all(p, h, args.radius or 60),
              "panoramax": lambda p, h: panoramax_candidates(p, h, args.radius or 80),
              "commons": lambda p, h: commons_candidates(p, h, args.radius or 700)}[src]
        entries, _ = rc.fetch_for_points(src, pts, fn, http, outdir, per_point=args.per_point, max_total=args.max,
                                         azimuth_tol=args.azimuth_tol if src != "commons" else None, now=now)
        n = rc.montages_for(src, pts, entries, outdir, art)
        print(f"montages: {n} -> {art}")
        if src == "commons" and args.categories:
            cats = []
            for c in args.category or COMMONS_CATEGORIES:
                cats.append((f"Category:{c}", lambda h, c=c: commons_category_candidates(h, c)[1]))
            e2, pseudo = fetch_text_source("commons", cats, None, http, outdir, per_item=args.per_item, max_total=args.max, now=now)
            print(f"category montages: {rc.montages_for('commons-cat', pseudo, e2, outdir, art / 'categories')}")
        return entries
    if src == "openverse":
        qs = args.query or OPENVERSE_QUERIES
        items = [(q, lambda h, q=q: openverse_candidates_for_query(h, q)) for q in qs]
        entries, pseudo = fetch_text_source("openverse", items, None, http, outdir, per_item=args.per_item, max_total=args.max, now=now)
        print(f"montages: {rc.montages_for('openverse', pseudo, entries, outdir, art)} -> {art}")
        return entries
    raise SystemExit(f"unknown source {src}")


def build_parser():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True, choices=["kartaview", "panoramax", "commons", "openverse"])
    ap.add_argument("--only-weak", action="store_true", help="only shots rated SŁABE/BRAK in artifacts/refs/coverage.json (if present)")
    ap.add_argument("--radius", type=float, help="search radius in m (kartaview <= 500)")
    ap.add_argument("--per-point", type=int, default=4)
    ap.add_argument("--per-item", type=int, default=8, help="images per category/query (text sources)")
    ap.add_argument("--azimuth-tol", type=float, help="keep images whose heading is within this many degrees of the shot azimuth")
    ap.add_argument("--max", type=int, default=150)
    ap.add_argument("--interval", type=float, default=0.6, help="min seconds between requests")
    ap.add_argument("--categories", action="store_true", help="commons: also fetch the default category list")
    ap.add_argument("--category", nargs="+", help="commons: explicit category names (without 'Category:')")
    ap.add_argument("--query", nargs="+", help="openverse: explicit queries")
    ap.add_argument("--out", help=argparse.SUPPRESS)
    ap.add_argument("--art", help=argparse.SUPPRESS)
    return ap


def main(argv=None):
    a = build_parser().parse_args(argv)
    try:
        run(a)
    except rc.SourceError as e:
        sys.exit(f"error: {e}")


if __name__ == "__main__":
    main()
