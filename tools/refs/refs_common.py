r"""Shared building blocks for the open reference sources (D43, ADR 0066).

Every image source (KartaView, Panoramax, Wikimedia Commons, Openverse) plugs a `candidates()` function into
`fetch_for_points()`; this module provides the rest: polite HTTP (rate limit, retry/backoff, on-disk JSON cache,
no secrets), licence policy, per-source manifest.jsonl (URL, author, licence, date, SHA256), per-shot montages.

Google Maps / Street View / Earth / 3D Tiles (also via Gemini) are banned; none of the sources here touch Google.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RAW_ROOT = REPO / "Data" / "raw" / "refs"
ART_ROOT = REPO / "artifacts" / "refs"
PHOTO_LIST = REPO / "docs" / "owner" / "PHOTO-LIST.md"
USER_AGENT = "truck-sim-refs/0.2 (offline reference tooling; open-licence street references)"

# ---------------------------------------------------------------- licence policy (ADR 0066)

# normalised licence key -> (label, canonical URL)
LICENSES = {
    "cc0": ("CC0 1.0", "https://creativecommons.org/publicdomain/zero/1.0/"),
    "pdm": ("Public Domain Mark", "https://creativecommons.org/publicdomain/mark/1.0/"),
    "by": ("CC BY", "https://creativecommons.org/licenses/by/4.0/"),
    "by-sa": ("CC BY-SA", "https://creativecommons.org/licenses/by-sa/4.0/"),
}
# usage class: texture = pixels may become game textures (attribution for BY); reference = pattern/framing only,
# BY-SA needs an explicit owner decision before any pixel use (share-alike), see ADR 0066.
TEXTURE_OK = {"cc0", "pdm", "by"}
REFERENCE_ONLY = {"by-sa"}


def normalize_license(text: str | None) -> str | None:
    """Map free-form licence strings (Commons 'CC BY-SA 4.0', Openverse 'by-sa', Panoramax 'CC-BY-SA-4.0',
    'Public domain', 'CC0') to cc0/pdm/by/by-sa, or None when the licence is NC/ND/unknown/all-rights-reserved."""
    if not text:
        return None
    t = re.sub(r"[\s_\-]+", " ", str(text).strip().lower())
    if re.search(r"\b(nc|nd)\b|non ?commercial|no ?deriv|all rights|copyright", t):
        return None
    if "cc0" in t or "zero" in t or t in ("cc 0",):
        return "cc0"
    if "public domain" in t or t in ("pd", "pdm") or t.startswith("pd ") or "pdm" in t or "no known copyright" in t:
        return "pdm"
    if re.search(r"\bby sa\b|\bbysa\b|share ?alike", t):
        return "by-sa"
    if re.fullmatch(r"(cc )?by( \d(\.\d)?)?( .*)?", t) or t.startswith("cc by"):
        return "by"
    return None


def usage_class(lic_key: str | None) -> str:
    if lic_key in TEXTURE_OK:
        return "texture_ok"
    if lic_key in REFERENCE_ONLY:
        return "reference_only_owner_decision_for_pixels"
    return "rejected"


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


# ---------------------------------------------------------------- route points

_ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*([^|]*?)\s*\|\s*(.*?)<br>`\s*(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)\s*`\s*\(s=(\d+)\s*m\)\s*\|([^|]*)\|")


def parse_photo_list(path: Path = PHOTO_LIST):
    """55 shots of the starting route from docs/owner/PHOTO-LIST.md -> [{nr, type, place, lat, lon, s_m, azimuth}]."""
    out = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        m = _ROW.match(line)
        if not m:
            continue
        az = re.search(r"azymut\s+(\d+)", m.group(7))
        out.append({
            "nr": int(m.group(1)),
            "type": re.sub(r"\*\*.*?\*\*", "", m.group(2)).strip(),
            "place": m.group(3).strip(),
            "lat": float(m.group(4)),
            "lon": float(m.group(5)),
            "s_m": int(m.group(6)),
            "azimuth": float(az.group(1)) if az else None,
        })
    return out


def weak_shots(coverage_path: Path | None = None):
    """Shot numbers rated SŁABE/BRAK in artifacts/refs/coverage.json (Mapillary agent), or None when absent.
    Accepts {"<nr>": "SŁABE"|...} or a list of {"nr"/"shot": n, "status"/"rating": ...}."""
    p = coverage_path or ART_ROOT / "coverage.json"
    if not p.exists():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    rows = data.get("shots", data) if isinstance(data, dict) else data
    if isinstance(rows, dict):
        rows = [{"nr": k, "status": (v.get("status") if isinstance(v, dict) else v)} for k, v in rows.items()]
    weak = set()
    for r in rows:
        st = str(r.get("status") or r.get("rating") or r.get("coverage") or "").upper()
        nr = r.get("nr", r.get("shot"))
        if nr is not None and any(k in st for k in ("SŁAB", "SLAB", "BRAK", "WEAK", "NONE", "MISSING")):
            weak.add(int(nr))
    return weak


# ---------------------------------------------------------------- HTTP

class SourceError(RuntimeError):
    pass


class Http:
    """Polite GET client: min interval, Retry-After/backoff on 429/5xx, JSON cache keyed by URL+params.
    `session` and `sleep` are injectable so tests never touch the network."""

    def __init__(self, cache_dir: Path | None = None, session=None, sleep=time.sleep, min_interval=0.5,
                 retries=4, headers=None):
        if session is None:
            import requests
            session = requests.Session()
        self.session, self.cache_dir, self._sleep = session, cache_dir, sleep
        self.min_interval, self.retries = min_interval, retries
        self.headers = {"User-Agent": USER_AGENT, **(headers or {})}
        self._last = 0.0
        self.requests_made = 0

    def _key(self, url, params):
        raw = url + "?" + json.dumps(params or {}, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:20]

    def _get(self, url, params=None, headers=None, data=None):
        delay = 1.0
        for attempt in range(self.retries + 1):
            wait = self.min_interval - (time.monotonic() - self._last)
            if wait > 0:
                self._sleep(wait)
            self._last = time.monotonic()
            self.requests_made += 1
            h = {**self.headers, **(headers or {})}
            if data is not None:
                r = self.session.post(url, data=data, headers=h, timeout=90)
            else:
                r = self.session.get(url, params=params, headers=h, timeout=90)
            code = r.status_code
            if code == 429 or code >= 500:
                if attempt == self.retries:
                    raise SourceError(f"HTTP {code} after {self.retries} retries: {url.split('?')[0]}")
                ra = (getattr(r, "headers", None) or {}).get("Retry-After")
                self._sleep(float(ra) if ra and str(ra).isdigit() else delay)
                delay = min(delay * 2, 60.0)
                continue
            if code != 200:
                raise SourceError(f"HTTP {code} from {url.split('?')[0]}")
            return r
        raise SourceError("unreachable")

    def get_json(self, url, params=None, headers=None):
        cf = self.cache_dir / f"{self._key(url, params)}.json" if self.cache_dir else None
        if cf and cf.exists():
            return json.loads(cf.read_text(encoding="utf-8"))
        body = self._get(url, params, headers).json()
        if cf:
            cf.parent.mkdir(parents=True, exist_ok=True)
            cf.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")
        return body

    def post_json(self, url, data):
        cf = self.cache_dir / f"{self._key(url, data)}.json" if self.cache_dir else None
        if cf and cf.exists():
            return json.loads(cf.read_text(encoding="utf-8"))
        body = self._get(url, data=data).json()
        if cf:
            cf.parent.mkdir(parents=True, exist_ok=True)
            cf.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")
        return body

    def download(self, url, dest: Path, params=None) -> tuple[str, int]:
        data = self._get(url, params).content
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".part")
        tmp.write_bytes(data)
        tmp.replace(dest)
        return hashlib.sha256(data).hexdigest(), len(data)


# ---------------------------------------------------------------- manifest

def load_manifest(path: Path):
    out = {}
    if Path(path).exists():
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                e = json.loads(line)
                out[e["id"]] = e
    return out


def write_manifest(path: Path, entries: dict):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        for k in sorted(entries):
            f.write(json.dumps(entries[k], ensure_ascii=False, sort_keys=True) + "\n")
    tmp.replace(path)


def make_entry(source, cand, lic_key, sha, size, shots, now=None):
    label, url = LICENSES[lic_key]
    return {
        "id": str(cand["id"]),
        "source": source,
        "title": cand.get("title"),
        "page_url": cand.get("page_url"),
        "file_url": cand.get("file_url"),
        "author": cand.get("author"),
        "captured_at": cand.get("date"),
        "lon": cand.get("lon"),
        "lat": cand.get("lat"),
        "heading": cand.get("heading"),
        "license": cand.get("license_label") or cand.get("license") or label,
        "license_key": lic_key,
        "license_url": cand.get("license_url") or url,
        "usage": usage_class(lic_key),
        "file": cand["file"],
        "sha256": sha,
        "size_bytes": size,
        "shots": sorted(shots),
        "distance_m": cand.get("distance_m"),
        "fetched_at": (now or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def safe_name(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", s).strip("_")[:120]


# ---------------------------------------------------------------- pipeline

def adopt_or_download(http, cand, dest: Path, log, source, stats=None):
    """File already on disk but not in the manifest (killed run): hash it instead of downloading again."""
    if Path(dest).exists() and Path(dest).stat().st_size > 0:
        data = Path(dest).read_bytes()
        return hashlib.sha256(data).hexdigest(), len(data)
    try:
        return http.download(cand["file_url"], dest)
    except SourceError as e:
        if stats is not None:
            stats["failed"] = stats.get("failed", 0) + 1
        log(f"[{source}] skip {cand['id']}: {e}")
        return None, 0


def fetch_for_points(source, points, candidates_fn, http, outdir: Path, per_point=3, max_total=150,
                     azimuth_tol=None, now=None, log=print):
    """For each shot: candidates -> licence gate -> nearest/best `per_point` -> download once -> manifest.

    candidates_fn(point, http) -> [cand] with id, lat, lon, heading, date, author, license (raw text), license_url,
    page_url, file_url, ext, title. Rejected licences are counted and never downloaded."""
    outdir = Path(outdir)
    manifest_path = outdir / "manifest.jsonl"
    entries = load_manifest(manifest_path)
    stats = {"candidates": 0, "rejected_license": 0, "downloaded": 0, "points_with_hits": 0}
    chosen = {}  # id -> (cand, lic_key, set(shots))
    for p in points:
        cands = candidates_fn(p, http)
        good = []
        for c in cands:
            stats["candidates"] += 1
            key = normalize_license(c.get("license"))
            if key is None:
                stats["rejected_license"] += 1
                continue
            if azimuth_tol is not None and p.get("azimuth") is not None and c.get("heading") is not None:
                if angle_diff(float(c["heading"]), p["azimuth"]) > azimuth_tol:
                    continue
            if c.get("lat") is not None and c.get("lon") is not None:
                c["distance_m"] = round(haversine_m(p["lon"], p["lat"], c["lon"], c["lat"]), 1)
            good.append((c.get("distance_m", 0.0), str(c["id"]), c, key))
        good.sort(key=lambda t: (t[0], t[1]))
        if good:
            stats["points_with_hits"] += 1
        for _, cid, c, key in good[:per_point]:
            chosen.setdefault(cid, (c, key, set()))[2].add(p["nr"])
    for cid, (c, key, shots) in sorted(chosen.items())[:max_total]:
        c["file"] = f"{safe_name(cid)}{c.get('ext', '.jpg')}"
        dest = outdir / c["file"]
        old = entries.get(cid)
        if old and dest.exists():
            old["shots"] = sorted(set(old.get("shots", [])) | shots)
            continue
        sha, size = adopt_or_download(http, c, dest, log, source, stats)
        if sha is None:
            continue
        entries[cid] = make_entry(source, c, key, sha, size, shots, now)
        stats["downloaded"] += 1
        if stats["downloaded"] % 10 == 0:
            write_manifest(manifest_path, entries)  # survive a killed run
    write_manifest(manifest_path, entries)
    log(f"[{source}] candidates {stats['candidates']}, licence-rejected {stats['rejected_license']}, "
        f"new downloads {stats['downloaded']}, shots with hits {stats['points_with_hits']}/{len(points)}, "
        f"requests {http.requests_made}; manifest {manifest_path}")
    return entries, stats


# ---------------------------------------------------------------- montages

def make_montage(source, shot, entries, raw_dir: Path, out: Path, max_tiles=6, tile_h=360):
    """Contact sheet for one shot: up to 6 thumbs with id/author/licence captions (view downscaled, <= 800 px wide)."""
    from PIL import Image, ImageDraw, ImageFont
    tiles = []
    for e in entries[:max_tiles]:
        f = Path(raw_dir) / e["file"]
        if not f.exists():
            continue
        try:
            im = Image.open(f).convert("RGB")
        except Exception:
            continue
        im = im.resize((max(1, round(im.width * tile_h / im.height)), tile_h))
        tiles.append((im, e))
    if not tiles:
        return None
    cols = 3 if len(tiles) > 2 else len(tiles)
    rows = math.ceil(len(tiles) / cols)
    cw = max(t[0].width for t in tiles)
    cap = 34
    sheet = Image.new("RGB", (cols * (cw + 6) + 6, rows * (tile_h + cap + 6) + 6 + 26), (24, 24, 24))
    d = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    d.text((6, 6), f"{source}  shot {shot.get('nr')}  {shot.get('type', '')}  {str(shot.get('place', ''))[:70]}", fill=(235, 235, 235), font=font)
    for i, (im, e) in enumerate(tiles):
        x, y = 6 + (i % cols) * (cw + 6), 26 + 6 + (i // cols) * (tile_h + cap + 6)
        sheet.paste(im, (x, y))
        d.text((x, y + tile_h + 3), f"{e['id'][:22]} {e.get('captured_at') or ''} {e.get('license')}", fill=(200, 200, 200), font=font)
        d.text((x, y + tile_h + 17), f"(c) {str(e.get('author'))[:40]}", fill=(150, 150, 150), font=font)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, "JPEG", quality=85)
    return out


def montages_for(source, points, entries: dict, raw_dir: Path, art_dir: Path):
    n = 0
    for p in points:
        es = sorted((e for e in entries.values() if p["nr"] in e.get("shots", [])), key=lambda e: (e.get("distance_m") or 0, e["id"]))
        if es and make_montage(source, p, es, raw_dir, Path(art_dir) / f"shot_{p['nr']:02d}.jpg"):
            n += 1
    return n


def coverage_row(points, entries: dict):
    """{shot nr: number of images} for the report."""
    return {p["nr"]: sum(1 for e in entries.values() if p["nr"] in e.get("shots", [])) for p in points}
