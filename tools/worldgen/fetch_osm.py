"""Download the Geofabrik `podlaskie` OSM extract (ODbL) and record a source manifest.

Usage (from repo root):
    uv run tools/worldgen/fetch_osm.py            # download only if not cached
    uv run tools/worldgen/fetch_osm.py --force    # re-download (new snapshot)

Raw file goes to `Data/raw/osm/` (gitignored). Manifest goes to
`Data/SourceManifests/osm-geofabrik-podlaskie.json` (committed).

Policy (ADR 0002): OSM + GUGiK only. One file download from Geofabrik instead of
bulk Overpass queries (docs/05 §3: "pobieraj wycinki plikowe").
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "Data" / "raw" / "osm"
MANIFEST = REPO_ROOT / "Data" / "SourceManifests" / "osm-geofabrik-podlaskie.json"
LATEST_URL = "https://download.geofabrik.de/europe/poland/podlaskie-latest.osm.pbf"
USER_AGENT = "truck-sim-pl-worldgen/0.1 (one-off extract download; non-commercial dev)"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_dated_url() -> str:
    """Geofabrik redirects *-latest* to a dated file (podlaskie-YYMMDD.osm.pbf)."""
    r = requests.head(LATEST_URL, allow_redirects=False, timeout=30,
                      headers={"User-Agent": USER_AGENT})
    if r.status_code in (301, 302, 303, 307, 308) and "Location" in r.headers:
        return requests.compat.urljoin(LATEST_URL, r.headers["Location"])
    return LATEST_URL


def load_manifest() -> dict | None:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return None


def cached_pbf() -> Path | None:
    """Return the cached raw file if it exists and matches the manifest hash."""
    m = load_manifest()
    if not m:
        return None
    p = REPO_ROOT / m["local_path"]
    if not p.exists():
        return None
    if sha256_of(p) != m["sha256"]:
        print(f"[fetch_osm] WARNING: {p} sha256 differs from manifest", file=sys.stderr)
        return None
    return p


def download(force: bool = False) -> Path:
    if not force:
        p = cached_pbf()
        if p:
            print(f"[fetch_osm] cached: {p}")
            return p
        m = load_manifest()
        if m:
            # Manifest pins a snapshot. Try to fetch exactly that file so results reproduce.
            url = m["url"]
        else:
            url = resolve_dated_url()
    else:
        url = resolve_dated_url()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out = RAW_DIR / url.rsplit("/", 1)[-1]
    print(f"[fetch_osm] downloading {url} -> {out}")
    with requests.get(url, stream=True, timeout=120, headers={"User-Agent": USER_AGENT}) as r:
        r.raise_for_status()
        tmp = out.with_suffix(".part")
        with tmp.open("wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
        tmp.replace(out)
    digest = sha256_of(out)

    prev = load_manifest()
    if prev and prev.get("url") == url and prev.get("sha256") != digest:
        print("[fetch_osm] WARNING: same URL, different sha256 than manifest", file=sys.stderr)

    manifest = {
        "id": "osm-geofabrik-podlaskie",
        "name": "OpenStreetMap extract: województwo podlaskie (Geofabrik)",
        "url": url,
        "url_latest_alias": LATEST_URL,
        "downloaded_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "snapshot": out.stem.split("-")[-1].split(".")[0],  # YYMMDD from Geofabrik filename
        "sha256": digest,
        "size_bytes": out.stat().st_size,
        "local_path": out.relative_to(REPO_ROOT).as_posix(),
        "format": "osm.pbf",
        "crs": "EPSG:4326 (WGS84 lon/lat, OSM native); reprojected to EPSG:2180 in pipeline",
        "extent": "Województwo podlaskie (Geofabrik boundary polygon)",
        "accuracy": "Volunteered geographic information; positional accuracy not guaranteed, "
                    "tag completeness varies (see docs/reports/map/candidates.json coverage stats)",
        "license": "ODbL 1.0",
        "license_url": "https://opendatacommons.org/licenses/odbl/1-0/",
        "attribution": "© OpenStreetMap contributors",
        "provider_terms": "https://download.geofabrik.de/ (Geofabrik GmbH; data © OpenStreetMap contributors)",
        "in_git": False,
        "used_by": ["tools/worldgen/analyze_candidates.py"],
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[fetch_osm] sha256={digest} size={manifest['size_bytes']} manifest={MANIFEST}")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true", help="download the current latest snapshot")
    args = ap.parse_args()
    download(force=args.force)


if __name__ == "__main__":
    main()
