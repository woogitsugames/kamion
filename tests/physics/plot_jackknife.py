# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib>=3.8", "numpy>=1.26"]
# ///
"""ADR 0228 before/after plots: articulation and tractor-trailer contact (jackknife scenarios), heave of the 0.5 m drop.

Usage:
    uv run tests/physics/plot_jackknife.py artifacts/jackknife-0228
Expects <dir>/before/*.csv (runner with --no-coupling-contact --elastic-landing) and <dir>/after/*.csv; writes <dir>/png/.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

BEFORE, AFTER = "#8a8980", "#2a78d6"
INK, GRID = "#3a3a38", "#e4e3dd"
LIMIT = "#eb6834"


def load(p: Path) -> dict[str, np.ndarray]:
    with p.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    out = {}
    for k in rows[0]:
        try:
            out[k] = np.array([float(r[k]) for r in rows])
        except ValueError:
            pass
    return out


def style(ax, title, ylabel):
    ax.set_title(title, fontsize=9, color=INK, loc="left")
    ax.set_ylabel(ylabel, fontsize=8, color=INK)
    ax.grid(True, color=GRID, linewidth=0.6)
    ax.tick_params(labelsize=7, colors=INK)
    for s in ax.spines.values():
        s.set_color(GRID)


def jackknife(root: Path, out: Path, sid: str, limit_deg: float):
    b, a = root / "before" / f"{sid}.csv", root / "after" / f"{sid}.csv"
    if not (b.exists() and a.exists()):
        return
    B, A = load(b), load(a)
    fig, axs = plt.subplots(4, 1, figsize=(8, 9), sharex=True)
    ax = axs[0]
    ax.plot(B["t"], np.abs(B["articulation_deg"]), color=BEFORE, label="before (angular 90 deg stop)")
    ax.plot(A["t"], np.abs(A["articulation_deg"]), color=AFTER, label="after (cab / trailer body contact)")
    ax.axhline(limit_deg, color=LIMIT, linewidth=0.8, linestyle="--", label=f"geometric first contact {limit_deg:.2f} deg")
    ax.legend(fontsize=7, frameon=False)
    style(ax, f"{sid}: |articulation|", "deg")
    style(axs[1], "tractor-trailer contact penetration (after)", "m")
    axs[1].plot(A["t"], A["coupling_pen_m"], color=AFTER)
    style(axs[2], "contact force on the trailer (after)", "kN")
    axs[2].plot(A["t"], A["coupling_force_kn"], color=AFTER)
    style(axs[3], "body angular rate |w| (tractor solid, trailer dashed)", "deg/s")
    axs[3].plot(B["t"], B["tractor_ang_rate_dps"], color=BEFORE)
    axs[3].plot(A["t"], A["tractor_ang_rate_dps"], color=AFTER)
    axs[3].plot(A["t"], A["trailer_ang_rate_dps"], color=AFTER, linestyle="--")
    axs[3].set_xlabel("t [s]", fontsize=8, color=INK)
    fig.tight_layout()
    fig.savefig(out / f"{sid}.png", dpi=110)
    plt.close(fig)


def drop(root: Path, out: Path, sid: str):
    b, a = root / "before" / f"{sid}.csv", root / "after" / f"{sid}.csv"
    if not (b.exists() and a.exists()):
        return
    B, A = load(b), load(a)
    fig, axs = plt.subplots(3, 1, figsize=(8, 7), sharex=True)
    style(axs[0], f"{sid}: tractor origin height (0 = static ride height)", "m")
    axs[0].plot(B["t"], B["y"], color=BEFORE, label="before (elastic bump stops)")
    axs[0].plot(A["t"], A["y"], color=AFTER, label="after (bump-stop unloading hysteresis)")
    axs[0].legend(fontsize=7, frameon=False)
    style(axs[1], "rear-left suspension compression (static 0)", "m")
    axs[1].plot(B["t"], B["rear_L_comp"], color=BEFORE)
    axs[1].plot(A["t"], A["rear_L_comp"], color=AFTER)
    style(axs[2], "rear-left wheel load", "kN")
    axs[2].plot(B["t"], B["rear_L_fz"] / 1000, color=BEFORE)
    axs[2].plot(A["t"], A["rear_L_fz"] / 1000, color=AFTER)
    axs[2].set_xlabel("t [s]", fontsize=8, color=INK)
    fig.tight_layout()
    fig.savefig(out / f"{sid}.png", dpi=110)
    plt.close(fig)


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("artifacts/jackknife-0228")
    out = root / "png"
    out.mkdir(parents=True, exist_ok=True)
    limit = 117.12
    for sid in ("jackknife_fold_90_reverse_comb", "jackknife_fold_90_reverse_empty",
                "jackknife_fold_120_reverse_comb@laden40", "jackknife_fold_120_reverse_comb@empty",
                "jackknife_fast_fold_impact_comb@laden40", "jackknife_fast_fold_impact_comb@empty",
                "jackknife_reverse_countersteer_comb@laden40", "jackknife_reverse_countersteer_comb@empty",
                "jackknife_wet_curve_retarder_noabs@empty", "reverse_dock_s_maneuver_comb@laden40"):
        jackknife(root, out, sid, limit)
    for sid in ("drop_05m_comb@laden40", "drop_05m_comb@empty", "free_fall_drop_comb"):
        drop(root, out, sid)
    print("written", out)


if __name__ == "__main__":
    main()
