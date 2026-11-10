"""Fetch the CC0 surface scans of the world materials (ADR 0063) into art-source/world/cc0/_raw/ (not in git).

The manifest art-source/world/cc0/cc0_manifest.json is the contract: asset id, source library, authors, physical size,
licence page, and per map the exact URL, byte size and SHA-256 of the downloaded file. A normal run downloads what is
missing and verifies every file against the manifest (a mismatch is an error: the source changed, re-review it).

    uv run --project tools/worldgen python art-source/world/materials/_src/cc0_fetch.py            # fetch + verify
    uv run --project tools/worldgen python art-source/world/materials/_src/cc0_fetch.py --resolve  # (re)query the
        Poly Haven API for URLs / authors / dimensions of the assets listed in SELECTION and rewrite the manifest
    ... --record   # write sha256 / bytes of the downloaded files into the manifest (first fetch of a new asset)

Only Poly Haven (api.polyhaven.com, CC0 1.0, https://polyhaven.com/license) and ambientCG (CC0 1.0,
https://docs.ambientcg.com/license/) are allowed sources (owner decision D40). No Google sources, no AI generators.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
CC0 = REPO / "art-source" / "world" / "cc0"
MANIFEST = CC0 / "cc0_manifest.json"
RAW = CC0 / "_raw"
UA = {"User-Agent": "kamion-worldgen/1.0 (CC0 material fetch)"}

# asset id -> (target sets, why). Resolution 2k JPG for every map: at the physical sizes below that is 1.0-2.0 mm per
# texel, i.e. at or above the High tier density of the generated sets (1.95 mm), so nothing larger is needed.
SELECTION = {
    "asphalt_04": (["asphalt_worn"], "weathered grey AC with fine light aggregate, dry discoloration (aged city asphalt)"),
    "asphalt_pit_lane": (["asphalt_sma_fresh"], "dark tarmac with fine chips and binder film (recent wearing course)"),
    "clean_asphalt": (["asphalt_patch"], "dark fine-grained asphalt (newer patch fill)"),
    "concrete_pavers": (["behaton_i_grey"], "grey interlocking double-T concrete pavers (behaton)"),
    "pavement_04": (["paving_20x10_grey"], "dark grey rectangular concrete pavers, running bond (holland 20x10)"),
    "concrete_pavement_02": (["sidewalk_slab_35"], "square concrete sidewalk slabs ~0.30 m, scaled to 35x35 (plyty chodnikowe)"),
    "brushed_concrete": (["concrete_cast_5m_joints"], "broom-finished cast concrete (yards, concrete roads, viaducts)"),
    "concrete_floor_worn_001": (["concrete_slab_3x1.5", "kerb_concrete_1m", "concrete_precast", "large_panel_joints"],
                                "worn grey precast concrete surface (JOMB plates, kerbs, plinths, large-panel blocks)"),
    "painted_plaster_wall": (["plaster"], "weathered painted exterior plaster (blocks, houses)"),
    "red_brick": (["brick"], "red brick, stretcher bond, recessed mortar"),
    "corrugated_iron_03": (["trapezoid_sheet"], "galvanised sheet weathering (scratches, rust spots); ribs notched out"),
    "gravel_floor_02": (["gravel_compacted"], "grey crushed-stone driveway gravel (shoulders, yards)"),
    "pine_bark": (["bark_pine"], "Scots-pine-like plated bark (processed only; trees are another agent's scope)"),
}
MAPS = ["Diffuse", "nor_gl", "Rough", "AO", "Displacement"]
RES = "2k"
FMT = "jpg"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve(old: dict) -> dict:
    prev = {a["id"]: a for a in old.get("assets", [])}
    assets = []
    for aid, (sets, why) in SELECTION.items():
        info = requests.get(f"https://api.polyhaven.com/info/{aid}", headers=UA, timeout=60).json()
        files = requests.get(f"https://api.polyhaven.com/files/{aid}", headers=UA, timeout=60).json()
        maps = []
        for m in MAPS:
            e = files[m][RES][FMT]
            pm = next((x for x in prev.get(aid, {}).get("files", []) if x["map"] == m and x["url"] == e["url"]), {})
            maps.append({"map": m, "url": e["url"], "md5_api": e["md5"], "bytes": e["size"],
                         "sha256": pm.get("sha256", ""), "fetched_utc": pm.get("fetched_utc", "")})
        assets.append({
            "id": aid, "source": "polyhaven", "name": info["name"], "page": f"https://polyhaven.com/a/{aid}",
            "authors": info["authors"], "dimensions_mm": [round(x, 1) for x in info["dimensions"]],
            "date_published_unix": info.get("date_published"), "license": "CC0 1.0",
            "license_page": "https://polyhaven.com/license", "sets": sets, "why": why,
            "resolution": RES, "format": FMT, "files": maps,
        })
    return {
        "schema": "kamion.world.cc0/1",
        "note": "CC0 surface scans (owner decision D40, ADR 0063). Raw files in art-source/world/cc0/_raw/<id>/ (not in "
                "git), fetched by art-source/world/materials/_src/cc0_fetch.py and verified by sha256. Processing: "
                "art-source/world/materials/_src/sets_scan.py (build_all.py).",
        "licenses": {"polyhaven": {"license": "CC0 1.0 Universal", "page": "https://polyhaven.com/license",
                                   "checked_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")}},
        "assets": assets,
    }


def fetch(man: dict, record: bool) -> int:
    bad = 0
    for a in man["assets"]:
        d = RAW / a["id"]
        d.mkdir(parents=True, exist_ok=True)
        for f in a["files"]:
            p = d / f["url"].rsplit("/", 1)[1]
            if not p.exists():
                r = requests.get(f["url"], headers=UA, timeout=300)
                r.raise_for_status()
                p.write_bytes(r.content)
                f["fetched_utc"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                print("  got", p.relative_to(REPO), len(r.content), flush=True)
            h = sha256(p)
            if not f.get("sha256"):
                if record:
                    f["sha256"] = h
                    f["bytes"] = p.stat().st_size
                else:
                    print(f"  UNRECORDED {p.name} {h} (run with --record)")
                    bad += 1
            elif f["sha256"] != h:
                print(f"  SHA256 MISMATCH {p.name}: manifest {f['sha256']} file {h}")
                bad += 1
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resolve", action="store_true")
    ap.add_argument("--record", action="store_true")
    a = ap.parse_args()
    old = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    man = resolve(old) if a.resolve else old
    if not man:
        sys.exit("no manifest: run with --resolve first")
    bad = fetch(man, a.record or a.resolve)
    if a.resolve or a.record:
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST.write_text(json.dumps(man, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print("wrote", MANIFEST.relative_to(REPO))
    n = sum(len(x["files"]) for x in man["assets"])
    print(f"{len(man['assets'])} assets, {n} files, {bad} problems")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
