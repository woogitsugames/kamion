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


@pytest.fixture(scope="session")
def piers_check():
    """(report, world) of tools/worldgen/qa/check_piers_vs_roads.py for the default region: the road stage of the
    generator on a flat ground model. No Data/raw, no Unity; about 100 s, once per session (ADR 0198 / 0226)."""
    sys.path.insert(0, str(REPO / "tools" / "worldgen" / "qa"))
    import check_piers_vs_roads as K
    return K.check(REGION_ID)


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


def _lfs_required(path) -> bool:
    """True when `path` matches KAMION_LFS_REQUIRED (comma-separated repo-relative globs, the same list CI gives to
    `git lfs pull --include`). There a pointer means the pull failed or the list is out of date: fail, do not skip."""
    import fnmatch
    import os
    globs = [g.strip() for g in os.environ.get("KAMION_LFS_REQUIRED", "").split(",") if g.strip()]
    try:
        rel = Path(path).resolve().relative_to(REPO).as_posix()
    except ValueError:
        return False
    return any(fnmatch.fnmatch(rel, g) for g in globs)


def require_lfs(*paths) -> None:
    """Skip the test when any given file is a git-lfs pointer instead of the real binary.

    CI checks out with lfs: false (LFS transfer budget) and then pulls only the ~18 MB the gis tests read
    (`.github/workflows/ci.yml`, job gis, LFS_GIS); everything else stays a pointer there and tests reading it
    skip. For paths in KAMION_LFS_REQUIRED a pointer is a failure. Locally, with LFS pulled, tests run unchanged.
    """
    for path in paths:
        if is_lfs_pointer(path):
            if _lfs_required(path):
                pytest.fail(f"plik LFS miał być pobrany w CI (KAMION_LFS_REQUIRED), a jest wskaźnikiem: {path}")
            pytest.skip(f"plik LFS niepobrany (wskaźnik): {path} - run `git lfs pull --include <path>`")


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "unit: fast pure-function unit tests on small synthetic data; run in CI without Data/raw "
        "(`pytest tests/gis -m unit`)",
    )


@pytest.fixture
def measured_widths(monkeypatch):
    """D94 / ADR 0306: the network with the MEASURED cross-sections (GAMEPLAY_LANE_WIDEN_M = 0) for tests that compare
    the generator with the orthophoto / BDOT / authored measurements."""
    import sys as _sys
    from pathlib import Path as _P
    _sys.path.insert(0, str(_P(__file__).resolve().parents[2] / "tools" / "worldgen"))
    from roads import standards as _S
    monkeypatch.setattr(_S, "GAMEPLAY_LANE_WIDEN_M", 0.0)
