r"""Mapillary street-level reference fetcher (Graph API v4, CC BY-SA 4.0; owner decision D42, ADR 0065).

Mapillary images are REFERENCE only (pattern, framing match, colour calibration). Google imagery stays banned.
Token: env MAPILLARY_TOKEN, else %USERPROFILE%\.kamion\secrets.env line MAPILLARY_TOKEN=... (sent as an Authorization header; never logged, never in argv).

Examples (repo root):
  uv run --project tools/refs python tools/refs/mapillary_fetch.py --region bialystok-industrial-c --max 200
  uv run --project tools/refs python tools/refs/mapillary_fetch.py --region bialystok-industrial-c \
      --points Data/Regions/bialystok-industrial-c/gate3_cameras.json --radius 30 --contact-sheet
  uv run --project tools/refs python tools/refs/mapillary_fetch.py --region bialystok-industrial-c --use <image_id> --attribution
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
API = "https://graph.mapillary.com/images"
FIELDS = "id,captured_at,compass_angle,computed_geometry,creator,thumb_2048_url,is_pano,sequence"
LICENSE = "CC BY-SA 4.0"
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
MAX_TILE_DEG2 = 0.01
PAGE_LIMIT = 2000
MIN_INTERVAL_S = 0.15
USER_AGENT = "truck-sim-refs/0.1 (offline reference tooling)"

SECRETS_ENV = Path(os.environ.get("USERPROFILE") or Path.home()) / ".kamion" / "secrets.env"

TOKEN_HELP = (
    "MAPILLARY_TOKEN not found (environment variable or secrets file).\n"
    "Owner action: create a free Mapillary developer app at https://www.mapillary.com/dashboard/developers,\n"
    "copy its 'Client Token' (starts with MLY|) and add this line to %USERPROFILE%/.kamion/secrets.env\n"
    "(outside the repo; typically C:/Users/<you>/.kamion/secrets.env):\n"
    "    MAPILLARY_TOKEN=<token>\n"
    "Alternatively set the environment variable MAPILLARY_TOKEN (it takes precedence).\n"
    "The token is never written to the repo, logs, manifests or arguments."
)


def read_secrets_env(path: Path) -> dict:
    """Minimal KEY=VALUE parser: skips blank lines and # comments, strips optional quotes."""
    out = {}
    try:
        text = Path(path).read_text(encoding="utf-8-sig")
    except OSError:
        return out
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        out[k] = v
    return out


def resolve_token(env=None, secrets_path: Path | None = None) -> str:
    """Environment variable first, then secrets.env; empty string = no token."""
    env = os.environ if env is None else env
    tok = (env.get("MAPILLARY_TOKEN") or "").strip()
    if tok:
        return tok
    return (read_secrets_env(secrets_path or SECRETS_ENV).get("MAPILLARY_TOKEN") or "").strip()


class MapillaryError(RuntimeError):
    pass


# ---------------------------------------------------------------- geometry

def haversine_m(lon1, lat1, lon2, lat2) -> float:
    r = 6371008.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def angle_diff(a: float, b: float) -> float:
    d = (a - b) % 360.0
    return min(d, 360.0 - d)


def bbox_around(lon, lat, radius_m):
    dlat = radius_m / 111320.0
    dlon = radius_m / (111320.0 * math.cos(math.radians(lat)))
    return (lon - dlon, lat - dlat, lon + dlon, lat + dlat)


def tile_bbox(bbox, max_area=MAX_TILE_DEG2):
    """Split (minlon, minlat, maxlon, maxlat) into a grid of tiles, each <= max_area deg^2."""
    x0, y0, x1, y1 = bbox
    w, h = x1 - x0, y1 - y0
    n = 1 if w * h <= max_area else math.ceil(math.sqrt(w * h / max_area))
    return [
        (x0 + w * i / n, y0 + h * j / n, x0 + w * (i + 1) / n, y0 + h * (j + 1) / n)
        for i in range(n)
        for j in range(n)
    ]


# ---------------------------------------------------------------- inputs

def _region_yaml(region_id: str) -> dict:
    import yaml
    f = REPO / "Data" / "Regions" / region_id / "region.yaml"
    if not f.exists():
        raise SystemExit(f"region data not found: {f}")
    return yaml.safe_load(f.read_text(encoding="utf-8"))


def region_bbox_lonlat(region_id: str):
    from pyproj import Transformer
    b = _region_yaml(region_id)["bbox"]
    t = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
    xs, ys = [], []
    for x, y in ((b["xmin"], b["ymin"]), (b["xmax"], b["ymin"]), (b["xmin"], b["ymax"]), (b["xmax"], b["ymax"])):
        lon, lat = t.transform(x, y)
        xs.append(lon)
        ys.append(lat)
    return (min(xs), min(ys), max(xs), max(ys))


def load_points(path: Path, region_id: str):
    """Cameras from gate3_cameras.json -> [{id, lon, lat, azimuth}].

    Camera pos/look_at are local E,N,U = EPSG:2180 minus the region origin (ADR 0003).
    """
    from pyproj import Transformer
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    o = _region_yaml(region_id)["origin"]
    t = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
    out = []
    for c in data["cameras"]:
        e, n = c["pos"][0], c["pos"][1]
        le, ln = c["look_at"][0], c["look_at"][1]
        if (le, ln) == (e, n):
            continue
        az = math.degrees(math.atan2(le - e, ln - n)) % 360.0
        lon, lat = t.transform(o["x"] + e, o["y"] + n)
        out.append({"id": c["id"], "lon": lon, "lat": lat, "azimuth": az})
    return out


# ---------------------------------------------------------------- client

def _strip_query_param(url: str, name: str) -> str:
    from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
    s = urlsplit(url)
    q = [(k, v) for k, v in parse_qsl(s.query, keep_blank_values=True) if k != name]
    return urlunsplit((s.scheme, s.netloc, s.path, urlencode(q), s.fragment))


class MapillaryClient:
    def __init__(self, token: str, session=None, cache_dir: Path | None = None, sleep=time.sleep, retries=5):
        if not token:
            raise MapillaryError(TOKEN_HELP)
        if session is None:
            import requests
            session = requests.Session()
        self._token = token
        self.session = session
        self.cache_dir = cache_dir
        self._sleep = sleep
        self.retries = retries
        self._last = 0.0
        self.requests_made = 0

    def _get(self, url, params=None, auth=True):
        headers = {"User-Agent": USER_AGENT}
        if auth:
            headers["Authorization"] = f"OAuth {self._token}"
        delay = 1.0
        for attempt in range(self.retries + 1):
            wait = MIN_INTERVAL_S - (time.monotonic() - self._last)
            if wait > 0:
                self._sleep(wait)
            self._last = time.monotonic()
            self.requests_made += 1
            r = self.session.get(url, params=params, headers=headers, timeout=60)
            code = r.status_code
            if code in (401, 403):
                raise MapillaryError(f"Mapillary rejected the token (HTTP {code}); check MAPILLARY_TOKEN.")
            if code == 429 or code >= 500:
                if attempt == self.retries:
                    raise MapillaryError(f"HTTP {code} after {self.retries} retries")
                ra = (getattr(r, "headers", None) or {}).get("Retry-After")
                self._sleep(float(ra) if ra and str(ra).isdigit() else delay)
                delay = min(delay * 2, 60.0)
                continue
            if code != 200:
                raise MapillaryError(f"HTTP {code} from {url.split('?')[0]}")
            return r
        raise MapillaryError("unreachable")

    def images_in_bbox(self, bbox):
        """All image records in a bbox (<= MAX_TILE_DEG2), cached on disk by bbox hash."""
        key = hashlib.sha256(json.dumps([round(v, 6) for v in bbox]).encode()).hexdigest()[:16]
        cf = self.cache_dir / f"bbox_{key}.json" if self.cache_dir else None
        if cf and cf.exists():
            return json.loads(cf.read_text(encoding="utf-8"))
        params = {"bbox": ",".join(f"{v:.6f}" for v in bbox), "fields": FIELDS, "limit": PAGE_LIMIT}
        recs, url = [], API
        while url:
            body = self._get(url, params=params).json()
            recs.extend(body.get("data", []))
            url = (body.get("paging") or {}).get("next")
            params = None  # `next` already carries the query
            if url:
                url = _strip_query_param(url, "access_token")  # token travels in the header only
        recs.sort(key=lambda r: str(r.get("id")))
        if cf:
            cf.parent.mkdir(parents=True, exist_ok=True)
            cf.write_text(json.dumps(recs, ensure_ascii=False), encoding="utf-8")
        return recs

    def download(self, url, dest: Path) -> str:
        data = self._get(url, auth=False).content
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(".part")
        tmp.write_bytes(data)
        tmp.replace(dest)
        return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------- selection

def record_lonlat(rec):
    c = (rec.get("computed_geometry") or {}).get("coordinates")
    return (c[0], c[1]) if c and len(c) >= 2 else None


def select_for_camera(records, cam, radius_m=30.0, max_dev_deg=40.0, per_camera=3, allow_pano=False):
    """Nearest images with a similar viewing azimuth; deterministic order (distance, then id)."""
    cand = []
    for r in records:
        pano = bool(r.get("is_pano"))
        if pano and not allow_pano:
            continue
        ll = record_lonlat(r)
        if ll is None or not r.get("thumb_2048_url"):
            continue
        d = haversine_m(cam["lon"], cam["lat"], ll[0], ll[1])
        if d > radius_m:
            continue
        if not pano:
            ca = r.get("compass_angle")
            if ca is None or angle_diff(float(ca), cam["azimuth"]) > max_dev_deg:
                continue
        cand.append((d, str(r["id"]), r))
    cand.sort(key=lambda t: (t[0], t[1]))
    return [(d, r) for d, _, r in cand[:per_camera]]


# ---------------------------------------------------------------- manifest

def load_manifest(path: Path):
    out = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                e = json.loads(line)
                out[e["id"]] = e
    return out


def write_manifest(path: Path, entries: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        for k in sorted(entries):
            f.write(json.dumps(entries[k], ensure_ascii=False, sort_keys=True) + "\n")
    tmp.replace(path)


def make_entry(rec, sha, cameras, now=None):
    iid = str(rec["id"])
    cb = rec.get("creator") or {}
    ll = record_lonlat(rec)
    ts = rec.get("captured_at")
    cap = datetime.fromtimestamp(ts / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d") if isinstance(ts, (int, float)) else None
    return {
        "id": iid,
        "page_url": f"https://www.mapillary.com/app/?pKey={iid}",
        "author": cb.get("username"),
        "author_id": cb.get("id"),
        "captured_at": cap,
        "captured_at_ms": ts,
        "compass_angle": rec.get("compass_angle"),
        "lon": ll[0] if ll else None,
        "lat": ll[1] if ll else None,
        "is_pano": bool(rec.get("is_pano")),
        "sequence": rec.get("sequence"),
        "file": f"{iid}.jpg",
        "sha256": sha,
        "license": LICENSE,
        "license_url": LICENSE_URL,
        "source": "Mapillary Graph API v4 (thumb_2048_url)",
        "game_cameras": sorted(cameras),
        "fetched_at": (now or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


# ---------------------------------------------------------------- contact sheets

def latest_game_frame(camera_id: str, root: Path | None = None):
    """Newest artifacts/gate3/<ts>/<serial>/cam/<id>.png (by mtime; the phone serial is not hard-coded)."""
    root = root or REPO / "artifacts" / "gate3"
    if not root.is_dir():
        return None
    hits = sorted(root.glob(f"*/*/cam/{camera_id}.png"), key=lambda p: (p.stat().st_mtime, str(p)))
    return hits[-1] if hits else None


def make_sheet(entry, photo: Path, frame: Path | None, out: Path, height=720):
    from PIL import Image, ImageDraw, ImageFont
    imgs = []
    for p in (photo, frame):
        if p and Path(p).exists():
            im = Image.open(p).convert("RGB")
            imgs.append(im.resize((max(1, round(im.width * height / im.height)), height)))
    bar = 44
    width = sum(i.width for i in imgs) + 8 * max(0, len(imgs) - 1)
    sheet = Image.new("RGB", (max(width, 640), height + bar), (24, 24, 24))
    x = 0
    for i in imgs:
        sheet.paste(i, (x, 0))
        x += i.width + 8
    d = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    d.text((6, height + 6), f"Mapillary {entry['id']}  (c) {entry.get('author')}  {entry.get('captured_at')}  {LICENSE}",
           fill=(235, 235, 235), font=font)
    d.text((6, height + 24), "left: Mapillary reference" + ("   right: game frame" if len(imgs) > 1 else "   (no game frame in artifacts/gate3)"),
           fill=(170, 170, 170), font=font)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, "JPEG", quality=88)
    return out


# ---------------------------------------------------------------- attribution

def write_attribution(region_id: str, entries: dict, used_ids, out: Path):
    used = [entries[i] for i in sorted(used_ids) if i in entries]
    missing = sorted(set(used_ids) - set(entries))
    lines = [
        "# Atrybucja: Mapillary (CC BY-SA 4.0)",
        "",
        f"Generowane przez `tools/refs/mapillary_fetch.py --attribution` (nie edytuj ręcznie). Region: `{region_id}`.",
        "",
        "Zdjęcia Mapillary służą jako REFERENCJA (wzór, dopasowanie kadru, kalibracja koloru). Pikseli nie ma w buildzie.",
        f"Gdyby kiedykolwiek piksele trafiły do tekstury, pochodna jest CC BY-SA 4.0 (ADR 0065). Licencja: {LICENSE_URL}",
        "",
        "| Zdjęcie | Autor | Data | Kamera gry | Licencja |",
        "|---|---|---|---|---|",
    ]
    for e in used:
        cams = ", ".join(e.get("game_cameras") or []) or "-"
        lines.append(f"| [{e['id']}]({e['page_url']}) | {e.get('author')} | {e.get('captured_at')} | {cams} | {LICENSE} |")
    if not used:
        lines.append("| (brak użytych zdjęć) | | | | |")
    if missing:
        lines += ["", "UWAGA: oznaczone jako użyte, ale nieobecne w manifeście: " + ", ".join(missing)]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return out


# ---------------------------------------------------------------- orchestration

def run(args, client=None, now=None):
    region = args.region or "custom"
    outdir = Path(args.out) if args.out else REPO / "Data" / "raw" / "mapillary" / region
    manifest_path = outdir / "manifest.jsonl"
    entries = load_manifest(manifest_path)
    used_file = Path(args.used_file) if args.used_file else REPO / "Data" / "Regions" / region / "mapillary_used.json"
    sheets_dir = Path(args.sheets_dir) if args.sheets_dir else REPO / "artifacts" / "refs" / "mapillary" / region
    attrib_out = Path(args.attribution_out) if args.attribution_out else REPO / "docs" / "ATTRIBUTION-mapillary.md"

    if args.use:
        used = set(json.loads(used_file.read_text(encoding="utf-8"))) if used_file.exists() else set()
        used |= set(args.use)
        used_file.parent.mkdir(parents=True, exist_ok=True)
        used_file.write_text(json.dumps(sorted(used), indent=1) + "\n", encoding="utf-8")

    offline_only = (args.attribution or args.use or args.contact_sheet_only) and not args.fetch
    if not offline_only:
        if client is None:
            token = resolve_token()
            if not token:
                raise SystemExit(TOKEN_HELP)
            client = MapillaryClient(token, cache_dir=outdir / ".cache")
        if args.bbox:
            region_box = tuple(args.bbox)
        elif args.region:
            region_box = region_bbox_lonlat(args.region)
        else:
            raise SystemExit("give --region or --bbox MINLON MINLAT MAXLON MAXLAT")

        chosen = {}  # id -> (record, set(cameras))
        if args.points:
            for cam in load_points(Path(args.points), args.region):
                recs = []
                for tb in tile_bbox(bbox_around(cam["lon"], cam["lat"], args.radius)):
                    recs += client.images_in_bbox(tb)
                for _, r in select_for_camera(recs, cam, args.radius, args.azimuth_tol, args.per_camera, args.pano):
                    chosen.setdefault(str(r["id"]), (r, set()))[1].add(cam["id"])
        else:
            for tb in tile_bbox(region_box):
                for r in client.images_in_bbox(tb):
                    if (r.get("is_pano") and not args.pano) or not r.get("thumb_2048_url"):
                        continue
                    chosen.setdefault(str(r["id"]), (r, set()))
        ordered = sorted(chosen.items(), key=lambda kv: (-(kv[1][0].get("captured_at") or 0), kv[0]))
        chosen = dict(ordered[: args.max])

        n_new = 0
        for iid, (rec, cams) in sorted(chosen.items()):
            dest = outdir / f"{iid}.jpg"
            old = entries.get(iid)
            if old and dest.exists():
                old["game_cameras"] = sorted(set(old.get("game_cameras", [])) | cams)
                continue
            sha = client.download(rec["thumb_2048_url"], dest)
            entries[iid] = make_entry(rec, sha, cams, now)
            n_new += 1
        write_manifest(manifest_path, entries)
        print(f"selected {len(chosen)} images, downloaded {n_new} new, api requests {client.requests_made}; manifest {manifest_path}")

    if args.contact_sheet or args.contact_sheet_only:
        by_cam = {}
        for e in entries.values():
            for c in e.get("game_cameras", []):
                by_cam.setdefault(c, []).append(e)
        for cam, es in sorted(by_cam.items()):
            es.sort(key=lambda e: e["id"])
            make_sheet(es[0], outdir / es[0]["file"], latest_game_frame(cam), sheets_dir / f"sheet_{cam}.jpg")
        print(f"contact sheets: {len(by_cam)} -> {sheets_dir}")

    if args.attribution:
        used = set(json.loads(used_file.read_text(encoding="utf-8"))) if used_file.exists() else set()
        write_attribution(region, entries, used, attrib_out)
        print(f"attribution: {len(used)} used images -> {attrib_out}")
    return entries


def build_parser():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--region", help="region id (bbox from Data/Regions/<id>/region.yaml)")
    ap.add_argument("--bbox", nargs=4, type=float, metavar=("MINLON", "MINLAT", "MAXLON", "MAXLAT"))
    ap.add_argument("--points", help="camera file (gate3_cameras.json style: cameras[].pos/look_at); needs --region")
    ap.add_argument("--radius", type=float, default=30.0, help="metres around each camera (default 30)")
    ap.add_argument("--azimuth-tol", type=float, default=40.0, help="compass_angle tolerance in deg (default 40)")
    ap.add_argument("--per-camera", type=int, default=3)
    ap.add_argument("--max", type=int, default=200, help="max images to fetch (default 200)")
    ap.add_argument("--pano", action="store_true", help="include panoramas (skipped by default)")
    ap.add_argument("--out", help="output dir (default Data/raw/mapillary/<region>)")
    ap.add_argument("--fetch", action="store_true", help="fetch even when combined with --attribution/--use")
    ap.add_argument("--contact-sheet", action="store_true", help="after fetching, build sheet_<camera>.jpg in artifacts/refs/mapillary/<region>/")
    ap.add_argument("--contact-sheet-only", action="store_true", help="rebuild sheets from the existing manifest (no token needed)")
    ap.add_argument("--use", nargs="+", metavar="IMAGE_ID", help="mark images as actually used (Data/Regions/<id>/mapillary_used.json)")
    ap.add_argument("--attribution", action="store_true", help="write docs/ATTRIBUTION-mapillary.md for images marked used")
    ap.add_argument("--attribution-out", help=argparse.SUPPRESS)
    ap.add_argument("--used-file", help=argparse.SUPPRESS)
    ap.add_argument("--sheets-dir", help=argparse.SUPPRESS)
    return ap


def main(argv=None):
    a = build_parser().parse_args(argv)
    if a.points and not a.region:
        sys.exit("error: --points needs --region (camera positions are relative to the region origin)")
    try:
        run(a)
    except MapillaryError as e:
        sys.exit(f"error: {e}")


if __name__ == "__main__":
    main()
