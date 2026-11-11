"""ADR 0101: the ratio calibration tool and the committed calibration spec follow the method rules (REVIEW s10 P1-2)."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/worldgen/qa"))
import tint_ratio as TR  # noqa: E402

SPEC = json.loads((ROOT / "tools/worldgen/qa/tint_ratio_spec.json").read_text(encoding="utf-8"))


def test_committed_spec_obeys_two_camera_lit_shaded_reference_rule():
    assert TR.validate_spec(SPEC) == []
    for mat in ("kp_wall", "noise_panel_dark"):
        entry = SPEC["materials"][mat]
        assert entry.get("calibrated", True)
        assert len({c["camera"] for c in entry["checks"]}) >= 2


def test_validator_rejects_single_roi_calibration():
    bad = {"materials": {"x": {"checks": [
        {"id": "a", "camera": "cam", "side": "lit", "roi": [0, 0, 10, 10], "ref": "sky", "ref_roi": [10, 0, 20, 10]}]}}}
    errors = TR.validate_spec(bad)
    assert any(">= 2 cameras" in e for e in errors)
    assert any("lit and a shaded" in e for e in errors)


def _frame(path: Path, target_level: int, ref_level: int):
    a = np.full((443, 960, 3), ref_level, np.uint8)
    a[0:100, 0:100] = target_level
    Image.fromarray(a).resize((2340, 1080), Image.NEAREST).save(path)


def test_ratio_clip_and_limits_are_measured_on_full_png(tmp_path):
    spec = {"materials": {"m": {"checks": [
        {"id": "lit", "camera": "c1", "side": "lit", "roi": [10, 10, 90, 90], "ref": "plinth", "ref_roi": [200, 200, 300, 300],
         "limits": {"overcast": {"ratio_level": [0.34, 0.38]}, "clear": {"clip_max": 0.0}}},
        {"id": "sh", "camera": "c2", "side": "shaded", "roi": [10, 10, 90, 90], "ref": "plinth", "ref_roi": [200, 200, 300, 300],
         "limits": {"overcast": {"ratio_level": [0.34, 0.38]}}}]}}}
    for cond, (t, r) in {"Low-overcast": (36, 100), "Low-clear": (252, 120)}.items():
        (tmp_path / cond).mkdir()
        _frame(tmp_path / cond / "c1.png", t, r)
        _frame(tmp_path / cond / "c2.png", 30, 100)
    res = TR.evaluate(spec, tmp_path)
    by = {(r["check"], r["condition"]): r for r in res["rows"]}
    assert abs(by[("lit", "Low-overcast")]["ratio_level"] - 0.36) < 1e-6 and by[("lit", "Low-overcast")]["pass"]
    assert by[("lit", "Low-clear")]["target"]["clip_250"] == 1.0 and not by[("lit", "Low-clear")]["pass"]
    assert not by[("sh", "Low-overcast")]["pass"]          # 0.30 < 0.34
    assert len(res["failures"]) == 2


def test_linear_ratio_uses_srgb_decode():
    a = np.full((4, 4, 3), 188, np.float64)   # sRGB 188 ~ linear 0.5
    assert abs(TR.roi_stats(a)["lin_luma"] - 0.5) < 0.01


def test_placement_check_flags_roi_off_the_material_mask(tmp_path):
    a = np.zeros((443, 960, 3), np.uint8)
    a[0:100, 0:100] = (255, 0, 255)                           # material slot rendered flat magenta
    (tmp_path / "m").mkdir()
    Image.fromarray(a).resize((2340, 1080), Image.NEAREST).save(tmp_path / "m" / "c1_mask.png")
    good = {"materials": {"m": {"checks": [{"id": "g", "camera": "c1", "roi": [10, 10, 90, 90], "ref_roi": [200, 200, 300, 300]}]}}}
    bad = {"materials": {"m": {"checks": [{"id": "b", "camera": "c1", "roi": [50, 50, 150, 150], "ref_roi": [20, 20, 40, 40]}]}}}
    assert TR.check_placement(good, tmp_path) == []
    assert len(TR.check_placement(bad, tmp_path)) == 1
