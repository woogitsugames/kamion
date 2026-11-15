"""Overlay old vs new golden telemetry (ADR 0201b review aid).

Usage: uv run --with matplotlib python tests/physics/plot_golden_overlay.py <old_dir> <new_dir> <out_dir> name1 [name2 ...]
"""
import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

COLS = ["speed_kmh", "rpm", "gear", "a_long", "front_L_fz", "rear_L_fz", "rear_L_p_bar", "kingpin_fz", "yaw_rate_dps", "articulation_deg"]


def load(p: Path):
    with p.open() as f:
        rows = list(csv.DictReader(f))
    return {k: [float(r[k]) for r in rows] for k in rows[0]}


def main() -> None:
    old, new, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    for name in sys.argv[4:]:
        a, b = load(old / f"{name}.csv"), load(new / f"{name}.csv")
        cols = [c for c in COLS if c in a and (max(a[c]) - min(a[c]) > 1e-9 or max(b[c]) - min(b[c]) > 1e-9)]
        fig, axs = plt.subplots(len(cols), 1, figsize=(9, 1.6 * len(cols)), sharex=True)
        for ax, c in zip(axs, cols):
            ax.plot(a["t"], a[c], color="#888888", lw=1.4, label="golden R3 (before)")
            ax.plot(b["t"], b[c], color="#1f5fbf", lw=1.0, label="ADR 0201b (after)")
            ax.set_ylabel(c, fontsize=8)
            ax.tick_params(labelsize=7)
            ax.grid(alpha=0.3)
        axs[0].legend(fontsize=7, loc="upper right")
        axs[0].set_title(name, fontsize=9)
        axs[-1].set_xlabel("t [s]")
        fig.tight_layout()
        fig.savefig(out / f"golden-{name}.png", dpi=90)
        plt.close(fig)


if __name__ == "__main__":
    main()
