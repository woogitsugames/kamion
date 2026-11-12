"""CLI for the world validator (M37).

    uv run --project tools/worldgen tools/worldgen/validate/run.py --region bialystok-industrial-c \
        [--out docs/reports/world-validator/bialystok-industrial-c] [--prev <world_validator.json>]

Reads Data/Regions/<region>/** (read-only), writes report.md / report.html / world_validator.json /
control_cameras.json into --out. Exit code 0 always (it is a report, not a gate); --fail-on-error makes
it exit 1 when any severity=error finding exists (CI use).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from validate import buildings, common, continuity, overlaps, report, signs, terrain  # noqa: E402


def run(region_id: str, out_dir: Path, prev_path: Path | None = None) -> dict:
    t0 = time.perf_counter()
    w = common.load_world(region_id)
    checks = [
        ("overlaps", overlaps.check),
        ("continuity", continuity.check),
        ("terrain", terrain.check),
        ("signs", signs.check),
        ("buildings", buildings.check),
    ]
    findings: list[common.Finding] = []
    per_check = {}
    for name, fn in checks:
        fs = fn(w)
        per_check[name] = len(fs)
        findings.extend(fs)
    findings = common.finalize(w, findings)
    runtime_s = time.perf_counter() - t0

    prev = None
    if prev_path is not None:
        prev = json.loads(prev_path.read_text(encoding="utf-8"))

    out_dir.mkdir(parents=True, exist_ok=True)
    origin_z = 131.14  # region.yaml origin z (PL-EVRF2007-NH); per-finding z needs Data/raw (not in git)
    import yaml
    reg_yaml = yaml.safe_load((common.REPO_ROOT / "Data" / "Regions" / region_id / "region.yaml").read_text(encoding="utf-8"))
    origin_z = float(reg_yaml.get("origin", {}).get("z", origin_z))

    report.write_json(w, findings, out_dir, runtime_s=runtime_s, prev=prev)
    report.write_md(w, findings, out_dir, runtime_s=runtime_s)
    report.write_html(w, findings, out_dir)
    report.write_cameras(w, findings, out_dir, origin_z)
    return {"world": w, "findings": findings, "runtime_s": runtime_s, "per_check": per_check,
            "summary": common.summarize(findings), "out_dir": out_dir}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--region", required=True)
    ap.add_argument("--out", default=None, help="output dir (default docs/reports/world-validator/<region>)")
    ap.add_argument("--prev", default=None, help="previous world_validator.json for the (b) diff")
    ap.add_argument("--fail-on-error", action="store_true")
    a = ap.parse_args()
    out = Path(a.out) if a.out else common.REPO_ROOT / "docs" / "reports" / "world-validator" / a.region
    res = run(a.region, out, Path(a.prev) if a.prev else None)
    s = res["summary"]
    print(f"region {a.region}: {s['count']} findings in {res['runtime_s']:.1f} s "
          f"(error {s['by_severity'].get('error', 0)}, warn {s['by_severity'].get('warn', 0)}, "
          f"info {s['by_severity'].get('info', 0)}; on route G3: {sum(s['on_route_by_category'].values())})")
    for k, v in s["by_category"].items():
        print(f"  {k:32s} {v:5d}  (on route {s['on_route_by_category'].get(k, 0)})")
    print(f"per check: {res['per_check']}")
    print(f"out: {res['out_dir']}")
    if a.fail_on_error and s["by_severity"].get("error", 0):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
