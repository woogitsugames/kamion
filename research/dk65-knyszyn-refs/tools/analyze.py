"""Cross-profile analysis: peaks (paint lines) and asphalt edges (strong steps) from *_prof.npy (0.1 m/px, centre = OSM axis)."""
import sys, glob, json, numpy as np
RES = 0.1
def smooth(a, k=3):
    return np.convolve(a, np.ones(k) / k, mode="same")
out = {}
for f in sorted(glob.glob(sys.argv[1] + "/*_prof.npy")):
    pid = f.split("/")[-1][:-9]
    p = np.load(f); n = len(p); c = n // 2
    s = smooth(p, 3)
    base = np.array([np.median(s[max(0, i - 8):i + 9]) for i in range(n)])
    peaks = []
    for i in range(2, n - 2):
        if s[i] == max(s[i - 2:i + 3]) and s[i] - min(s[max(0, i - 6):i]) > 10 and s[i] - min(s[i + 1:i + 7]) > 10:
            peaks.append((round((i - c) * RES, 2), int(s[i] - base[i])))
    g = np.gradient(smooth(p, 7))
    # asphalt plateau: region around the axis whose smoothed brightness is within band of axis-centred median
    core = np.median(p[c - 15:c + 15])
    steps = sorted([(round((i - c) * RES, 1), round(float(g[i]), 1)) for i in range(5, n - 5) if abs(g[i]) == max(abs(g[i - 5:i + 6])) and abs(g[i]) > 4], key=lambda t: t[0])
    out[pid] = {"peaks_m": peaks, "steps_m": steps, "core_gray": float(core)}
    print(pid, "core", int(core))
    print("  peaks", [pk for pk in peaks if abs(pk[0]) < 8])
    print("  steps", [st for st in steps if abs(st[0]) < 9])
json.dump(out, open(sys.argv[1] + "/analysis.json", "w"), indent=1)
