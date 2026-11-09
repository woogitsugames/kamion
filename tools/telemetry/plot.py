# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib>=3.8", "numpy>=1.26"]
# ///
"""Plot vehicle-physics telemetry CSVs (docs/04 section 4) to PNG.

Usage:
    uv run tools/telemetry/plot.py artifacts/physics/<run>/            # every CSV in the folder
    uv run tools/telemetry/plot.py artifacts/physics/<run>/brake_80_0_dry.csv [--out DIR]

One PNG per CSV, written next to the CSV unless --out is given. Small multiples: one measure per
panel, one y-axis per panel (no dual axes); wheels use a fixed categorical order FL, FR, RL, RR.
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
WHEEL_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
INK = "#3a3a38"
MUTED = "#8a8980"
GRID = "#e4e3dd"


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
    return cols, meta


def wheel_names(cols: dict[str, np.ndarray]) -> list[str]:
    return [c[: -len("_fz")] for c in cols if c.endswith("_fz")]


def style(ax, title: str, unit: str) -> None:
    ax.set_title(f"{title} [{unit}]" if unit else title, fontsize=9, color=INK, loc="left")
    ax.grid(True, color=GRID, linewidth=0.6)
    ax.tick_params(labelsize=7, colors=MUTED)
    for s in ax.spines.values():
        s.set_color(GRID)


def line(ax, t, y, label=None, color=WHEEL_COLORS[0], ls="-"):
    ax.plot(t, y, color=color, linewidth=1.2, label=label, linestyle=ls)


def plot_csv(path: Path, out_dir: Path) -> Path:
    c, meta = load(path)
    t = c["t"]
    wheels = wheel_names(c)
    fig, axes = plt.subplots(5, 3, figsize=(16, 17), sharex=False)
    ax = axes.ravel()

    line(ax[0], t, c["speed_kmh"]); style(ax[0], "Speed", "km/h")
    line(ax[1], t, c["throttle_in"], "throttle in", WHEEL_COLORS[0])
    line(ax[1], t, c["throttle_eff"], "throttle eff", WHEEL_COLORS[0], "--")
    line(ax[1], t, c["brake_in"], "brake in", WHEEL_COLORS[1])
    line(ax[1], t, c["brake_demand"], "brake demand (incl. hill hold)", WHEEL_COLORS[1], "--")
    line(ax[1], t, c["clutch_cmd"], "clutch cmd", WHEEL_COLORS[2])
    style(ax[1], "Pedals / clutch", "0..1"); ax[1].legend(fontsize=7, frameon=False)
    line(ax[2], t, c["rpm"]); style(ax[2], "Engine speed", "rpm")
    ax[3].step(t, c["gear"], where="post", color=WHEEL_COLORS[0], linewidth=1.2); style(ax[3], "Gear (0=N, -1=R)", "")
    line(ax[4], t, c["engine_torque"], "engine net", WHEEL_COLORS[0])
    line(ax[4], t, c["clutch_torque"], "clutch transmitted", WHEEL_COLORS[1])
    style(ax[4], "Torque", "N m"); ax[4].legend(fontsize=7, frameon=False)
    line(ax[5], t, c["a_long"], "longitudinal", WHEEL_COLORS[0])
    line(ax[5], t, c["a_lat"], "lateral", WHEEL_COLORS[1])
    style(ax[5], "Chassis acceleration (vehicle frame)", "m/s²"); ax[5].legend(fontsize=7, frameon=False)

    for k, (key, title, unit, scale) in enumerate([
        ("fz", "Wheel normal load Fz", "kN", 1e-3),
        ("fx", "Tire Fx", "kN", 1e-3),
        ("fy", "Tire Fy", "kN", 1e-3),
        ("slip", "Slip ratio κ' (transient)", "-", 1.0),
        ("alpha_deg", "Slip angle α' (transient)", "deg", 1.0),
        ("comp", "Suspension compression (vs static)", "m", 1.0),
    ]):
        a = ax[6 + k]
        for i, w in enumerate(wheels):
            line(a, t, c[f"{w}_{key}"] * scale, w, WHEEL_COLORS[i % len(WHEEL_COLORS)])
        style(a, title, unit)
        a.legend(fontsize=7, frameon=False, ncol=4)

    line(ax[12], t, c["yaw_rate_dps"]); style(ax[12], "Yaw rate", "deg/s")
    line(ax[13], t, c["pitch_deg"], "body pitch", WHEEL_COLORS[0])
    line(ax[13], t, c["roll_deg"], "body roll", WHEEL_COLORS[1])
    line(ax[13], t, c["cab_pitch_deg"], "cab pitch (rel.)", WHEEL_COLORS[2])
    line(ax[13], t, c["cab_roll_deg"], "cab roll (rel.)", WHEEL_COLORS[3])
    style(ax[13], "Attitude", "deg"); ax[13].legend(fontsize=7, frameon=False, ncol=2)
    ax[14].plot(c["x"], c["z"], color=WHEEL_COLORS[0], linewidth=1.2)
    ax[14].set_aspect("equal", adjustable="datalim")
    style(ax[14], "Trajectory (vehicle origin) x→z", "m")

    for a in ax[:14]:
        a.set_xlabel("t [s]", fontsize=7, color=MUTED)
    fig.suptitle(f"{path.stem}   config={meta.get('config_id', '?')}   commit={meta.get('commit', '?')}",
                 fontsize=11, color=INK, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.98))
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / (path.stem + ".png")
    fig.savefig(out, dpi=90)
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
