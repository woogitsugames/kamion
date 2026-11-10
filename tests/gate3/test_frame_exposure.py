"""Frame-exposure check of scripts/gate3_evidence.py (r6 W-N10): frames inside geometry / with black holes must FAIL.

    uv run --project tools/worldgen --with pillow --with pytest pytest tests/gate3 -q
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

PIL = pytest.importorskip("PIL.Image")
REPO = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("gate3_evidence", REPO / "scripts" / "gate3_evidence.py")
ge = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ge)


def frame(path: Path, base: int, black_frac: float = 0.0):
    a = np.full((100, 200, 3), base, np.uint8)
    n = int(round(100 * black_frac))
    if n:
        a[:n] = 0
    PIL.fromarray(a).save(path)
    return path


def test_normal_frame_passes():
    r = ge.frame_exposure(np.full((50, 50, 3), 120, np.uint8))
    assert r["ok"] and r["dark_frac"] == 0.0


def test_black_box_inside_geometry_fails():
    r = ge.frame_exposure(np.zeros((50, 50, 3), np.uint8))
    assert not r["ok"] and r["p50"] == 0.0


def test_dim_frame_p50_boundary():
    # sRGB grey 38 -> luma 0.149 (<= 15 %) fails, 39 -> 0.153 passes
    assert not ge.frame_exposure(np.full((10, 10, 3), 38, np.uint8))["ok"]
    assert ge.frame_exposure(np.full((10, 10, 3), 39, np.uint8))["ok"]


def test_black_hole_share_boundary():
    def img(frac):
        n = int(100 * frac)
        return np.vstack([np.zeros((n, 20, 3), np.uint8), np.full((100 - n, 20, 3), 150, np.uint8)])

    assert ge.frame_exposure(img(0.20))["ok"]       # exactly 20 % black is allowed
    assert not ge.frame_exposure(img(0.21))["ok"]    # more than 20 % black fails even with a bright median


def test_check_aggregates_and_names_failures(tmp_path):
    good = frame(tmp_path / "good.png", 130)
    hole = frame(tmp_path / "hole.png", 150, black_frac=0.3)
    dark = frame(tmp_path / "dark.png", 10)
    res = ge.check_frame_exposure({"good": good, "hole": hole, "dark": dark})
    assert res["verdict"] == "FAIL" and res["frames_checked"] == 3
    assert {r["frame"] for r in res["failing"]} == {"hole", "dark"}
    assert ge.check_frame_exposure({"good": good})["verdict"] == "PASS"


def test_unreadable_frame_fails(tmp_path):
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"not a png")
    assert ge.check_frame_exposure({"bad": bad})["verdict"] == "FAIL"


def test_no_frames_is_not_a_pass():
    assert ge.check_frame_exposure({})["verdict"] == "FAIL"


def test_spawn_camera_is_out_of_the_truck():
    d = json.loads((REPO / "Data/Regions/bialystok-industrial-c/gate3_cameras.json").read_text(encoding="utf-8"))
    c = next(c for c in d["cameras"] if c["id"] == "g3a_eye_s0012")
    assert c["s_m"] >= 12.0 + 12.0, "camera at the truck spawn (s=12 m) sits inside the cab (W-N10)"
