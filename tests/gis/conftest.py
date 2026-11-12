"""pytest setup for GIS pipeline tests.

Run from repo root:
    uv run --project tools/worldgen pytest tests/gis -q

Tests that need raw data (Data/raw/, gitignored) are skipped when it is missing; run
`tools/worldgen/ingest.py --region bialystok-industrial-c` first to enable them.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))

REGION_ID = "bialystok-industrial-c"
REGION_DIR = REPO / "Data" / "Regions" / REGION_ID


@pytest.fixture(scope="session")
def region():
    import regions
    return regions.get(REGION_ID)


@pytest.fixture(scope="session")
def graph():
    p = REGION_DIR / "roads.graph.json"
    if not p.exists():
        pytest.skip("roads.graph.json not built")
    return json.loads(p.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def buildings_fc():
    p = REGION_DIR / "buildings.geojson"
    if not p.exists():
        pytest.skip("buildings.geojson not built")
    return json.loads(p.read_text(encoding="utf-8"))


def raw_available() -> bool:
    import sources
    for ds in ("gugik-nmt-2025-" + REGION_ID, "gugik-bdot10k-2061", "gugik-lod1-2024-2061", "gugik-lod2-2017-2061",
               "osm-geofabrik-podlaskie"):
        m = sources.load_manifest(ds)
        if not m:
            return False
        files = m.get("files") or [{"local_path": m.get("local_path")}]
        if not all((REPO / f["local_path"]).exists() for f in files):
            return False
    return True


needs_raw = pytest.mark.skipif(not raw_available(), reason="raw data not ingested (Data/raw is gitignored)")


LFS_POINTER_MAGIC = b"version https://git-lfs.github.com/spec/v1"


def is_lfs_pointer(path) -> bool:
    """True when a tracked binary file is only a git-lfs pointer (CI checks out with lfs: false)."""
    try:
        with Path(path).open("rb") as fh:
            return fh.read(len(LFS_POINTER_MAGIC)) == LFS_POINTER_MAGIC
    except OSError:
        return False


def require_lfs(*paths) -> None:
    """Skip the test when any given file is a git-lfs pointer instead of the real binary.

    CI runs with lfs: false (LFS transfer budget), so tracked binaries (.glb, .png, ...) are
    pointer files there; tests that read their bytes must skip, not fail. Locally, with real
    LFS content pulled, the tests run unchanged.
    """
    for path in paths:
        if is_lfs_pointer(path):
            pytest.skip(f"{path} is a git-lfs pointer, not the real file (checkout without lfs)")


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "unit: fast pure-function unit tests on small synthetic data; run in CI without Data/raw "
        "(`pytest tests/gis -m unit`)",
    )
