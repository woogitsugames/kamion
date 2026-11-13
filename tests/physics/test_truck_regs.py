"""ADR 0175: the appearance of the TRAKT tractor + curtainsider trailer agrees with the artist table of
docs/reports/REVIEW-2026-11-13-s17-mistral-r8-p4.md (UN R48 / R46 / R58 / R70 / R73 / R104, 96/53/EC, WT).

art-source/truck/regs/{tractor,trailer}.json are the measured dumps of the generators (no bake):
    blender -b --factory-startup --python tools/blender/truck/regs_audit.py -- --what tractor --out art-source/truck/regs/tractor.json
    blender -b --factory-startup --python tools/blender/truck/regs_audit.py -- --what trailer --out art-source/truck/regs/trailer.json
Regenerate them after every change of tools/blender/truck/{exterior,trailer}. Run: pytest tests/physics/test_truck_regs.py
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/blender/truck"))
import regs_check  # noqa: E402

REGS = ROOT / "art-source/truck/regs"
tractor = json.loads((REGS / "tractor.json").read_text(encoding="utf-8"))["tractor"]
trailer = json.loads((REGS / "trailer.json").read_text(encoding="utf-8"))["trailer"]
dims = json.loads((ROOT / "art-source/truck/dims.json").read_text(encoding="utf-8"))["values"]


def _fails(rows):
    return [f"{r['vehicle']}: {r['item']} | {r['requirement']} | {r['measured']} | {r['source']}" for r in rows if not r["ok"]]


def test_tractor_rows():
    rows = regs_check.run(tractor=tractor)
    assert len(rows) >= 50
    assert not _fails(rows), "\n".join(_fails(rows))


def test_trailer_rows():
    rows = regs_check.run(trailer=trailer)
    assert len(rows) >= 80
    assert not _fails(rows), "\n".join(_fails(rows))


def test_tractor_carries_no_trailer_only_equipment():
    names = tractor["objects"]
    for prefix in ("contour", "r70", "rup", "sideguard", "tri_reflector"):
        assert not [n for n in names if n.startswith(prefix)], prefix


def test_checker_catches_a_missing_reversing_lamp():
    broken = json.loads(json.dumps(trailer))
    del broken["objects"]["rear_lens_rev_L"]
    assert any("cofania" in f for f in _fails(regs_check.run(trailer=broken)))


def test_combination_limits_9653():
    v = {k: x["value"] for k, x in dims.items()}
    assert v["artic_length_m"] <= 16.50 and v["max_width_m"] == 2.55 and v["trailer_overall_height_m"] <= 4.00
    assert trailer["overall"][5] <= 4.00 and tractor["overall"][5] <= 4.00
    assert 2 * trailer["dims"]["half_width"] <= 2.55
