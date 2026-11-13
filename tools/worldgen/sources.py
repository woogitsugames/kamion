"""Download + manifest helpers shared by ingest scripts.

Rules (ADR 0002, docs/05 §4):
  * raw files live in Data/raw/ (gitignored), manifests in Data/SourceManifests/ (committed);
  * every file is pinned by URL + SHA256; a file whose hash matches the manifest is never re-downloaded;
  * requests are sequential, identified by User-Agent, and paced (POLITE_DELAY_S);
  * a manifest is rewritten only when its content changes, so a no-op ingest leaves git clean.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import time
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_ROOT = REPO_ROOT / "Data" / "raw"
MANIFEST_DIR = REPO_ROOT / "Data" / "SourceManifests"
USER_AGENT = "truck-sim-pl-worldgen/0.1 (open-data ingest; sequential, low volume)"
POLITE_DELAY_S = 1.5
CHUNK = 1 << 20


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
    # abspath, not resolve(): Data/raw may be a junction to the main checkout (agent worktrees)
    return Path(os.path.abspath(path)).relative_to(REPO_ROOT).as_posix()


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


class Downloader:
    def __init__(self, delay_s: float = POLITE_DELAY_S, dry_run: bool = False):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = USER_AGENT
        self.delay_s = delay_s
        self.dry_run = dry_run
        self._last = 0.0
        self.stats = {"downloaded": 0, "skipped": 0, "bytes": 0}

    def _pace(self) -> None:
        wait = self._last + self.delay_s - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        self._last = time.monotonic()

    def fetch(self, url: str, dest: Path, expected_sha: str | None) -> dict:
        """Ensure `dest` holds the file at `url`. Returns a manifest file record."""
        if dest.exists() and expected_sha and sha256_of(dest) == expected_sha:
            self.stats["skipped"] += 1
            print(f"  [skip] {dest.name} (sha256 matches manifest)")
            return {"skipped": True}
        if dest.exists() and not expected_sha:
            # Present but never manifested (e.g. copied from another checkout): adopt, don't re-download.
            digest = sha256_of(dest)
            self.stats["skipped"] += 1
            print(f"  [adopt] {dest.name} sha256={digest[:12]}")
            return {"sha256": digest, "size_bytes": dest.stat().st_size, "downloaded_utc": None,
                    "note": "adopted existing local file"}
        if self.dry_run:
            print(f"  [dry-run] would download {url}")
            return {"skipped": True}
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name + ".part")
        self._pace()
        print(f"  [get] {url}")
        with self.s.get(url, stream=True, timeout=(30, 300)) as r:
            r.raise_for_status()
            with tmp.open("wb") as f:
                for chunk in r.iter_content(CHUNK):
                    f.write(chunk)
        digest = sha256_of(tmp)
        if expected_sha and digest != expected_sha:
            print(f"  [WARN] {dest.name}: server copy changed (sha256 {digest[:12]} != manifest "
                  f"{expected_sha[:12]}). Keeping new file; manifest will be updated.")
        tmp.replace(dest)
        self.stats["downloaded"] += 1
        self.stats["bytes"] += dest.stat().st_size
        return {"sha256": digest, "size_bytes": dest.stat().st_size, "downloaded_utc": now_utc()}


def load_manifest(dataset_id: str) -> dict | None:
    p = MANIFEST_DIR / f"{dataset_id}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def write_if_changed(path: Path, text: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return True


def save_manifest(manifest: dict) -> bool:
    text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    changed = write_if_changed(MANIFEST_DIR / f"{manifest['id']}.json", text)
    print(f"  manifest {manifest['id']}.json {'updated' if changed else 'unchanged'}")
    return changed


def ingest_dataset(dl: Downloader, meta: dict, files: list[dict]) -> dict:
    """Download a multi-file dataset and (re)write its manifest.

    meta  – dataset-level fields (id, name, licence, crs, ...).
    files – [{"url": ..., "name": local file name, **per-file attrs (sheet, akt_data ...)}]
    """
    ds_id = meta["id"]
    raw_dir = RAW_ROOT / meta.get("raw_subdir", f"gugik/{ds_id}")
    old = load_manifest(ds_id) or {}
    old_files = {f["url"]: f for f in old.get("files", [])}
    out_files = []
    print(f"[ingest] {ds_id}: {len(files)} file(s) -> {rel(raw_dir) if raw_dir.exists() else raw_dir}")
    for spec in sorted(files, key=lambda f: f["url"]):
        dest = raw_dir / spec["name"]
        prev = old_files.get(spec["url"], {})
        res = dl.fetch(spec["url"], dest, prev.get("sha256"))
        rec = {k: v for k, v in spec.items() if k != "name"}
        rec["local_path"] = (Path("Data/raw") / meta.get("raw_subdir", f"gugik/{ds_id}") / spec["name"]).as_posix()
        if res.get("skipped"):
            if not prev:
                continue  # dry run of a never-downloaded file
            rec.update({k: prev[k] for k in ("sha256", "size_bytes", "downloaded_utc") if k in prev})
        else:
            rec.update(res)
        out_files.append(rec)
    manifest = {**{k: v for k, v in meta.items() if k != "raw_subdir"}, "in_git": False, "files": out_files}
    # ADR 0166: a shared (per-powiat) dataset already ingested for another region with identical content is NOT
    # rewritten: its sha256 is pinned in that region's region.yaml (rewriting only "used_by" would invalidate region C).
    # The new consumer records the manifest (and its sha256) in its own region.yaml.
    if old and {k: v for k, v in old.items() if k != "used_by"} == {k: v for k, v in manifest.items() if k != "used_by"}:
        return old
    if out_files:
        save_manifest(manifest)
    return manifest
