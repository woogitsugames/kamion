"""ADR 0232: physics telemetry behind the A/B audio scenes.

The driver timelines in ``scenarios0232/*.json`` are run by the project's own physics runner
(``tools/physics-runner``, the same C# vehicle model the game uses, 100 Hz):

    uv run python telemetry0232.py --refresh      # needs the .NET 8 SDK (dotnet on PATH or DOTNET=...)

which stores the columns the sound needs in ``scenarios0232/telemetry/<id>.csv`` (committed, so the
audio renders and tests run without .NET). Nothing here is a hand-drawn rpm curve: rpm, gear and AMT
shift phases, throttle demand, boost, engine and retarder torques, reservoir pressure and the compressor
state are what the physics produced for the timeline.

``load(name)`` returns the audio inputs exactly as ``TruckAudioController`` / ``EngineAudio`` read them
from the vehicle model (see the property-by-property mapping in ``Frames``).
"""

from __future__ import annotations

import argparse
import csv
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np

import physics_params as pp

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCEN_DIR = HERE / "scenarios0232"
TELE_DIR = SCEN_DIR / "telemetry"
DT = 0.01  # physics step of the runner

COLUMNS = ["t", "speed_kmh", "throttle_in", "brake_in", "parking_in", "retarder_lever", "throttle_eff", "brake_demand",
           "rpm", "gear", "amt_state", "engine_torque", "boost", "engine_brake_cmd", "engine_brake_torque",
           "retarder_torque", "retarder_power_kw", "air_supply_bar", "compressor_on"]

# AmtState (AmtController.cs)
AMT_IDLE, AMT_LAUNCH, AMT_DRIVE, AMT_TORQUE_RAMP, AMT_NEUTRAL, AMT_SYNC, AMT_ENGAGE = range(7)
SHIFT_STATES = (AMT_TORQUE_RAMP, AMT_NEUTRAL, AMT_SYNC, AMT_ENGAGE)


@dataclass(frozen=True)
class Scene:
    name: str            # file stem of the A/B renders
    scenario: str        # scenario id incl. variant, as the runner names its CSV
    window: tuple[float, float]   # part of the physics run that is rendered [s]
    title: str           # Polish, for the README


SCENES = (
    Scene("1_ruszanie_40t", "a0232_launch_laden@laden40", (0.0, 27.0),
          "Ruszanie z ładunkiem 40 t pod górę 3 %, pełny gaz przez biegi, odpuszczenie gazu, częściowy gaz"),
    Scene("2_biegi_pusty", "a0232_gears@empty", (0.0, 25.0),
          "Przyspieszanie pustym zestawem przez biegi: gaz 55 %, potem 100 %, odpuszczenie, gaz 70 %"),
    Scene("3_zjazd_hamulce_dlugotrwale", "a0232_downhill@laden40", (0.0, 26.0),
          "Zjazd 7 % z 75 km/h, 40 t: wybieg, dźwignia stopień 2, maksimum, zwolnienie, gaz 60 %"),
    Scene("4_postoj_pneumatyka", "a0232_standstill_air@laden40", (32.0, 60.0),
          "Postój 40 t: sprężarka na podwyższonych obrotach, odcięcie regulatora (osuszacz), zwolnienie hamulca "
          "postojowego, ruszenie, zatrzymanie, zaciągnięcie postojowego"),
)


def scene(name: str) -> Scene:
    return next(s for s in SCENES if s.name == name)


# --------------------------------------------------------------------------- refresh (physics runner)
def refresh() -> None:
    dotnet = os.environ.get("DOTNET") or shutil.which("dotnet")
    if not dotnet:
        raise SystemExit("dotnet (.NET 8 SDK) not found: set DOTNET=<path to dotnet> or use the committed telemetry")
    TELE_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        cmd = [dotnet, "run", "--project", str(ROOT / "tools" / "physics-runner" / "Runner"), "-c", "Release", "--",
               "--scenarios", str(SCEN_DIR), "--no-multi", "--out", tmp]
        subprocess.run(cmd, check=True, env={**os.environ, "DOTNET_CLI_TELEMETRY_OPTOUT": "1"})
        for sc in SCENES:
            with open(Path(tmp) / f"{sc.scenario}.csv", newline="", encoding="utf-8") as f:
                rows = list(csv.reader(f))
            idx = [rows[0].index(c) for c in COLUMNS]
            out = TELE_DIR / f"{sc.scenario.replace('@', '_')}.csv"
            with open(out, "w", newline="\n", encoding="utf-8") as f:
                f.write(",".join(COLUMNS) + "\n")
                for r in rows[1:]:
                    f.write(",".join(f"{float(r[i]):.6g}" for i in idx) + "\n")
            print(f"{out.relative_to(ROOT)}: {len(rows) - 1} rows")


# --------------------------------------------------------------------------- audio inputs
@dataclass
class Frames:
    """Audio inputs per physics step (100 Hz), named after what the game reads.

    rpm          Engine.Rpm
    load         Engine.LastLoad, recovered exactly from the logged net torque:
                 LastTorque = full(rpm) * LastLoad - (drag(rpm) + EngineBrakeTorque)   (Engine.ComputeTorque)
    throttle     VehicleModel.ThrottleDemand (telemetry column throttle_eff)
    boost        Engine.Boost
    engine_brake TruckAudioController.EngineBrake: Engine.EngineBrakeState, muted while the AMT is mid-shift.
                 The state is recovered from EngineBrakeTorque / (EngineBrakeTotal(rpm) - drag(rpm)).
    ebrake_state the unmuted actuator state (DrivelineSfx reads it), ebrake_cmd = EngineBrakeCommand > 0.01
    speed        |SpeedForward| [m/s]
    retarder_fill  Retarder.Fill, recovered from torque / available torque; retarder_power [W] = Retarder.Power
    brake        BrakeDemand, park = Input.ParkingBrake, compressor = Air.CompressorLoaded, amt = Amt.State
    """
    t: np.ndarray
    rpm: np.ndarray
    load: np.ndarray
    throttle: np.ndarray
    boost: np.ndarray
    engine_brake: np.ndarray
    ebrake_state: np.ndarray
    ebrake_cmd: np.ndarray
    speed: np.ndarray
    retarder_fill: np.ndarray
    retarder_power: np.ndarray
    brake: np.ndarray
    park: np.ndarray
    compressor: np.ndarray
    amt: np.ndarray
    gear: np.ndarray
    air_supply: np.ndarray
    lever: np.ndarray

    def __len__(self) -> int:
        return len(self.t)


def read_csv(scenario: str) -> dict[str, np.ndarray]:
    path = TELE_DIR / f"{scenario.replace('@', '_')}.csv"
    data = np.genfromtxt(path, delimiter=",", names=True)
    return {n: np.asarray(data[n], dtype=float) for n in data.dtype.names}


def retarder_available_torque(shaft_rpm):
    """RetarderDefinition: torque ~ shaft speed^2 up to fullTorqueShaftRpm, capped by the power limit [N m]."""
    r = pp.vehicle()["retarder"]
    shaft_rpm = np.asarray(shaft_rpm, dtype=float)
    w = shaft_rpm * 2 * np.pi / 60.0
    t = r["maxTorqueNm"] * np.minimum(1.0, (shaft_rpm / r["fullTorqueShaftRpm"]) ** 2)
    return np.where(w > 1e-3, np.minimum(t, r["maxPowerKW"] * 1000.0 / np.maximum(w, 1e-3)), t)


def load(name: str) -> Frames:
    sc = scene(name)
    c = read_csv(sc.scenario)
    m = (c["t"] >= sc.window[0] - 1e-9) & (c["t"] < sc.window[1] + DT - 1e-9)
    c = {k: v[m] for k, v in c.items()}
    rpm = c["rpm"]
    amt = c["amt_state"].astype(int)
    eb_extra = np.maximum(pp.engine_brake_extra(rpm), 1.0)
    state = np.clip(c["engine_brake_torque"] / eb_extra, 0.0, 1.0)
    speed = np.abs(c["speed_kmh"]) / 3.6
    shaft = pp.shaft_rpm(speed)
    fill = np.clip(c["retarder_torque"] / np.maximum(retarder_available_torque(shaft), 1.0), 0.0, 1.0)
    return Frames(
        t=c["t"] - sc.window[0],
        rpm=rpm,
        load=pp.load_from_torque(rpm, c["engine_torque"], c["engine_brake_torque"]),
        throttle=np.clip(c["throttle_eff"], 0.0, 1.0),
        boost=np.clip(c["boost"], 0.0, 1.0),
        engine_brake=np.where(np.isin(amt, SHIFT_STATES), 0.0, state),
        ebrake_state=state,
        ebrake_cmd=c["engine_brake_cmd"] > 0.01,
        speed=speed,
        retarder_fill=fill,
        retarder_power=c["retarder_power_kw"] * 1000.0,
        brake=c["brake_demand"],
        park=c["parking_in"] > 0.5,
        compressor=c["compressor_on"] > 0.5,
        amt=amt,
        gear=c["gear"].astype(int),
        air_supply=c["air_supply_bar"],
        lever=c["retarder_lever"].astype(int),
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="re-run the physics runner and rewrite the telemetry CSVs")
    args = ap.parse_args()
    if args.refresh:
        refresh()
    for sc in SCENES:
        f = load(sc.name)
        shifts = int(np.sum((f.amt[1:] == AMT_NEUTRAL) & (f.amt[:-1] != AMT_NEUTRAL)))
        print(f"{sc.name}: {len(f) * DT:.1f} s, rpm {f.rpm.min():.0f}-{f.rpm.max():.0f}, load {f.load.min():.2f}-{f.load.max():.2f}, "
              f"boost max {f.boost.max():.2f}, shifts {shifts}, engine brake max {f.engine_brake.max():.2f}, "
              f"retarder max {f.retarder_power.max() / 1000:.0f} kW, air {f.air_supply.min():.2f}-{f.air_supply.max():.2f} bar")


if __name__ == "__main__":
    main()
