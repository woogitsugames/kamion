"""ADR 0246: the phone pose list is derived from the photo-pair cameras, never authored by hand.

    uv run --project tools/worldgen --with pytest pytest tests/gate3/test_g3_poses.py -q
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("g3_poses", REPO / "scripts" / "g3_poses.py")
gp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gp)

REGION = "bialystok-industrial-c"


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def test_both_copies_are_current_and_identical():
    assert gp.main(["check", "--region", REGION]) == 0
    paths = gp.data_paths(REGION)
    assert paths["data_out"].read_bytes() == paths["resource_out"].read_bytes()


def test_every_pose_equals_its_photo_pair_camera():
    paths = gp.data_paths(REGION)
    doc = load(paths["resource_out"])
    cams = load(paths["cameras"])["cameras"]
    refs = {r["camera"]: r for r in load(paths["references"])["references"]}
    assert doc["schema"] == gp.SCHEMA
    assert doc["count"] == len(doc["poses"]) == len(cams) == 42
    for i, (p, c) in enumerate(zip(doc["poses"], cams)):
        assert p["index"] == i + 1
        assert p["source"]["cameras_index"] == i
        for k in ("id", "segment", "kind", "pos", "look_at", "fov_deg"):
            assert p[k] == c[k], (p["id"], k)
        r = refs[p["id"]]
        assert (p["reference"]["width"], p["reference"]["height"]) == (r["width"], r["height"])
        assert p["out_width"] == 1280
        assert p["out_height"] == round(1280 * r["height"] / r["width"])
    assert doc["inputs"][gp.rel(paths["cameras"])] == gp.sha256(paths["cameras"])


def test_filter_rule_matches_the_game():
    pose = {"index": 7, "id": "sbs-g3-a-1406533339711789"}
    assert gp.matches(pose, "")
    assert gp.matches(pose, "7")
    assert not gp.matches(pose, "8")
    assert gp.matches(pose, "1-9") and gp.matches(pose, "9-1")
    assert not gp.matches(pose, "8-12")
    assert gp.matches(pose, "140653")          # > 3 digits: id substring, not an index
    assert gp.matches(pose, "SBS_G3_A")
    assert not gp.matches(pose, "g3-b")
    assert gp.matches(pose, "3-a")
