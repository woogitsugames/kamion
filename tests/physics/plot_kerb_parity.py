# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib>=3.8", "numpy>=1.26"]
# ///
"""Overlay runner vs Unity telemetry for the kerb-strike parity test (KerbStrikeParityTests).

Usage:
    uv run tests/physics/plot_kerb_parity.py <runner.csv> <unity.csv> [<unity2.csv> ...] --out <png>

Panels: front-left / rear-left / trailer axle 1 left Fz, front-left suspension compression + tyre deflection,
body pitch. The Unity CSV is written by the PlayMode test to artifacts/physics/unity-kerb/ (runner column names).
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#8b5cf6"]
STYLES = ["-", "--", ":", "-."]


def load(p: Path) -> dict[str, np.ndarray]:
    with open(p, newline="") as f:
        rows = [r for r in csv.reader(f) if r and not r[0].startswith("#")]
    head, data = rows[0], rows[1:]
    out = {}
    for i, h in enumerate(head):
        try:
            out[h] = np.array([float(r[i]) for r in data if len(r) > i and r[i] not in ("", "config_id")])
        except ValueError:
            pass
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--t0", type=float, default=1.5)
    ap.add_argument("--t1", type=float, default=4.0)
    a = ap.parse_args()
    runs = [(p.stem, load(p)) for p in a.csv]
    panels = [("front_L_fz", "Front left Fz", "kN", 1e-3), ("rear_L_fz", "Rear left Fz", "kN", 1e-3),
              ("T_axle1_L_fz", "Trailer axle 1 left Fz", "kN", 1e-3), ("front_L_comp", "Front left suspension compression", "m", 1),
              ("front_L_tire_defl", "Front left tyre deflection", "m", 1), ("pitch_deg", "Body pitch", "deg", 1)]
    fig, axes = plt.subplots(2, 3, figsize=(15, 7))
    for ax, (k, title, unit, sc) in zip(axes.ravel(), panels):
        for i, (name, c) in enumerate(runs):
            if k not in c:
                continue
            t = c["t"]
            m = (t >= a.t0) & (t <= a.t1)
            ax.plot(t[m], c[k][m] * sc, STYLES[i % 4], color=COLORS[i % 4], linewidth=1.2, label=name)
        ax.set_title(title, fontsize=10, loc="left")
        ax.set_ylabel(unit, fontsize=8)
        ax.set_xlabel("t [s]", fontsize=8)
        ax.grid(alpha=0.25)
    axes[0, 0].legend(fontsize=7)
    fig.tight_layout()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out, dpi=80)
    print(a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
