# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib>=3.8", "numpy>=1.26"]
# ///
"""Plot vehicle-physics telemetry CSVs (docs/04 section 4) to PNG.

Usage:
    uv run tools/telemetry/plot.py artifacts/physics/<run>/            # every CSV in the folder
    uv run tools/telemetry/plot.py artifacts/physics/<run>/brake_80_0_dry.csv [--out DIR]

One PNG per CSV, written next to the CSV unless --out is given. Small multiples: one measure per
panel, one y-axis per panel (no dual axes); tractor wheels use a fixed categorical order FL, FR, RL, RR;
trailer wheels (when present) get their own row of panels in axle order.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

# Fixed categorical order (validated reference palette, light mode): wheel identity.
WHEEL_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#8b5cf6", "#d6336c"]
INK = "#3a3a38"
MUTED = "#8a8980"
GRID = "#e4e3dd"
WHEEL_KEYS = ("fz", "fx", "fy", "slip", "alpha_deg", "comp", "omega", "brake_t", "p_bar")


RUNNER_ONLY_COLUMNS = ("air_park_bar", "air_yellow_bar", "clutch_temp_c", "retarder_power_kw", "trailer_a_lat",
                       "trailer_roll_deg", "trailer_yaw_rate_dps")


def load(path: Path) -> tuple[dict[str, np.ndarray], dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    header, body = rows[0], rows[1:]
    cols: dict[str, np.ndarray] = {}
    meta: dict[str, str] = {}
    for j, name in enumerate(header):
        vals = [r[j] for r in body if j < len(r)]
        try:
            cols[name] = np.array([float(v) for v in vals])
        except ValueError:
            meta[name] = vals[0] if vals else ""
    # Columns of the .NET runner that the Unity recorder (VehicleTelemetryRecorder) does not write: empty (NaN) series,
    # so Unity / phone CSVs plot with the same layout (ADR 0195).
    n = len(body)
    for name in RUNNER_ONLY_COLUMNS:
        cols.setdefault(name, np.full(n, np.nan))
    return cols, meta


def wheel_names(cols: dict[str, np.ndarray]) -> list[str]:
    return [c[: -len("_fz")] for c in cols if c.endswith("_fz") and f"{c[:-3]}_slip" in cols]


def style(ax, title: str, unit: str) -> None:
    ax.set_title(f"{title} [{unit}]" if unit else title, fontsize=9, color=INK, loc="left")
    ax.grid(True, color=GRID, linewidth=0.6)
    ax.tick_params(labelsize=7, colors=MUTED)
    for s in ax.spines.values():
        s.set_color(GRID)


def line(ax, t, y, label=None, color=WHEEL_COLORS[0], ls="-"):
    ax.plot(t, y, color=color, linewidth=1.1, label=label, linestyle=ls)


def legend(ax, ncol=1):
    ax.legend(fontsize=7, frameon=False, ncol=ncol)


def wheel_panel(a, t, c, wheels, key, title, unit, scale):
    for i, w in enumerate(wheels):
        line(a, t, c[f"{w}_{key}"] * scale, w, WHEEL_COLORS[i % len(WHEEL_COLORS)])
    style(a, title, unit)
    legend(a, ncol=3 if len(wheels) > 4 else 4)


def plot_csv(path: Path, out_dir: Path) -> Path:
    c, meta = load(path)
    t = c["t"]
    allw = wheel_names(c)
    tractor = [w for w in allw if not w.startswith("T_")]
    trailer = [w for w in allw if w.startswith("T_")]
    has_tr = len(trailer) > 0
    rows = 7 if has_tr else 6
    fig, axes = plt.subplots(rows, 3, figsize=(16, 3.25 * rows), sharex=False)
    ax = axes.ravel()

    line(ax[0], t, c["speed_kmh"]); style(ax[0], "Speed", "km/h")
    line(ax[1], t, c["throttle_in"], "throttle in", WHEEL_COLORS[0])
    line(ax[1], t, c["throttle_eff"], "throttle eff", WHEEL_COLORS[0], "--")
    line(ax[1], t, c["brake_in"], "brake pedal", WHEEL_COLORS[1])
    line(ax[1], t, c["brake_demand"], "service demand (blend + hill hold)", WHEEL_COLORS[1], "--")
    line(ax[1], t, c["clutch_cmd"], "clutch cmd", WHEEL_COLORS[2])
    if "retarder_lever" in c:
        line(ax[1], t, c["retarder_lever"] / 5.0, "endurance lever / 5", WHEEL_COLORS[3])
    style(ax[1], "Driver inputs / clutch", "0..1"); legend(ax[1])
    line(ax[2], t, c["rpm"]); style(ax[2], "Engine speed", "rpm")
    ax[3].step(t, c["gear"], where="post", color=WHEEL_COLORS[0], linewidth=1.1); style(ax[3], "Gear (0=N, -1=R)", "")
    line(ax[4], t, c["engine_torque"], "engine net", WHEEL_COLORS[0])
    line(ax[4], t, c["clutch_torque"], "clutch transmitted", WHEEL_COLORS[1])
    if "engine_brake_torque" in c:
        line(ax[4], t, -c["engine_brake_torque"], "engine brake (retarding)", WHEEL_COLORS[2])
        line(ax[4], t, -c["retarder_torque"], "retarder at gearbox output", WHEEL_COLORS[3])
    style(ax[4], "Driveline torque", "N m"); legend(ax[4])
    line(ax[5], t, c["a_long"], "longitudinal", WHEEL_COLORS[0])
    line(ax[5], t, c["a_lat"], "lateral", WHEEL_COLORS[1])
    if has_tr:
        line(ax[5], t, c["trailer_a_lat"], "trailer lateral", WHEEL_COLORS[2])
    style(ax[5], "Acceleration (vehicle frame)", "m/s²"); legend(ax[5])

    for k, (key, title, unit, scale) in enumerate([
        ("fz", "Tractor wheel load Fz", "kN", 1e-3),
        ("fx", "Tractor tire Fx", "kN", 1e-3),
        ("fy", "Tractor tire Fy", "kN", 1e-3),
        ("slip", "Tractor slip ratio κ' (transient)", "-", 1.0),
        ("p_bar" if f"{tractor[0]}_p_bar" in c else "alpha_deg",
         "Tractor brake chamber pressure" if f"{tractor[0]}_p_bar" in c else "Slip angle α'",
         "bar" if f"{tractor[0]}_p_bar" in c else "deg", 1.0),
        ("comp", "Tractor suspension compression", "m", 1.0),
    ]):
        wheel_panel(ax[6 + k], t, c, tractor, key, title, unit, scale)

    line(ax[12], t, c["yaw_rate_dps"], "tractor", WHEEL_COLORS[0])
    if has_tr:
        line(ax[12], t, c["trailer_yaw_rate_dps"], "trailer", WHEEL_COLORS[1])
    style(ax[12], "Yaw rate", "deg/s"); legend(ax[12])
    line(ax[13], t, c["pitch_deg"], "body pitch", WHEEL_COLORS[0])
    line(ax[13], t, c["roll_deg"], "body roll", WHEEL_COLORS[1])
    line(ax[13], t, c["cab_pitch_deg"], "cab pitch (rel.)", WHEEL_COLORS[2])
    line(ax[13], t, c["cab_roll_deg"], "cab roll (rel.)", WHEEL_COLORS[3])
    if has_tr:
        line(ax[13], t, c["trailer_roll_deg"], "trailer roll", WHEEL_COLORS[4])
    style(ax[13], "Attitude", "deg"); legend(ax[13], ncol=2)
    ax[14].plot(c["x"], c["z"], color=WHEEL_COLORS[0], linewidth=1.1, label="tractor rear axle")
    if has_tr:
        ax[14].plot(c["trailer_x"], c["trailer_z"], color=WHEEL_COLORS[1], linewidth=1.1, label="trailer kingpin (ground)")
        legend(ax[14])
    ax[14].set_aspect("equal", adjustable="datalim")
    style(ax[14], "Trajectory x→z", "m")

    if "air_front_bar" in c:
        line(ax[15], t, c["air_front_bar"], "circuit 1 front", WHEEL_COLORS[0])
        line(ax[15], t, c["air_rear_bar"], "circuit 2 rear", WHEEL_COLORS[1])
        line(ax[15], t, c["air_park_bar"], "circuit 3 park/trailer", WHEEL_COLORS[2])
        if has_tr:
            line(ax[15], t, c["air_trailer_res_bar"], "trailer reservoir", WHEEL_COLORS[3])
            line(ax[15], t, c["air_yellow_bar"], "yellow (control) line", WHEEL_COLORS[4], "--")
        style(ax[15], "Air pressures", "bar"); legend(ax[15], ncol=2)
        line(ax[16], t, c["retarder_power_kw"], "retarder power", WHEEL_COLORS[3])
        line(ax[16], t, c["engine_brake_torque"] * c["rpm"] * np.pi / 30 / 1000, "engine brake power", WHEEL_COLORS[2])
        style(ax[16], "Endurance braking power", "kW"); legend(ax[16])
    if has_tr:
        line(ax[17], t, c["articulation_deg"], "articulation", WHEEL_COLORS[0])
        line(ax[17], t, c["kingpin_fz"] * 1e-4, "kingpin vertical load ×10 kN", WHEEL_COLORS[1])
        line(ax[17], t, c["kingpin_fx"] * 1e-4, "kingpin longitudinal ×10 kN", WHEEL_COLORS[2])
        style(ax[17], "Fifth wheel", "deg / 10 kN"); legend(ax[17])
        wheel_panel(ax[18], t, c, trailer, "fz", "Trailer wheel load Fz", "kN", 1e-3)
        wheel_panel(ax[19], t, c, trailer, "slip", "Trailer slip ratio κ'", "-", 1.0)
        wheel_panel(ax[20], t, c, trailer, "fy", "Trailer tire Fy", "kN", 1e-3)
    elif "air_front_bar" in c:
        line(ax[17], t, c["clutch_temp_c"], "clutch temperature", WHEEL_COLORS[0])
        style(ax[17], "Clutch", "°C")

    for i, a in enumerate(ax):
        if i != 14:
            a.set_xlabel("t [s]", fontsize=7, color=MUTED)
    fig.suptitle(f"{path.stem}   config={meta.get('config_id', '?')}   commit={meta.get('commit', '?')}",
                 fontsize=11, color=INK, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.985))
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / (path.stem + ".png")
    fig.savefig(out, dpi=80)
    plt.close(fig)
    return out


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("inputs", nargs="+", type=Path)
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args(argv)
    files: list[Path] = []
    for i in args.inputs:
        files += sorted(i.glob("*.csv")) if i.is_dir() else [i]
    if not files:
        print("no CSV files found", file=sys.stderr)
        return 1
    for f in files:
        out = plot_csv(f, args.out or f.parent)
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
