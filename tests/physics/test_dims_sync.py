"""art-source/truck/dims.json is the single source of truth for shared model/physics dimensions (ADR 0014).
Run: python tests/physics/test_dims_sync.py   (or pytest)."""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "game/Assets/_Project/Vehicle/Physics/Definitions/Data"
dims = json.loads((ROOT / "art-source/truck/dims.json").read_text(encoding="utf-8"))["values"]
veh = json.loads((DATA / "tractor_4x2_generic.vehicle.json").read_text(encoding="utf-8"))
trl = json.loads((DATA / "curtainsider_tridem_13_6.trailer.json").read_text(encoding="utf-8"))
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


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f()
            print("ok", n)
