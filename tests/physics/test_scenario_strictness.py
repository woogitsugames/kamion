"""Regression guard: the Stage 2 scenario generator must not loosen checks (ADR 0032 context, ADR 0019 geometry).

Run: python tests/physics/test_scenario_strictness.py   (or pytest)

1. Regenerating into a temp dir must reproduce every committed scenario JSON (semantic equality). A generator that
   drifts from the committed files, in either direction, fails.
2. Hard ceilings on the kerb checks are pinned here independently of the generator and the JSON, so raising a
   tolerance in BOTH places still fails. Raise them only together with a documented physics change.
3. Kerb block geometry covers every left tyre patch (from dims.json) and none of the right ones.
"""
import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
GEN = ROOT / "tests/physics/generate_stage2_scenarios.py"
SCEN = ROOT / "tests/physics/scenarios"
DIMS = json.loads((ROOT / "art-source/truck/dims.json").read_text(encoding="utf-8"))["values"]

# (scenario, metric, arg, variant) -> maximum allowed "max" (None variant = any)
CEILINGS = {
    ("curb_strike_5cm_50kmh_comb", "max_fz_ratio", 0, None): 2.2,
    ("curb_strike_5cm_50kmh_comb", "wheel_off_ground_time_s", 0, "empty"): 0.08,
    ("curb_strike_5cm_50kmh_comb", "wheel_off_ground_time_s", 0, "laden40"): 0.03,
    ("curb_strike_5cm_50kmh_comb", "max_wheel_airtime_s", 1, "empty"): 0.03,
    ("curb_strike_5cm_50kmh_comb", "max_wheel_airtime_s", 1, "laden40"): 0.03,
    ("curb_strike_14cm_50kmh_comb", "max_fz_ratio", 0, None): 4.2,
    ("curb_strike_14cm_50kmh_comb", "wheel_off_ground_time_s", 0, "empty"): 0.75,
    ("curb_strike_14cm_50kmh_comb", "wheel_off_ground_time_s", 0, "laden40"): 0.28,
    ("curb_strike_14cm_50kmh_comb", "max_wheel_airtime_s", 1, "empty"): 0.15,
    ("curb_strike_14cm_50kmh_comb", "max_wheel_airtime_s", 1, "laden40"): 0.12,
    ("curb_strike_14cm_50kmh_comb", "max_wheel_airtime_s", 0, "empty"): 0.25,
    ("curb_strike_14cm_50kmh_comb", "max_wheel_airtime_s", 0, "laden40"): 0.12,
    ("kerb_step_27cm_42kmh_comb", "max_fz_ratio", 0, None): 7.5,
    ("kerb_step_27cm_42kmh_comb", "max_wheel_airtime_s", 1, None): 0.5,
}
for _s in ("curb_strike_5cm_50kmh_comb", "curb_strike_14cm_50kmh_comb", "kerb_step_27cm_42kmh_comb"):
    CEILINGS[(_s, "max_dv_step_ms", 0, None)] = 0.35
    CEILINGS[(_s, "max_pos_jump_m", 0, None)] = 1e-6
    CEILINGS[(_s, "max_fifth_wheel_error_mm", 0, None)] = 5


def _load(p):
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))


def test_generator_reproduces_committed_scenarios():
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run([sys.executable, str(GEN), tmp], capture_output=True, text=True)
        assert r.returncode == 0, f"generator failed: {r.stdout}{r.stderr}"
        diffs = []
        for f in sorted(pathlib.Path(tmp).glob("*.json")):
            committed = SCEN / f.name
            assert committed.exists(), f"generator emits {f.name} but it is not committed"
            if _load(f) != _load(committed):
                diffs.append(f.name)
        assert not diffs, f"regeneration differs from committed scenarios (loosened or hand-edited): {diffs}"


def test_kerb_ceilings_not_loosened():
    for (sid, metric, arg, variant), ceil in CEILINGS.items():
        checks = [c for c in _load(SCEN / f"{sid}.json")["checks"]
                  if c["metric"] == metric and c.get("arg", 0) == arg and c.get("variant") == variant and "max" in c]
        assert checks, f"{sid}: missing check {metric} arg={arg} variant={variant}"
        for c in checks:
            assert c["max"] <= ceil + 1e-12, f"{sid} {metric}@{variant}: max {c['max']} > pinned {ceil} (tolerance loosened)"


def test_kerb_block_covers_left_wheels_only():
    v = lambda k: DIMS[k]["value"]
    hs, ts = v("tyre_section_width_m") / 2, v("trailer_tyre_section_width_m") / 2
    patches = [(v("front_track_m") / 2 - hs, v("front_track_m") / 2 + hs),
               (v("rear_track_m") / 2 - v("dual_spacing_m") / 2 - hs, v("rear_track_m") / 2 + v("dual_spacing_m") / 2 + hs),
               (v("trailer_track_m") / 2 - ts, v("trailer_track_m") / 2 + ts)]
    assert abs(v("artic_length_m") - 16.47) < 1e-6 and v("artic_length_m") <= v("max_artic_length_m")
    for sid in ("curb_strike_5cm_50kmh_comb", "curb_strike_14cm_50kmh_comb", "kerb_step_27cm_42kmh_comb"):
        b = _load(SCEN / f"{sid}.json")["ground"]["boxes"][0]
        for inner, outer in patches:
            assert b["minX"] <= -outer and b["maxX"] >= -inner, f"{sid}: block does not cover left patch {inner:.3f}..{outer:.3f} m"
        assert b["maxX"] <= 0, f"{sid}: block touches right wheels"


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f()
            print("ok", n)
