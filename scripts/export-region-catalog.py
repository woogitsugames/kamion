"""Refresh the start-menu region catalog (ADR 0229) from the region data in git.

    python scripts/export-region-catalog.py            # rewrite routeLengthM / startS from Data/Regions/*/route_start.json
    python scripts/export-region-catalog.py --check    # exit 1 when the catalog is stale or misses a region (CI / review)

Catalog: game/Assets/_Project/Gameplay/Resources/Regions/region_catalog.json (Resources, loaded by
Game.Gameplay.RegionCatalog in the Boot menu and read by Game.Editor.Build.RegionBuildList for `-Regions`).
Authored fields (kept as they are): id, label, group, order of the list, aliases, sets (except the derived ones below).
Derived fields (rewritten here): routeLengthM (route_start.json length_m), startS (12 m like the spawn the importer
places, WorldSceneBuilder spawnS, clamped so that at least MIN_AHEAD_M of route remains), and the DERIVED_SETS
(ADR 0267: d67-full = d67 + the D71 extras; the C# resolver does not nest sets, so the list is expanded here).
Standard library only (no uv needed).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CATALOG = REPO / "game/Assets/_Project/Gameplay/Resources/Regions/region_catalog.json"
REGIONS = REPO / "Data/Regions"
SPAWN_S_M = 12.0       # WorldSceneBuilder: const float spawnS = 12f
MIN_AHEAD_M = 100.0    # keep >= 100 m before the tile-end closure (closure 60 m before the edge, ADR 0169) - WORKING_VALUE

# Derived sets (ADR 0267, owner decision D71): name -> (base set, extra region ids, note). Written after the base set.
DERIVED_SETS: dict[str, tuple[str, list[str], str]] = {
    "d67-full": (
        "d67",
        ["bialystok-dojlidy", "knyszyn-w", "dk65-monki-01", "dw671-tykocin-01"],
        "D71: d67 + Dojlidy, Knyszyn-W, Monki, Tykocin. APK size ESTIMATED 1407-1948 MB "
        "(REVIEW-2026-11-15-s21-code-104, like 'all'); measure on the build (ADR 0267).",
    ),
}


def apply_derived_sets(cat: dict, problems: list[str]) -> None:
    """Expand DERIVED_SETS into cat["sets"] (in place); a missing / differing entry is reported in problems."""
    sets = cat.setdefault("sets", [])
    for name, (base_name, extra, note) in DERIVED_SETS.items():
        base = next((s for s in sets if s.get("name") == base_name), None)
        if base is None:
            problems.append(f"set {name}: base set {base_name} missing")
            continue
        regions: list[str] = []
        for r in list(base["regions"]) + extra:
            if r not in regions:
                regions.append(r)
        want = {"name": name, "note": note, "regions": regions}
        cur = next((i for i, s in enumerate(sets) if s.get("name") == name), None)
        if cur is None:
            problems.append(f"set {name}: missing (derived from {base_name})")
            sets.insert(sets.index(base) + 1, want)
        elif sets[cur] != want:
            problems.append(f"set {name}: stale (derived from {base_name} + {', '.join(extra)})")
            sets[cur] = want


def derived(region_id: str) -> dict:
    route = REGIONS / region_id / "route_start.json"
    if not route.exists():
        raise SystemExit(f"{region_id}: {route.relative_to(REPO)} missing (scripts/export-route.py)")
    length = float(json.loads(route.read_text(encoding="utf-8"))["length_m"])
    start = max(0.0, min(SPAWN_S_M, length - MIN_AHEAD_M))
    return {"routeLengthM": round(length, 2), "startS": round(start, 2)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    cat = json.loads(CATALOG.read_text(encoding="utf-8"))
    problems: list[str] = []
    ids = [r["id"] for r in cat["regions"]]
    on_disk = sorted(p.name for p in REGIONS.iterdir() if (p / "route_start.json").exists())
    for rid in on_disk:
        if rid not in ids:
            problems.append(f"region {rid} has route_start.json but no catalog entry (add id + label by hand)")
    if len(set(ids)) != len(ids):
        problems.append("duplicate region ids in the catalog")
    for r in cat["regions"]:
        d = derived(r["id"])
        for k, v in d.items():
            if r.get(k) != v:
                problems.append(f"{r['id']}.{k}: {r.get(k)} -> {v}")
                r[k] = v
    apply_derived_sets(cat, problems)
    for s in cat.get("sets", []):
        for t in s["regions"]:
            if t not in ids:
                problems.append(f"set {s['name']}: unknown region {t}")
    for al in cat.get("aliases", []):
        if al["region"] not in ids:
            problems.append(f"alias {al['alias']}: unknown region {al['region']}")
    for p in problems:
        print(p)
    if a.check:
        return 1 if problems else 0
    CATALOG.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {CATALOG.relative_to(REPO)} ({len(ids)} regions)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
