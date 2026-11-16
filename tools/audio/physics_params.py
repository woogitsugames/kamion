"""Vehicle physics parameters used by the sound model (ADR 0232).

Read from the game's definition files (the same JSON the physics loads), so the synthesis and the
offline runtime mirror never carry their own copy of a torque curve or a shift time:

    game/Assets/_Project/Vehicle/Physics/Definitions/Data/*.json

Status of the numbers is the status given in those files (sourced fact-sheet points or WORKING_VALUE);
nothing is measured here.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DEFS = ROOT / "game" / "Assets" / "_Project" / "Vehicle" / "Physics" / "Definitions" / "Data"
ENGINE_ID = "diesel_r6_13l_368kw"
GEARBOX_ID = "amt12_od_class"
VEHICLE_ID = "tractor_4x2_generic"
TYRE_ID = "tire_315_80_r22_5"


@lru_cache(maxsize=None)
def _load(name: str) -> dict:
    return json.loads((DEFS / name).read_text(encoding="utf-8"))


def engine() -> dict:
    return _load(f"{ENGINE_ID}.engine.json")


def gearbox() -> dict:
    return _load(f"{GEARBOX_ID}.gearbox.json")


def vehicle() -> dict:
    return _load(f"{VEHICLE_ID}.vehicle.json")


def _lut(xs, ys, x):
    return np.interp(x, np.asarray(xs, dtype=float), np.asarray(ys, dtype=float))


def full_load_torque(rpm):
    """Engine.FullLoadTorque: torque LUT with the high-speed governor fade [N m]."""
    e = engine()
    rpm = np.asarray(rpm, dtype=float)
    t = _lut(e["torqueCurveRpm"], e["torqueCurveNm"], rpm)
    fade = np.clip((e["maxRpm"] - rpm) / (e["maxRpm"] - e["governorStartRpm"]), 0.0, 1.0)
    return np.where(rpm > e["governorStartRpm"], t * fade, t)


def drag_torque(rpm):
    """Engine.DragTorque (motoring friction + pumping) [N m]."""
    e = engine()
    return _lut(e["dragCurveRpm"], e["dragCurveNm"], np.asarray(rpm, dtype=float))


def engine_brake_total(rpm):
    """Engine.EngineBrakeTotal: retarding torque at full engine-brake command, drag included [N m]."""
    e = engine()
    rpm = np.asarray(rpm, dtype=float)
    eb = _lut(e["engineBrakeCurveRpm"], e["engineBrakeCurveNm"], rpm)
    eb = eb * np.clip((rpm - 0.9 * e["idleRpm"]) / (0.5 * e["idleRpm"]), 0.0, 1.0)
    return np.maximum(drag_torque(rpm), eb)


def engine_brake_extra(rpm):
    """Torque the engine brake adds beyond the motoring drag at full command [N m]."""
    return engine_brake_total(rpm) - drag_torque(rpm)


def load_from_torque(rpm, net_torque, engine_brake_torque=0.0):
    """Inverse of Engine.ComputeTorque: LastLoad = (LastTorque + drag + engine-brake torque) / full-load torque."""
    full = np.maximum(full_load_torque(rpm), 1.0)
    return np.clip((np.asarray(net_torque, dtype=float) + drag_torque(rpm) + engine_brake_torque) / full, 0.0, 1.0)


def wheel_radius() -> float:
    t = _load(f"{TYRE_ID}.tire.json")
    for key in ("radius", "loadedRadius", "unloadedRadius"):
        if key in t:
            return float(t[key])
    raise KeyError("tyre radius")


def shaft_rpm(speed_ms):
    """Propshaft speed (LayerMath.ShaftRpm): wheel speed x final drive."""
    return np.asarray(speed_ms, dtype=float) / wheel_radius() * vehicle()["driveline"]["finalDriveRatio"] * 60.0 / (2 * np.pi)
