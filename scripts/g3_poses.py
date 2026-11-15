#!/usr/bin/env python
"""Gate 3 photo-pair poses for the phone (ADR 0246, BACKLOG B-111). Stdlib only.

The poses are NOT authored here: every pose is copied from the photo-pair cameras the editor side-by-side uses
(Data/Regions/<region>/sbs_cameras.json, ADR 0103/0160/0172; rendered by scripts/sbs-gate3.ps1 through visual-qa -Gate3)
and joined with the photo metadata of sbs_references.json (photo size -> output aspect, attribution, comparison photo).
Output: ONE pose file, written to the data folder and byte-identical to the copy the game loads from Resources.

CLI:
  python scripts/g3_poses.py export [--region bialystok-industrial-c]   -> writes both copies, prints a summary
  python scripts/g3_poses.py check  [--region ...]                      -> exit 1 when a copy is stale or missing
  python scripts/g3_poses.py list   [--region ...] [--only <filter>]    -> "index id ref_photo comparison_photo w h" per pose
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCHEMA = "kamion/g3-poses/1"
DEFAULT_REGION = "bialystok-industrial-c"
# Output width of the phone frames: the same width scripts/sbs-gate3.ps1 renders the editor pairs at ($width = 1280),
# height from the photo aspect exactly as there ([int]($width * height / width)).
OUT_WIDTH = 1280
RESOURCE_REL = "game/Assets/_Project/Gameplay/Resources/g3_poses.json"


def data_paths(region: str) -> dict[str, Path]:
    d = REPO / "Data" / "Regions" / region
    return {
        "cameras": d / "sbs_cameras.json",
        "references": d / "sbs_references.json",
        "data_out": d / "g3_poses.json",
        "resource_out": REPO / RESOURCE_REL,
    }


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rel(p: Path) -> str:
    return p.resolve().relative_to(REPO).as_posix()


def out_height(width: int, ref_w: int, ref_h: int) -> int:
    # PowerShell [int] rounds half to even; Python round() does the same.
    return int(round(width * ref_h / ref_w))


def build(region: str) -> dict:
    p = data_paths(region)
    cams_doc = json.loads(p["cameras"].read_text(encoding="utf-8"))
    refs_doc = json.loads(p["references"].read_text(encoding="utf-8"))
    cams = cams_doc["cameras"]
    refs = {r["camera"]: r for r in refs_doc["references"]}
    poses = []
    errors = []
    seen = set()
    for i, c in enumerate(cams):
        cid = c["id"]
        if cid in seen:
            errors.append(f"duplicate camera id {cid}")
        seen.add(cid)
        r = refs.get(cid)
        if r is None:
            errors.append(f"camera {cid} has no entry in {rel(p['references'])}")
            continue
        if c.get("segment") != r.get("segment"):
            errors.append(f"camera {cid}: segment {c.get('segment')} != reference {r.get('segment')}")
        w, h = int(r["width"]), int(r["height"])
        poses.append({
            "index": len(poses) + 1,
            "id": cid,
            "segment": c["segment"],
            "kind": c["kind"],
            "seat": c.get("seat", ""),
            "pos": c["pos"],
            "look_at": c["look_at"],
            "fov_deg": c["fov_deg"],
            "pose_confidence": c.get("pose_confidence", ""),
            "out_width": OUT_WIDTH,
            "out_height": out_height(OUT_WIDTH, w, h),
            "source": {
                "cameras_file": rel(p["cameras"]),
                "cameras_index": i,
                "references_file": rel(p["references"]),
                "pose_reason": c.get("pose_reason", ""),
                "note": c.get("note", ""),
            },
            "reference": {
                "photo": r.get("photo", ""),
                "comparison_photo": r.get("comparison_photo", ""),
                "source_id": str(r.get("source_id", "")),
                "page_url": r.get("page_url", ""),
                "author": r.get("author", ""),
                "license": r.get("license", ""),
                "captured_at": r.get("captured_at", ""),
                "width": w,
                "height": h,
            },
        })
    extra = sorted(set(refs) - seen)
    if extra:
        errors.append(f"references without a camera: {', '.join(extra)}")
    if errors:
        raise SystemExit("g3_poses: " + "; ".join(errors))
    return {
        "schema": SCHEMA,
        "region": region,
        "frame": cams_doc.get("frame", ""),
        "generated_by": "python scripts/g3_poses.py export --region " + region,
        "adr": "docs/adr/0246-zrzuty-a16-poz-par-zdjeciowych-g3.md",
        "inputs": {
            rel(p["cameras"]): sha256(p["cameras"]),
            rel(p["references"]): sha256(p["references"]),
        },
        "count": len(poses),
        "count_note": "every camera of sbs_cameras.json (kind photo_match); the 42 pairs of the s16b review "
                      "(docs/reports/visual/REVIEW-2026-11-13-s16b-final.md, 27 R / 15 P / 0 N)",
        "out_width_source": "scripts/sbs-gate3.ps1 ($width = 1280, height from the photo aspect)",
        "poses": poses,
    }


def render(doc: dict) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def cmd_export(a) -> int:
    p = data_paths(a.region)
    text = render(build(a.region))
    for k in ("data_out", "resource_out"):
        p[k].parent.mkdir(parents=True, exist_ok=True)
        p[k].write_text(text, encoding="utf-8", newline="\n")
    doc = json.loads(text)
    seg = {}
    for x in doc["poses"]:
        seg[x["segment"]] = seg.get(x["segment"], 0) + 1
    print(f"g3_poses: {doc['count']} poses ({', '.join(f'{k} {v}' for k, v in sorted(seg.items()))}) -> "
          f"{rel(p['data_out'])}, {rel(p['resource_out'])}")
    return 0


def cmd_check(a) -> int:
    p = data_paths(a.region)
    want = render(build(a.region))
    bad = []
    for k in ("data_out", "resource_out"):
        if not p[k].exists():
            bad.append(f"{rel(p[k])} missing")
        elif p[k].read_text(encoding="utf-8") != want:
            bad.append(f"{rel(p[k])} stale")
    if bad:
        print("g3_poses check FAIL: " + "; ".join(bad) + f" - run: python scripts/g3_poses.py export --region {a.region}")
        return 1
    print(f"g3_poses check OK ({json.loads(want)['count']} poses)")
    return 0


def is_index(t: str) -> bool:
    return 0 < len(t) <= 3 and t.isascii() and t.isdigit()


def matches(pose: dict, only: str) -> bool:
    """Same rule as Game.Gameplay.G3PoseSet.Matches: comma tokens; a number of at most 3 digits is the 1-based index,
    "a-b" of such numbers an index range, otherwise (also a longer number, e.g. a photo key) a case-insensitive
    substring of the id ('_' and '-' are equal)."""
    if not only or not only.strip():
        return True
    norm = pose["id"].replace("_", "-").lower()
    for t in (x.strip() for x in only.split(",")):
        if not t:
            continue
        if is_index(t):
            if int(t) == pose["index"]:
                return True
            continue
        a, dash, b = t.partition("-")
        if dash and is_index(a) and is_index(b):
            if min(int(a), int(b)) <= pose["index"] <= max(int(a), int(b)):
                return True
            continue
        if t.replace("_", "-").lower() in norm:
            return True
    return False


def cmd_list(a) -> int:
    p = data_paths(a.region)
    doc = json.loads(p["data_out"].read_text(encoding="utf-8"))
    for x in doc["poses"]:
        if matches(x, a.only):
            r = x["reference"]
            print(f"{x['index']}\t{x['id']}\t{r['photo']}\t{r['comparison_photo']}\t{x['out_width']}\t{x['out_height']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("export", "check", "list"):
        s = sub.add_parser(name)
        s.add_argument("--region", default=DEFAULT_REGION)
        if name == "list":
            s.add_argument("--only", default="")
    a = ap.parse_args(argv)
    return {"export": cmd_export, "check": cmd_check, "list": cmd_list}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
