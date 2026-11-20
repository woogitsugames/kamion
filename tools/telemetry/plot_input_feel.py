# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib>=3.8", "numpy>=1.26"]
# ///
"""Plot PC input-feel traces (physics-runner --input-feel, drive-feel-s24) to PNG, before vs after.

Usage:
    uv run tools/telemetry/plot_input_feel.py <before_dir> [<after_dir>] --cases keyhold50_high,keylc80 --out DIR

One PNG per case: command, cab wheel, road-wheel angle, lateral offset (and target), yaw rate, lateral acceleration
(tractor / trailer), articulation; before = grey, after = blue. One measure per panel, no dual axes.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

PANELS = [("cmd", "Komenda (klawisz -1/0/1 / gałka) [-]"), ("column_deg", "Kierownica w kabinie [deg]"),
          ("roadwheel_deg", "Kąt kół [deg]"), ("lat_m", "Przesunięcie boczne [m]"),
          ("yaw_rate_dps", "Prędkość odchylania [deg/s]"), ("lat_accel_ms2", "Przysp. boczne ciągnika [m/s²]"),
          ("trailer_lat_accel_ms2", "Przysp. boczne naczepy [m/s²]"), ("articulation_deg", "Kąt przegubu [deg]"),
          ("kmh", "Prędkość [km/h]")]


def load(p: Path) -> dict[str, np.ndarray]:
    with p.open() as f:
        rows = list(csv.DictReader(f))
    return {k: np.array([float(r[k]) for r in rows]) for k in rows[0]}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dirs", nargs="+", type=Path)
    ap.add_argument("--cases", required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    styles = [("#8a8980", "przed"), ("#2a78d6", "po")] if len(a.dirs) > 1 else [("#2a78d6", "")]
    for case in a.cases.split(","):
        fig, axs = plt.subplots(3, 3, figsize=(13, 8.5))
        for (color, label), d in zip(styles, a.dirs):
            p = d / f"{case}.csv"
            if not p.exists():
                continue
            t = load(p)
            for ax, (k, title) in zip(axs.flat, PANELS):
                ax.plot(t["t"], t[k], color=color, lw=1.3, label=label or None)
                if k == "lat_m" and np.any(t["target_m"] != 0):
                    ax.plot(t["t"], t["target_m"], color=color, lw=0.8, ls="--")
                ax.set_title(title, fontsize=9, loc="left")
                ax.grid(color="#e4e3dd", lw=0.6)
                ax.tick_params(labelsize=8)
        for ax in axs[-1]:
            ax.set_xlabel("t [s]", fontsize=8)
        if len(a.dirs) > 1:
            axs.flat[0].legend(fontsize=8, frameon=False)
        fig.suptitle(case, x=0.01, ha="left", fontsize=11)
        fig.tight_layout()
        fig.savefig(a.out / f"{case}.png", dpi=90)
        plt.close(fig)
        print(a.out / f"{case}.png")


if __name__ == "__main__":
    main()
