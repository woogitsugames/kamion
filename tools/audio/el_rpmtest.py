"""Does an engine loop sit at its prompt rpm? (ADR 0137, comparison with the GPT review)

For every ENG_* loop: prominence (dB over a +-25 Hz running median of the Welch spectrum) of the firing harmonics
k*f, k=1..6, (a) at the prompt rpm f = rpm/20 and (b) at the measured dominant line (el_analyze rpm_med/20).
A loop "is at" an rpm when >= 3 of the 6 harmonics stand >= 6 dB above the floor (1.5 % tolerance).
Writes artifacts/audio-el/rpmtest.json + .csv; prints a summary per prompt rpm.
"""
import csv
import json
from pathlib import Path

import numpy as np
import soundfile as sf

import el_analyze as ea

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "artifacts" / "audio-el"
SRC = ea.MAIN / "art-source" / "audio" / "elevenlabs"


def ladder(f, prom, f0):
    df = f[1] - f[0]
    out = []
    for k in range(1, 7):
        j = int(round(k * f0 / df))
        tol = max(1, int(round(0.015 * k * f0 / df)))
        out.append(float(prom[max(0, j - tol): j + tol + 1].max()))
    return out


rows = [r for r in json.loads((A / "analysis" / "analysis.json").read_text(encoding="utf-8")) if "rpm_nominal" in r]
res = []
for r in rows:
    d, fs = sf.read(SRC / r["file"], always_2d=True)
    f, p = ea.welch_db(d.mean(axis=1), fs, 1 << 16)
    prom = ea.prominence_db(f, p)
    ln = ladder(f, prom, r["rpm_nominal"] / 20)
    lm = ladder(f, prom, r["rpm_med"] / 20)
    res.append({"file": r["file"], "nominal": r["rpm_nominal"], "measured": round(r["rpm_med"]),
                "hits_nominal": sum(v >= 6 for v in ln), "hits_measured": sum(v >= 6 for v in lm),
                "ladder_nominal_db": [round(v, 1) for v in ln], "ladder_measured_db": [round(v, 1) for v in lm]})
(A / "rpmtest.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
with open(A / "rpmtest.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, list(res[0].keys()))
    w.writeheader()
    w.writerows(res)
for n in sorted({x["nominal"] for x in res}):
    s = [x for x in res if x["nominal"] == n]
    print(n, "files", len(s), "at prompt rpm (>=3/6):", sum(x["hits_nominal"] >= 3 for x in s),
          " at measured:", sum(x["hits_measured"] >= 3 for x in s),
          " measured median", int(np.median([x["measured"] for x in s])),
          " mean hits nominal %.1f measured %.1f" % (np.mean([x["hits_nominal"] for x in s]), np.mean([x["hits_measured"] for x in s])))
