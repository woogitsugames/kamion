"""art-source/truck/dims.json is the single source of truth for shared model/physics dimensions (ADR 0014).
Run: python tests/physics/test_dims_sync.py   (or pytest)."""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "game/Assets/_Project/Vehicle/Physics/Definitions/Data"
dims = json.loads((ROOT / "art-source/truck/dims.json").read_text(encoding="utf-8"))["values"]
veh = json.loads((DATA / "tractor_4x2_generic.vehicle.json").read_text(encoding="utf-8"))
trl = json.loads((DATA / "curtainsider_tridem_13_6.trailer.json").read_text(encoding="utf-8"))
TIRES = {n: json.loads((DATA / (n + ".tire.json")).read_text(encoding="utf-8")) for n in ("tire_385_65_r22_5",)}
TOL = 0.0005


def d(k):
    return dims[k]["value"]


def axle(name_front):
    return next(a for a in veh["axles"] if (a["positionZ"] > 1) == name_front)


def check(label, art, phys):
    assert abs(art - phys) <= TOL, f"{label}: dims.json {art} != physics {phys}"


def test_wheelbase():
    check("wheelbase", d("wheelbase_m"), axle(True)["positionZ"] - axle(False)["positionZ"])


def test_tracks():
    check("front track", d("front_track_m"), axle(True)["trackWidth"])
    check("rear track", d("rear_track_m"), axle(False)["trackWidth"])


def test_fifth_wheel():
    p = veh["fifthWheel"]["position"]
    check("fifth wheel height", d("fifth_wheel_height_m"), p["y"])
    check("fifth wheel lead", d("fifth_wheel_lead_m"), p["z"])
    check("trailer kingpin height", d("fifth_wheel_height_m"), trl["kingpinHeight"])


def test_cab_mount():
    m = veh["cab"]["mountCenter"]
    check("cab mount height", d("cab_mount_height_m"), m["y"])
    check("cab mount z", d("cab_mount_z_m"), m["z"])


def test_combination_length_legal():
    """96/53/EC Annex I 1.1: articulated vehicle <= 16.50 m (tractor front -> kingpin + kingpin -> trailer rear)."""
    front_to_kingpin = d("front_overhang_m") + d("wheelbase_m") - veh["fifthWheel"]["position"]["z"]
    total = front_to_kingpin + d("semitrailer_kingpin_to_rear_m")
    assert total <= d("max_artic_length_m") + 1e-9, f"combination {total:.3f} m > {d('max_artic_length_m')} m"
    check("artic_length_m", d("artic_length_m"), total)
    assert d("max_artic_length_m") - total >= 0.02, "keep >= 2 cm margin"


def test_trailer_kingpin_frame():
    # (the front corner radius sqrt(1.6^2 + 1.275^2) = 2.046 m is a box bound; the model's rounded corner measures 2.029 m)
    assert d("trailer_body_length_m") - d("trailer_kingpin_to_front_m") <= d("semitrailer_kingpin_to_rear_m") + 1e-9
    # tractor cab back stays outside the trailer front swing circle
    cab_back_z = d("wheelbase_m") - d("cab_back_behind_front_axle_m")
    assert veh["fifthWheel"]["position"]["z"] - 0 <= cab_back_z - d("semitrailer_front_swing_radius_m")


def test_trailer_axles_tyres():
    z = d("trailer_axle_z_m")
    assert len(z) == len(trl["axles"])
    for a, zz in zip(trl["axles"], z):
        check("trailer axle z", zz, a["positionZ"])
        check("trailer track", d("trailer_track_m"), a["trackWidth"])
    check("trailer wheel centre", d("trailer_wheel_centre_m"), trl["massElements"][3]["center"]["y"])
    check("trailer wheel centre vs tyre", d("trailer_wheel_centre_m"), 0.515)
    check("trailer tyre width", d("trailer_tyre_section_width_m"), TIRES["tire_385_65_r22_5"]["widthM"])


def test_trailer_cargo_bay():
    cb = trl["cargoBay"]
    check("floor height", d("trailer_floor_height_m"), cb["floorHeight"])
    check("cargo front z", d("trailer_cargo_front_z_m"), cb["frontZ"])
    check("cargo length", d("trailer_cargo_length_m"), cb["length"])
    check("cargo width", d("trailer_cargo_width_m"), cb["width"])
    check("cargo height", d("trailer_cargo_height_m"), cb["height"])
    top = cb["floorHeight"] + cb["height"]
    assert top < d("trailer_overall_height_m") - 0.05, f"cargo envelope top {top} leaves no roof below {d('trailer_overall_height_m')}"
    assert d("trailer_overall_height_m") <= d("max_height_m") + 1e-9
    assert cb["width"] <= d("max_width_m")
    # body mass element spans floor top -> roof top
    body = next(m for m in trl["massElements"] if m["name"].startswith("body_"))
    check("body top", d("trailer_overall_height_m"), body["center"]["y"] + body["size"]["y"] / 2)
    check("body bottom", d("trailer_floor_height_m"), body["center"]["y"] - body["size"]["y"] / 2)


def test_trailer_landing_gear():
    lg, g = d("trailer_landing_gear_m"), trl["landingGear"]
    check("leg z", lg["z"], g["positionZ"])
    check("leg half track", lg["half_track"], g["halfTrack"])
    check("leg raised foot", lg["raised_foot_y"], g["raisedFootY"])
    check("leg lowered foot", lg["lowered_foot_y"], g["loweredFootY"])


def _boxes(defn):
    return {b["name"]: b for b in defn["bodyBoxes"]}


def _check_box(b, center, size, ground, coupling):
    for ax, c, s in zip("xyz", center, size):
        check(f"{b['name']} centre {ax}", c, b["center"][ax])
        check(f"{b['name']} size {ax}", s, b["size"][ax])
    assert b["ground"] is ground and b["coupling"] is coupling, f"{b['name']}: flags ground={b['ground']} coupling={b['coupling']}"


def test_body_boxes_tractor():
    """ADR 0228: tractor body boxes (one geometry source for the chassis-ground and tractor-trailer contact) = the
    graybox colliders (GrayboxTractorBuilder 'Colliders': Frame, Cab, Bumper) + the graybox rear mudguards, from dims.json.
    Builder constants (frame depth 0.22, bumper 0.60 / 0.50 / 0.20, cab gap 0.05, mudguard 1.12 / 0.70 x 0.03 x 1.20)."""
    b = _boxes(veh)
    wb, front, rear = d("wheelbase_m"), d("wheelbase_m") + d("front_overhang_m"), -d("rear_overhang_m")
    cab_rear = wb - d("cab_back_behind_front_axle_m")
    cab_len, cab_h = front - 0.05 - cab_rear, d("overall_height_m") - d("cab_body_bottom_m")
    _check_box(b["Frame"], (0, d("frame_top_height_m") - 0.11, rear + (front - rear) / 2), (d("frame_width_outer_m"), 0.22, front - rear), True, True)
    _check_box(b["Cab"], (0, d("cab_body_bottom_m") + cab_h / 2, cab_rear + cab_len / 2), (d("cab_width_m"), cab_h, cab_len), True, True)
    _check_box(b["Bumper"], (0, 0.60, front - 0.10), (d("cab_width_m") - 0.04, 0.50, 0.20), True, False)
    for side, s in (("Mudguard_L", -1), ("Mudguard_R", 1)):
        _check_box(b[side], (s * d("rear_track_m") / 2, 1.12, 0), (0.70, 0.03, 1.20), False, True)
    assert len(b) == 5


def test_body_boxes_trailer():
    """ADR 0228: trailer body boxes = GrayboxTrailerBuilder colliders (Body, Beams, RearUnderrun). Builder constants: front wall
    0.05 ahead of the cargo front, plate bottom 1.15 (+0.07), beam bottom 0.92, floor - 0.10, underrun 0.40-0.55 / 2.35 x 0.12."""
    b = _boxes(trl)
    cb, lg = trl["cargoBay"], trl["landingGear"]["positionZ"]
    fz = cb["frontZ"] + 0.05
    rz = fz - d("trailer_body_length_m")
    h, w = d("trailer_overall_height_m"), d("max_width_m")
    floor_bottom = cb["floorHeight"] - 0.10
    _check_box(b["Body"], (0, (1.15 + 0.07 + h) / 2, (fz + rz) / 2), (w, h - 1.15 - 0.07, d("trailer_body_length_m")), True, True)
    _check_box(b["Beams"], (0, (0.92 + floor_bottom) / 2, (lg - 0.4 + rz + 0.1) / 2), (1.2, floor_bottom - 0.92, lg - 0.4 - rz - 0.1), True, True)
    _check_box(b["RearUnderrun"], (0, (0.40 + 0.55) / 2, rz + 0.25), (2.35, 0.15, 0.12), True, True)
    assert len(b) == 3


def test_body_box_swing_clearance():
    """ADR 0228 finding: the graybox front corner (cargo front + 0.05 m wall, half width 1.275 m) swings at 2.063 m, the cab
    back is 2.07 m ahead of the kingpin: 7 mm clearance, so a slightly pitched trailer front touches the cab at ~45-55 deg.
    Pinned here so a dims change that closes the gap fails loudly (the legal 2.04 m swing radius has 3 cm)."""
    fz = trl["cargoBay"]["frontZ"] + 0.05
    swing = (fz ** 2 + (d("max_width_m") / 2) ** 2) ** 0.5
    cab_back = d("wheelbase_m") - d("cab_back_behind_front_axle_m") - veh["fifthWheel"]["position"]["z"]
    assert cab_back - swing > 0, f"graybox trailer front corner ({swing:.3f} m) reaches the cab back ({cab_back:.3f} m) when level"


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f()
            print("ok", n)
