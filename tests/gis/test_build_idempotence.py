"""Idempotence: building twice gives byte-identical outputs; ingest skips files whose hash matches."""

import hashlib
import json
import subprocess
import sys

from conftest import REGION_DIR, REGION_ID, REPO, needs_raw


def _hashes():
    out = {}
    for p in sorted(REGION_DIR.iterdir()):
        if p.is_file():
            out[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def _build():
    r = subprocess.run([sys.executable, str(REPO / "tools" / "worldgen" / "build_region.py"), "--region", REGION_ID],
                       cwd=REPO, capture_output=True, text=True, timeout=900)
    assert r.returncode == 0, r.stdout + r.stderr
    return json.loads((REGION_DIR / "build_manifest.json").read_text(encoding="utf-8"))["sha256"]


@needs_raw
def test_build_twice_same_hashes():
    m1, f1 = _build(), _hashes()
    m2, f2 = _build(), _hashes()
    assert m1 == m2
    assert f1 == f2


def test_downloader_skips_matching_hash(tmp_path):
    import sources
    p = tmp_path / "a.bin"
    p.write_bytes(b"truck")
    sha = hashlib.sha256(b"truck").hexdigest()
    dl = sources.Downloader(delay_s=0)
    res = dl.fetch("https://example.invalid/never-requested", p, sha)
    assert res == {"skipped": True}
    assert dl.stats == {"downloaded": 0, "skipped": 1, "bytes": 0}


def test_write_if_changed(tmp_path):
    import sources
    p = tmp_path / "m.json"
    assert sources.write_if_changed(p, "x\n") is True
    mtime = p.stat().st_mtime_ns
    assert sources.write_if_changed(p, "x\n") is False
    assert p.stat().st_mtime_ns == mtime
