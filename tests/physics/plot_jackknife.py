# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib>=3.8", "numpy>=1.26"]
# ///
"""ADR 0228 before/after plots: articulation and tractor-trailer contact (jackknife scenarios), heave of the 0.5 m drop.

Usage:
    uv run tests/physics/plot_jackknife.py artifacts/jackknife-0228
Expects <dir>/before/*.csv (runner with --no-coupling-contact --elastic-landing) and <dir>/after/*.csv; writes <dir>/png/.

H11 (review P1 + FFB #132), same layout:
    uv run tests/physics/plot_jackknife.py artifacts/jackknife-0228/h11
before = PR head 27cb70566 (flat graybox trailer front, no feedback smoothing), after = rounded coupling front + contact
smoothing of the steering feedback. Plots the tight-turn / hard-stop scenarios and the wheel force feedback in the contact.
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


def ffb_replica(A: dict[str, np.ndarray]) -> np.ndarray:
    """ForceFeedbackModel (game/Assets/_Project/Input/ForceFeedback.cs, ADR 0263 defaults) driven from the CSV like
    DrivingLabBootstrap: aligning term + road feel, device at rest (no damping / friction / soft lock), 1:1 gearing.
    Returns the normalised output after the clamp and the 20/s slew limit."""
    t, mz, v = A["t"], A["aligning_torque"], A["v_fwd"]
    ratio, share, full, slew = 20.0, 1 - 0.85, 8.0, 20.0
    va = np.abs(v)
    x = np.clip((va - 0.3) / (2.5 - 0.3), 0, 1)
    fade = x * x * (3 - 2 * x)
    diff = A["front_R_fz"] - A["front_L_fz"]
    out = np.zeros_like(t)
    hp, prev, o = 0.0, diff[0], 0.0
    for i in range(len(t)):
        dt = t[i] - t[i - 1] if i else 0.01
        a = 0.05 / (0.05 + dt)
        hp = a * (hp + diff[i] - prev)
        prev = diff[i]
        tot = mz[i] / ratio * share * fade[i] + hp * 0.01 / ratio * share * fade[i]
        tgt = float(np.clip(tot / full, -1, 1))
        step = slew * dt
        o = min(tgt, o + step) if tgt > o else max(tgt, o - step)
        out[i] = o
    return out


def h11_ffb(root: Path, out: Path, sid: str):
    b, a = root / "before" / f"{sid}.csv", root / "after" / f"{sid}.csv"
    if not (b.exists() and a.exists()):
        return
    B, A = load(b), load(a)
    t0 = A["t"][np.argmax(A["coupling_contacts"] > 0)] if (A["coupling_contacts"] > 0).any() else 0.0
    sel_b, sel_a = (B["t"] > t0 - 1) & (B["t"] < t0 + 3), (A["t"] > t0 - 1) & (A["t"] < t0 + 3)
    fig, axs = plt.subplots(3, 1, figsize=(8, 7.5), sharex=True)
    style(axs[0], f"{sid}: contact force on the trailer", "kN")
    axs[0].plot(A["t"][sel_a], A["coupling_force_kn"][sel_a], color=AFTER)
    style(axs[1], "steered-axle aligning torque fed to the steering feedback", "N m")
    axs[1].plot(B["t"][sel_b], B["aligning_torque"][sel_b], color=BEFORE, label="before (raw tyre value)")
    axs[1].plot(A["t"][sel_a], A["aligning_torque"][sel_a], color=AFTER, label="after (smoothed while the bodies touch, lag 0.5 s)")
    axs[1].legend(fontsize=7, frameon=False)
    fb, fa = ffb_replica(B), ffb_replica(A)
    style(axs[2], "wheel force-feedback output (ForceFeedbackModel replica, defaults, slew 20/s)", "normalised")
    axs[2].plot(B["t"][sel_b], fb[sel_b], color=BEFORE)
    axs[2].plot(A["t"][sel_a], fa[sel_a], color=AFTER)
    axs[2].axvline(t0, color=LIMIT, linewidth=0.8, linestyle="--")
    axs[2].set_xlabel("t [s] (dashed: first contact)", fontsize=8, color=INK)
    fig.tight_layout()
    fig.savefig(out / f"ffb_{sid}.png", dpi=110)
    plt.close(fig)


def h11_turn(root: Path, out: Path, sid: str):
    b, a = root / "before" / f"{sid}.csv", root / "after" / f"{sid}.csv"
    if not (b.exists() and a.exists()):
        return
    B, A = load(b), load(a)
    fig, axs = plt.subplots(4, 1, figsize=(8, 9), sharex=True)
    style(axs[0], f"{sid}: |articulation|", "deg")
    axs[0].plot(B["t"], np.abs(B["articulation_deg"]), color=BEFORE, label="before (flat graybox front, swing 2.063 m)")
    axs[0].plot(A["t"], np.abs(A["articulation_deg"]), color=AFTER, label="after (rounded coupling front, swing 2.029 m)")
    axs[0].legend(fontsize=7, frameon=False)
    style(axs[1], "speed", "km/h")
    axs[1].plot(A["t"], A["speed_kmh"], color=AFTER)
    style(axs[2], "tractor-trailer contact force", "kN")
    axs[2].plot(B["t"], B["coupling_force_kn"], color=BEFORE)
    axs[2].plot(A["t"], A["coupling_force_kn"], color=AFTER)
    style(axs[3], "tractor pitch (solid) and trailer roll (dashed)", "deg")
    axs[3].plot(A["t"], A["pitch_deg"], color=AFTER)
    axs[3].plot(A["t"], A["trailer_roll_deg"], color=AFTER, linestyle="--")
    axs[3].set_xlabel("t [s]", fontsize=8, color=INK)
    fig.tight_layout()
    fig.savefig(out / f"turn_{sid}.png", dpi=110)
    plt.close(fig)


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("artifacts/jackknife-0228")
    out = root / "png"
    out.mkdir(parents=True, exist_ok=True)
    if (root / "after" / "jackknife_tight_turn_forward_comb@laden40.csv").exists():
        for sid in ("jackknife_tight_turn_forward_comb@laden40", "jackknife_tight_turn_forward_comb@empty",
                    "jackknife_tight_turn_forward_10_comb@laden40", "probe_turn57_stop_from15kmh@laden40",
                    "probe_turn55_stop_from20kmh@laden40", "probe_turn55_stop_from20kmh@empty"):
            h11_turn(root, out, sid)
        for sid in ("jackknife_fold_120_reverse_comb@laden40", "jackknife_fold_120_reverse_comb@empty",
                    "jackknife_fast_fold_impact_comb@laden40", "jackknife_fast_fold_impact_comb@empty"):
            h11_ffb(root, out, sid)
        print("written", out)
        return
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
