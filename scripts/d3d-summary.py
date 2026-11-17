"""Tabela D3D11 vs D3D12 z artifacts/full-build-s23/d3d-ab/*/pc-report.json + cykle wyjścia z d3d-ab.log."""
import json, sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\matma\Documents\Claude\kamion\artifacts\full-build-s23\d3d-ab")
rows = []
for rep in sorted(root.glob("*/pc-report.json")):
    r = json.loads(rep.read_text(encoding="utf-8"))
    m = r["metrics"]; ft = m.get("frame_ms") or {}
    api = (r.get("system") or {}).get("graphicsApi")
    over = m.get("frames_over") or {}
    pr = m.get("process") or {}
    rows.append((rep.parent.name, api, r["verdict"], m.get("frames_window"), ft.get("p50"), ft.get("p95"), ft.get("p99"), ft.get("max"),
                 (over.get("100") or {}).get("count"), (pr.get("private_mb") or {}).get("peak"), (pr.get("gpu_dedicated_mb") or {}).get("peak"),
                 (m.get("cpu_main_ms") or {}).get("p50"), (m.get("gpu_ms") or {}).get("p50")))
print("| run | API (run.json) | werdykt | klatki | p50 | p95 | p99 | max | >100ms | private MB | VRAM MB | CPU p50 | GPU p50 |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
f = lambda v: "-" if v is None else (f"{v:.2f}" if isinstance(v, float) else str(v))
for row in rows:
    print("| " + " | ".join(f(v) for v in row) + " |")
log = root / "d3d-ab.log"
if log.exists():
    print()
    for line in log.read_text(encoding="utf-8-sig").splitlines():
        if "-quit" in line:
            print("- " + line)
