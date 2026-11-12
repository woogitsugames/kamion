# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib>=3.8"]
# ///
"""ADR 0149: plots of the finger-in-the-loop evidence written by
`dotnet run -c Release --project tools/physics-runner/Runner -- --touch-evidence <dir>`.

Usage: uv run tests/physics/plot_touch_feel.py <dir>
Writes <dir>/gain_curve.png, replay35.png, lc35.png, lc45.png, sweep35.png (before = ADR 0135 curve, after = shipped).
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

BEFORE, AFTER = "#9a9a9a", "#1f5fbf"


def read(p: Path) -> dict[str, list[float]]:
    rows = list(csv.DictReader(p.open()))
    return {k: [float(r[k]) for r in rows] for k in rows[0]}


def gain_curve(d: Path) -> None:
    g = read(d / "gain_margin.csv")
    fig, ax = plt.subplots(3, 1, figsize=(8, 9), sharex=True)
    for a, (kb, ka, title) in zip(ax, [
        ("cab_deg_per_mm_before", "cab_deg_per_mm_after", "cab-wheel deg per mm of thumb"),
        ("lat_accel_per_mm_before", "lat_accel_per_mm_after", "kinematic lateral accel per mm [m/s2]"),
        ("pio_onset_gain_before_mm_per_m", "pio_onset_gain_after_mm_per_m", "PIO onset: thumb gain [mm/m] (higher = more margin)"),
    ]):
        a.plot(g["kmh"], g[kb], "o-", color=BEFORE, label="before (ADR 0135)")
        a.plot(g["kmh"], g[ka], "o-", color=AFTER, label="after (ADR 0149)")
        a.set_title(title, fontsize=10, loc="left")
        a.grid(alpha=0.3)
    ax[0].legend(fontsize=8)
    ax[1].axvspan(30, 40, color="#f0c040", alpha=0.25, label="owner video 30-41 km/h")
    ax[1].legend(fontsize=8)
    ax[-1].set_xlabel("speed [km/h]")
    fig.tight_layout()
    fig.savefig(d / "gain_curve.png", dpi=90)


def traces(d: Path, name: str, title: str) -> None:
    b, a = read(d / f"{name}_before.csv"), read(d / f"{name}_after.csv")
    panels = [("finger_mm", "thumb x [mm]"), ("column_deg", "cab wheel [deg]"), ("roadwheel_deg", "road wheel [deg]"),
              ("lat_m", "lateral offset [m]"), ("heading_deg", "heading [deg]"), ("lat_accel_ms2", "lateral accel [m/s2]"),
              ("articulation_deg", "articulation [deg]")]
    fig, ax = plt.subplots(len(panels), 1, figsize=(8, 13), sharex=True)
    for x, (k, lab) in zip(ax, panels):
        x.plot(b["t"], b[k], color=BEFORE, label="before")
        x.plot(a["t"], a[k], color=AFTER, label="after")
        if k == "lat_m" and any(v != 0 for v in a["target_m"]):
            x.plot(a["t"], a["target_m"], ":", color="black", lw=0.8, label="path")
        x.set_title(lab, fontsize=9, loc="left")
        x.grid(alpha=0.3)
    ax[0].legend(fontsize=8)
    ax[-1].set_xlabel("t [s]")
    fig.suptitle(title, fontsize=10)
    fig.tight_layout()
    fig.savefig(d / f"{name}.png", dpi=80)


def sweep(d: Path, kmh: int) -> None:
    gains = [1, 2, 3, 4, 5, 6, 8]
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5), sharey=True)
    for x, ph in zip(ax, ["before", "after"]):
        for gi, g in enumerate(gains):
            p = d / "sweep" / f"sweep{kmh}_g{g:.1f}_{ph}.csv"
            if not p.exists():
                continue
            r = read(p)
            x.plot(r["t"], r["lat_m"], lw=1, color=plt.cm.viridis(gi / (len(gains) - 1)), label=f"{g} mm/m")
        x.set_title(f"{kmh} km/h, lane change 3.5 m, {ph}", fontsize=10)
        x.set_ylim(-1, 8)
        x.grid(alpha=0.3)
        x.set_xlabel("t [s]")
    ax[0].set_ylabel("lateral offset [m]")
    ax[1].legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(d / f"sweep{kmh}.png", dpi=80)


def main() -> int:
    d = Path(sys.argv[1])
    gain_curve(d)
    traces(d, "replay35", "Replay: owner's thumb 4.4 mm left for 0.66 s at 35 km/h, then released (video 17.57-18.23 s), 40 t")
    traces(d, "lc35", "Lane change 3.5 m at 35 km/h, human model (delay 0.25 s, thumb gain 4 mm/m), 40 t")
    traces(d, "lc45", "Lane change 3.5 m at 45 km/h, human model (delay 0.25 s, thumb gain 4 mm/m), 40 t")
    sweep(d, 35)
    sweep(d, 45)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
