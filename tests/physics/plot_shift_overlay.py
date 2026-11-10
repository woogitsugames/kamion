# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib>=3.8", "numpy>=1.26"]
# ///
"""Overlay AMT shift behaviour of two or more runner CSVs (e.g. before / after a shift-strategy change, ADR 0024).

Usage:
    uv run tests/physics/plot_shift_overlay.py <a.csv> <b.csv> [...] --labels before after --out <png> [--tmax 32]

Panels: speed, engine rpm, engaged gear (0 = neutral during a shift), longitudinal acceleration. 960 x 900 px.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

COLORS = ["#8a8980", "#2a78d6", "#eb6834", "#1baf7a"]
WIDTHS = [2.2, 1.3, 1.3, 1.3]
INK = "#3a3a38"
GRID = "#e4e3dd"
PANELS = [("speed_kmh", "speed [km/h]"), ("rpm", "engine [rpm]"), ("gear", "gear"), ("a_long", "a_long [m/s²]")]


def load(p: Path) -> dict[str, np.ndarray]:
    with open(p, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    head, body = rows[0], rows[1:]
    want = {"t"} | {k for k, _ in PANELS}
    out = {}
    for i, h in enumerate(head):
        if h in want:
            out[h] = np.array([float(r[i]) for r in body])
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="+", type=Path)
    ap.add_argument("--labels", nargs="+")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--tmax", type=float, default=32.0)
    ap.add_argument("--title", default="")
    a = ap.parse_args()
    labels = a.labels or [p.stem for p in a.csv]
    data = [load(p) for p in a.csv]
    fig, axes = plt.subplots(len(PANELS), 1, figsize=(9.6, 9.0), dpi=100, sharex=True)
    for ax, (key, name) in zip(axes, PANELS):
        for i, d in enumerate(data):
            m = d["t"] <= a.tmax
            kw = dict(color=COLORS[i % 4], lw=WIDTHS[i % 4], label=labels[i])
            if key == "gear":
                ax.step(d["t"][m], d[key][m], where="post", **kw)
            else:
                ax.plot(d["t"][m], d[key][m], **kw)
        ax.set_ylabel(name, color=INK, fontsize=9)
        ax.grid(True, color=GRID, lw=0.6)
        ax.tick_params(labelsize=8, colors=INK)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    axes[0].legend(frameon=False, fontsize=9, loc="upper left")
    axes[-1].set_xlabel("t [s]", color=INK, fontsize=9)
    if a.title:
        fig.suptitle(a.title, fontsize=11, color=INK)
    fig.tight_layout()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out)
    print(a.out)


if __name__ == "__main__":
    main()
