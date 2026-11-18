"""Unit test (no Data/raw, no build): PBR freshness check of art-source/world/materials/_src/build_all.py (D43).

scripts/import-region.ps1 runs `build_all.py --check --tier <t>` and rebuilds (~8 min) only on exit 3. Only files
build_all would write with the current inputs may decide; files it skips (asphalt_detail_photo without the owner
photo, scan-only sets without CC0 scans) must not, or every import rebuilds and leaves them unchanged.

Run: uv run --project tools/worldgen python -m pytest tests/gis/test_materials_freshness.py -q
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

BUILD_ALL = Path(__file__).resolve().parents[2] / "art-source" / "world" / "materials" / "_src" / "build_all.py"


@pytest.fixture(scope="module")
def ba():
    spec = importlib.util.spec_from_file_location("materials_build_all", BUILD_ALL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _tree(tmp: Path, *, gen_old: bool, photo_old: bool) -> tuple[Path, Path]:
    """Synthetic materials root: _src/gen.py at t=2000, one generated set + the photo layer, PNG mtimes 1000/3000."""
    root, src = tmp / "materials", tmp / "materials" / "_src"
    src.mkdir(parents=True)
    (src / "gen.py").write_text("# generator\n")
    os.utime(src / "gen.py", (2000, 2000))
    spec = {"sets": {
        "asphalt_worn": {"files": {"Medium": {"dir": "asphalt_worn/Medium", "files": ["T_asphalt_worn_BaseColor.png"]}}},
        "asphalt_detail_photo": {"files": {"Medium": {"dir": "asphalt_detail_photo/Medium",
                                                      "files": ["T_asphalt_detail_photo_DetailAlbedo.png",
                                                                "T_asphalt_detail_photo_DetailNormal.png"]}}},
    }}
    (root / "materials_spec.json").write_text(json.dumps(spec))
    for set_name, entry in spec["sets"].items():
        f = entry["files"]["Medium"]
        t = (1000 if photo_old else 3000) if set_name == "asphalt_detail_photo" else (1000 if gen_old else 3000)
        for n in f["files"]:
            p = root / f["dir"] / n
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"png")
            os.utime(p, (t, t))
    return root, src


def test_unproduced_file_older_than_src_does_not_rebuild(ba, tmp_path):
    root, src = _tree(tmp_path, gen_old=False, photo_old=True)
    prod = ba.producible_sets(photo=tmp_path / "no_photo.jpg")
    assert prod["asphalt_detail_photo"] is not None and prod["asphalt_worn"] is None
    r = ba.check_fresh("Medium", root, src, producible={"asphalt_worn": None, "asphalt_detail_photo": "no photo"})
    assert r["rebuild"] is False, r
    assert r["stale"] == [] and len(r["skipped"]) == 2


def test_unproduced_missing_file_does_not_rebuild(ba, tmp_path):
    root, src = _tree(tmp_path, gen_old=False, photo_old=True)
    for p in (root / "asphalt_detail_photo").rglob("*.png"):
        p.unlink()
    r = ba.check_fresh("Medium", root, src, producible={"asphalt_worn": None, "asphalt_detail_photo": "no photo"})
    assert r["rebuild"] is False and r["missing"] == []


def test_produced_file_older_than_src_rebuilds(ba, tmp_path):
    root, src = _tree(tmp_path, gen_old=True, photo_old=False)
    r = ba.check_fresh("Medium", root, src, producible={"asphalt_worn": None, "asphalt_detail_photo": "no photo"})
    assert r["rebuild"] is True
    assert r["stale"] == ["asphalt_worn/Medium/T_asphalt_worn_BaseColor.png"]


def test_photo_layer_counts_when_photo_present(ba, tmp_path):
    root, src = _tree(tmp_path, gen_old=False, photo_old=True)
    photo = tmp_path / "photo.jpg"
    photo.write_bytes(b"jpg")
    prod = ba.producible_sets(photo=photo)
    assert prod["asphalt_detail_photo"] is None
    r = ba.check_fresh("Medium", root, src, photo=photo,
                       producible={"asphalt_worn": None, "asphalt_detail_photo": None})
    assert r["rebuild"] is True and len(r["stale"]) == 2


def test_produced_missing_and_unbuilt_set_rebuild(ba, tmp_path):
    root, src = _tree(tmp_path, gen_old=False, photo_old=False)
    (root / "asphalt_worn/Medium/T_asphalt_worn_BaseColor.png").unlink()
    r = ba.check_fresh("Medium", root, src, producible={"asphalt_worn": None, "asphalt_detail_photo": "no photo"})
    assert r["rebuild"] and r["missing"] == ["asphalt_worn/Medium/T_asphalt_worn_BaseColor.png"]
    (root / "asphalt_worn/Medium/T_asphalt_worn_BaseColor.png").write_bytes(b"png")
    r = ba.check_fresh("Medium", root, src, producible={"asphalt_worn": None, "grass_verge": None})
    assert r["rebuild"] and r["unbuilt_sets"] == ["grass_verge"]


def test_check_cli_exit_codes(tmp_path):
    """CLI contract used by import-region.ps1: exit 0 = fresh, 3 = rebuild, anything else = error."""
    r = subprocess.run([sys.executable, str(BUILD_ALL), "--check", "--tier", "Medium",
                        "--photo", str(tmp_path / "none.jpg")], capture_output=True, text=True)
    assert r.returncode in (0, 3), r.stderr
    assert "asphalt_detail_photo" in r.stdout          # reported as skipped without the photo
