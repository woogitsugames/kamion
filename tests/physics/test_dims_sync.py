"""art-source/truck/dims.json is the single source of truth for shared model/physics dimensions (ADR 0014).
Run: python tests/physics/test_dims_sync.py   (or pytest)."""
import json
import math
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


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f()
            print("ok", n)
