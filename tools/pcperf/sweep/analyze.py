"""pc-budget-s23 (D83): aggregate the sweep (runs/<point>__<cfg>/pc-report.json) and fit frame cost vs tris/draws per tier.

usage: uv run --no-project --with numpy python tools/pcperf/sweep/analyze.py <artifacts/pc-budget-s23>
writes <dir>/summary.csv and <dir>/fit.json; prints a markdown table.
"""
import csv, json, sys
from datetime import datetime
from pathlib import Path
import numpy as np

root = Path(sys.argv[1])
rows = []
for d in sorted((root / "runs").iterdir()):
    rep = d / "pc-report.json"
    if not rep.exists():
        continue
    r = json.loads(rep.read_text(encoding="utf-8"))
    meta = json.loads((d / "pc-metrics-meta.json").read_text(encoding="utf-8-sig"))
    m = r["metrics"]
    point, cfg = d.name.split("__")
    ts = datetime.strptime(meta["timestamp"], "%Y%m%d-%H%M%S")
    g = lambda k, q="p50": (m.get(k) or {}).get(q)
    rows.append(dict(
        point=point, cfg=cfg, tier=r["display"].get("qualityName"), start=ts.strftime("%m-%d %H:%M"),
        # another agent's full pytest (CPU) ran ~02:41-03:40 on 17.11 (lead's note)
        contended=int(ts.day == 17 and (ts.hour, ts.minute) <= (3, 40)),
        frame_p50=g("frame_ms"), frame_p95=g("frame_ms", "p95"), frame_p99=g("frame_ms", "p99"),
        cpu_p50=g("cpu_main_ms"), gpu_p50=g("gpu_ms"), gpu_samples=g("gpu_ms", "samples"), frames=m.get("frames_window"),
        draws_p50=g("draw_calls"), draws_p95=g("draw_calls", "p95"), setpass_p50=g("setpass"),
        tris_p50=g("tris"), tris_p95=g("tris", "p95"),
        vram_peak=(m.get("process") or {}).get("gpu_dedicated_mb", {}).get("peak") if isinstance(m.get("process"), dict) else None,
        verdict=r.get("verdict"),
    ))
keys = list(rows[0].keys())
with open(root / "summary.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, keys); w.writeheader(); w.writerows(rows)

fit = {}
rng = np.random.default_rng(83)
for tier in ("Low", "Medium", "High", "Ultra"):
    sub = [x for x in rows if x["cfg"] == f"unc-{tier}"]
    T = np.array([x["tris_p50"] for x in sub]) / 1e6
    D = np.array([x["draws_p50"] for x in sub]) / 1e3
    Y = np.array([x["frame_p50"] for x in sub])
    C = np.array([x["cpu_p50"] for x in sub])
    def lsq(y, X):
        return np.linalg.lstsq(X, y, rcond=None)[0]
    X2 = np.column_stack([np.ones_like(T), T, D])
    coef = lsq(Y, X2)
    boots = []
    for _ in range(2000):
        i = rng.integers(0, len(sub), len(sub))
        boots.append(lsq(Y[i], X2[i]))
    boots = np.array(boots)
    res = Y - X2 @ coef
    # single-variable fits (tris and draws are correlated - report both)
    ct = lsq(Y, np.column_stack([np.ones_like(T), T])); cd = lsq(Y, np.column_stack([np.ones_like(D), D]))
    fit[tier] = dict(
        n=len(sub), corr_tris_draws=float(np.corrcoef(T, D)[0, 1]),
        frame_ms=dict(a=coef[0], b_per_Mtris=coef[1], c_per_kdraws=coef[2],
                      ci90=dict(zip(("a", "b", "c"), [list(np.percentile(boots[:, k], [5, 95])) for k in range(3)])),
                      rmse=float(np.sqrt(np.mean(res ** 2)))),
        frame_vs_tris_only=dict(a=ct[0], b_per_Mtris=ct[1]),
        frame_vs_draws_only=dict(a=cd[0], c_per_kdraws=cd[1]),
        cpu_share=float(np.median(C / Y)),
        range=dict(tris_M=[float(T.min()), float(T.max())], kdraws=[float(D.min()), float(D.max())],
                   frame_ms=[float(Y.min()), float(Y.max())]),
    )
fit = json.loads(json.dumps(fit, default=float))
(root / "fit.json").write_text(json.dumps(fit, indent=2), encoding="utf-8")

print("| punkt | cfg | start | obc. | p50 | p95 | p99 | CPU p50 | GPU p50 | draws p50/p95 | tris p50/p95 [M] | werdykt |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|")
for x in rows:
    print(f"| {x['point']} | {x['cfg']} | {x['start']} | {'T' if x['contended'] else ''} | {x['frame_p50']:.2f} | {x['frame_p95']:.2f} | "
          f"{x['frame_p99']:.2f} | {x['cpu_p50'] or 0:.2f} | {x['gpu_p50'] or 0:.2f} | {x['draws_p50']:.0f}/{x['draws_p95']:.0f} | "
          f"{x['tris_p50']/1e6:.2f}/{x['tris_p95']/1e6:.2f} | {x['verdict']} |")
print(json.dumps(fit, indent=1))
