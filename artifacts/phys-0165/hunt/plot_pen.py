# ADR 0165: body penetration per body vs time (columns body_pen_tractor_m / body_pen_trailer_m), with the scenario limits.
import csv, sys, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
out = sys.argv[1]; files = sys.argv[2:]
fig, axs = plt.subplots(len(files), 1, figsize=(10, 3 * len(files)), squeeze=False)
for ax, f in zip(axs[:, 0], files):
    r = list(csv.DictReader(open(f)))
    t = [float(x["t"]) for x in r]
    ax.plot(t, [float(x["body_pen_tractor_m"]) for x in r], label="tractor")
    ax.plot(t, [float(x["body_pen_trailer_m"]) for x in r], label="trailer")
    for y, l in ((0.10, "peak limit 0.10"), (0.035, "rest limit 0.035")): ax.axhline(y, ls="--", lw=0.8, color="gray"); ax.text(t[-1], y, l, ha="right", va="bottom", fontsize=7)
    ax.set_title(f.replace("\\", "/").split("/")[-1], fontsize=9); ax.set_ylabel("penetration [m]"); ax.set_xlabel("t [s]"); ax.legend(fontsize=7); ax.grid(alpha=.3)
fig.tight_layout(); fig.savefig(out, dpi=90)
