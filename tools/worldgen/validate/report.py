"""Check 5 (M37): report writers + extension (b) diff between runs.

Writes into the --out directory (never into Data/**):
  world_validator.json   full machine-readable findings + summary + params (input to --prev diffs);
  report.md              Markdown report: table per category, top 20 with E/N, id, chunk tile link;
  report.html            the same as a standalone HTML page;
  control_cameras.json   cameras for the leader's visual QA (format = generated/control_cameras.json:
                         pos / look_at / fov_deg / note / type, region-local metres, z from region origin).
"""

from __future__ import annotations

import html
import json
from pathlib import Path

from .common import DRIVER_EYE_M, PARAMS, SEVERITY_ORDER, Finding, World, summarize

SCHEMA = "truck-sim-pl/world-validator/1"
CAMERA_SCHEMA = "truck-sim-pl/world-validator-cameras/1"
TOP_N = 20


def _tile_link(w: World, chunk: str | None) -> str:
    if not chunk:
        return "-"
    for c in w.manifest.get("chunks", []):
        if c["id"] == chunk:
            return f"[{chunk}]({c['file']}#{chunk})"
    return chunk


def cameras(w: World, findings: list[Finding], origin_z: float = 131.14) -> list[dict]:
    """One control camera per top finding (errors and on-route first, capped): pos 15 m back from the
    finding towards the route / region centre, driver eye height above the origin z (WORKING_VALUE: the
    heightmap is not in git, so z is the region anchor + eye height)."""
    cams = []
    picked = findings[:60]
    for i, f in enumerate(picked):
        dx, dy = -f.e, -f.n
        norm = max((dx * dx + dy * dy) ** 0.5, 1e-6)
        dx, dy = dx / norm, dy / norm
        dist = 15.0
        pos = [round(f.e - dx * dist, 2), round(f.n - dy * dist, 2), round(origin_z + DRIVER_EYE_M, 2)]
        cams.append({
            "id": f"wv-{i:03d}-{f.category}",
            "type": "persp", "fov_deg": 55.0,
            "pos": pos, "look_at": [round(f.e, 2), round(f.n, 2), round(origin_z + 1.0, 2)],
            "note": f"{f.category} | {f.id} | {f.detail} | E {f.e:.1f} N {f.n:.1f}"
                    + (f" | {f.lat:.6f}, {f.lon:.6f}" if f.lat else ""),
            "category": f.category, "severity": f.severity, "finding": f.id,
        })
    return cams


def _md_table(w: World, rows: list[Finding]) -> str:
    out = ["| # | kategoria | E (m) | N (m) | id | szczegół | kafelek |", "|---|---|---|---|---|---|---|"]
    for i, f in enumerate(rows, 1):
        latlon = f" ({f.lat:.6f}, {f.lon:.6f})" if f.lat else ""
        out.append(f"| {i} | {f.category} | {f.e:.1f} | {f.n:.1f} | `{f.id}` | "
                   f"{html.escape(f.detail)}{latlon} | {_tile_link(w, f.chunk)} |")
    return "\n".join(out)


def write_md(w: World, findings: list[Finding], out: Path, runtime_s: float | None = None) -> Path:
    s = summarize(findings)
    lines = [f"# World validator — region `{w.region_id}`",
             "",
             f"Schema `{SCHEMA}`. Ramka: lokalne E/N w metrach (EPSG:2180 minus origin regionu); "
             f"lat/lon = WGS84. Kafelek = chunk 256 m z `generated/world_manifest.json`.",
             "",
             f"Znaleziska: **{s['count']}** (error {s['by_severity'].get('error', 0)}, "
             f"warn {s['by_severity'].get('warn', 0)}, info {s['by_severity'].get('info', 0)}), "
             f"z czego na trasie G3 (±60 m): **{sum(s['on_route_by_category'].values())}**"
             + (f", czas walidatora: {runtime_s:.1f} s" if runtime_s else ""),
             "",
             "## Liczby wg kategorii", "",
             "| kategoria | liczba | na trasie G3 |", "|---|---|---|"]
    for cat, n in s["by_category"].items():
        lines.append(f"| {cat} | {n} | {s['on_route_by_category'].get(cat, 0)} |")
    lines += ["", "## Top 20 znalezisk (posortowane: severity, trasa G3, odległość, kategoria)", "",
              _md_table(w, findings[:TOP_N]), "",
              "Pełna lista: `world_validator.json` obok tego raportu. Kamery kontrolne: `control_cameras.json`."]
    p = out / "report.md"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return p


def write_html(w: World, findings: list[Finding], out: Path) -> Path:
    s = summarize(findings)
    def _row(i: int, f: Finding) -> str:
        lat = f"{f.lat:.6f}" if f.lat is not None else ""
        lon = f"{f.lon:.6f}" if f.lon is not None else ""
        return (f"<tr><td>{i}</td><td>{html.escape(f.category)}</td><td>{f.severity}</td>"
                f"<td>{f.e:.1f}</td><td>{f.n:.1f}</td><td>{lat}</td><td>{lon}</td>"
                f"<td><code>{html.escape(f.id)}</code></td><td>{html.escape(f.detail)}</td>"
                f"<td>{html.escape(_tile_link(w, f.chunk))}</td></tr>")
    rows = "\n".join(_row(i, f) for i, f in enumerate(findings[:200], 1))
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>world validator {html.escape(w.region_id)}</title>
<style>body{{font:13px/1.4 sans-serif;margin:2em}}table{{border-collapse:collapse}}td,th{{border:1px solid #ccc;
padding:2px 6px}}th{{background:#eee}}</style></head><body>
<h1>World validator — {html.escape(w.region_id)}</h1>
<p>Znaleziska: <b>{s['count']}</b> (error {s['by_severity'].get('error', 0)},
warn {s['by_severity'].get('warn', 0)}, info {s['by_severity'].get('info', 0)});
na trasie G3 (±60 m): <b>{sum(s['on_route_by_category'].values())}</b>. Lokalne E/N (m), lat/lon WGS84.</p>
<table><tr><th>#</th><th>kategoria</th><th>severity</th><th>E</th><th>N</th><th>lat</th><th>lon</th><th>id</th>
<th>szczegół</th><th>kafelek</th></tr>
{rows}</table></body></html>"""
    p = out / "report.html"
    p.write_text(doc, encoding="utf-8", newline="\n")
    return p


def write_json(w: World, findings: list[Finding], out: Path, runtime_s: float | None = None,
               prev: dict | None = None) -> Path:
    s = summarize(findings)
    doc = {"schema": SCHEMA, "region": w.region_id,
           "frame": "e, n = local metres (EPSG:2180 minus region origin); lat, lon = WGS84; chunk = 256 m tile",
           "params": PARAMS, "runtime_s": runtime_s, "summary": s,
           "findings": [f.as_dict() for f in findings]}
    if prev is not None:
        doc["diff_vs_prev"] = diff(prev, doc)
    p = out / "world_validator.json"
    p.write_text(json.dumps(doc, indent=1, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    return p


def write_cameras(w: World, findings: list[Finding], out: Path, origin_z: float) -> Path:
    doc = {"schema": CAMERA_SCHEMA, "region": w.region_id, "source": "tools/worldgen/validate/run.py",
           "frame": "local E/N metres; z = region origin z + eye height (heightmap not in git, WORKING_VALUE)",
           "cameras": cameras(w, findings, origin_z)}
    p = out / "control_cameras.json"
    p.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return p


def diff(prev: dict, cur: dict) -> dict:
    """Extension (b): compare two world_validator.json runs (counts by category + new/fixed finding keys)."""
    pc, cc = prev.get("summary", {}).get("by_category", {}), cur.get("summary", {}).get("by_category", {})
    cats = sorted(set(pc) | set(cc))
    counts = [{"category": c, "prev": pc.get(c, 0), "cur": cc.get(c, 0), "delta": cc.get(c, 0) - pc.get(c, 0)}
              for c in cats]
    pk = {(f["category"], round(f["e"], 1), round(f["n"], 1), f["id"]) for f in prev.get("findings", [])}
    ck = {(f["category"], round(f["e"], 1), round(f["n"], 1), f["id"]) for f in cur.get("findings", [])}
    return {"by_category": counts, "new": len(ck - pk), "fixed": len(pk - ck),
            "prev_total": prev.get("summary", {}).get("count"), "cur_total": cur.get("summary", {}).get("count")}
