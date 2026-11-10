#!/usr/bin/env python
"""Gate 3 evidence report (docs/06 section 5, docs/plan/STAGE-3.md E8).  Tooling only - no visuals are changed here.

Inputs (all produced by scripts/gate3-evidence.ps1):
  <out>/audit_raw.json            Unity export of Game.Editor.VisualQA.Gate3Audit (corridor materials, textures, meshes, ground probes)
  <out>/renders/<Tier>-<light>/   editor renders of every gate3 camera (+ reused control cameras)
  <phone-dir>/**                  phone screencaps (default artifacts/gate3/final/), matched by camera id in the file name
  Data/Regions/<region>/gate3_cameras.json, gate3_reference_map.json
Outputs in <out>: gate3-evidence.json, gate3-evidence.md, sheets/<camera>.png, albedo_histogram.png

Every threshold below is a WORKING_VALUE (docs/06 asks for a texel-density ADR; there is none yet): they are written here
so a change is a visible diff.  Verdicts are tooling output; the owner decides the gate.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- thresholds (WORKING_VALUE)
ALBEDO_LO, ALBEDO_HI = 30, 240          # docs/06 section 2: sRGB albedo range (no pure black / pure white)
ALBEDO_FAIL_FRAC, ALBEDO_WARN_FRAC = 0.05, 0.01   # share of texels outside the range per material
TEXEL_BAND = (100.0, 1500.0)            # texels per metre of any corridor material (mean, area weighted)
TEX_MAX_DIM = 2048                      # no world texture larger than this after the Android max-size override
UNCOMPRESSED_BPP, UNCOMPRESSED_MIN_DIM = 24, 256   # a >= 24 bpp texture larger than 256 px on Android = not compressed
# Prototypes whose origin is not at their base on purpose (mounted on a pole / facade / gantry / hanging): a floating
# origin is expected for them.  Everything else must touch the ground (0.30 m) and not be buried (0.60 m).
ELEVATED_BY_DESIGN = re.compile(
    r"^(signal_head|board_|facade_sign|plate_|sign_face|banner|wire|cable|lamp_head|luminaire|mirror_|gantry_|bracket|camera_|clock|flag)", re.I)
# Documented exemptions (each is listed in the report, never silent):
ALBEDO_EXEMPT = re.compile(r"^M_(sign|plate)_", re.I)          # traffic-sign faces: retroreflective white and black print by design
TEXEL_EXEMPT = re.compile(r"^M_impostor_", re.I)               # distance billboards of whole trees, low density by design
VEGETATION = re.compile(r"^(tree|shrub|bush|hedge)_", re.I)   # planted: trunk base may sit below the terrain
VEGETATION_SUNK_OK_M = 1.0
TIER_ORDER = ["Low", "Medium", "High", "Ultra"]
CC_OK = re.compile(r"^(CC0|PD|public domain|domena publiczna)", re.I)

FONT = None


def font(size: int):
    global FONT
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default(size)


def norm(s: str) -> str:
    return s.replace("_", "-").lower()


def srgb_luma(rgb: np.ndarray) -> np.ndarray:
    """Rec.709 luma of sRGB values (0..255), weights applied to the encoded values (what the docs/06 range means)."""
    return rgb[..., 0] * 0.2126 + rgb[..., 1] * 0.7152 + rgb[..., 2] * 0.0722


# ---------------------------------------------------------------- checks
def check_albedo(audit: dict, repo: Path, out: Path) -> dict:
    mats = audit["materials"]
    rows, glob_hist, glob_w = [], np.zeros(256), 0.0
    for m in mats:
        base = np.array(m["base_color_srgb"], dtype=np.float64)
        weight = max(float(m["area_m2"]), 1.0)
        if m["base_map"]:
            p = repo / "game" / m["base_map"]
            if not p.exists():
                rows.append({"name": m["name"], "status": "SKIP", "why": f"texture file missing {m['base_map']}"})
                continue
            im = Image.open(p)
            im.thumbnail((512, 512))
            a = np.asarray(im.convert("RGBA"), dtype=np.float64)
            keep = a[..., 3] >= 128                      # cutout / decal texels only
            rgb = a[..., :3][keep] * (base / 255.0)
            if rgb.size == 0:
                rows.append({"name": m["name"], "status": "SKIP", "why": "fully transparent"})
                continue
        else:
            rgb = base.reshape(1, 3)
        luma = srgb_luma(rgb)
        outside = float(np.mean((luma < ALBEDO_LO) | (luma > ALBEDO_HI)))
        mean = float(luma.mean())
        p1, p99 = float(np.percentile(luma, 1)), float(np.percentile(luma, 99))
        status = "PASS"
        if ALBEDO_EXEMPT.search(m["name"]):
            status = "EXEMPT"
        elif mean < ALBEDO_LO or mean > ALBEDO_HI or outside > ALBEDO_FAIL_FRAC:
            status = "FAIL"
        elif outside > ALBEDO_WARN_FRAC:
            status = "WARN"
        rows.append({"name": m["name"], "shader": m["shader"], "textured": bool(m["base_map"]), "mean_srgb": round(mean, 1),
                     "p1": round(p1, 1), "p99": round(p99, 1), "outside_frac": round(outside, 4), "status": status})
        h, _ = np.histogram(luma, bins=256, range=(0, 256))
        glob_hist += h / max(1, h.sum()) * weight
        glob_w += weight
    draw_histogram(glob_hist / max(glob_w, 1e-9), out / "albedo_histogram.png")
    fails = [r for r in rows if r["status"] == "FAIL"]
    warns = [r for r in rows if r["status"] == "WARN"]
    return {"verdict": "FAIL" if fails else "PASS", "exempt": [r["name"] for r in rows if r["status"] == "EXEMPT"],
            "exempt_rule": ALBEDO_EXEMPT.pattern,
            "rule": f"material albedo (texel x base colour, sRGB luma) mean inside [{ALBEDO_LO},{ALBEDO_HI}] and <= {ALBEDO_FAIL_FRAC:.0%} of texels outside it (WARN above {ALBEDO_WARN_FRAC:.0%}); alpha < 0.5 texels ignored",
            "materials_checked": len([r for r in rows if r["status"] not in ("SKIP", "EXEMPT")]), "fail": len(fails), "warn": len(warns),
            "failing": sorted(fails, key=lambda r: -r["outside_frac"])[:25], "warning": sorted(warns, key=lambda r: -r["outside_frac"])[:15],
            "histogram_png": "albedo_histogram.png"}


def draw_histogram(h: np.ndarray, path: Path):
    W, H = 768, 260
    im = Image.new("RGB", (W + 40, H + 50), (24, 24, 24))
    d = ImageDraw.Draw(im)
    mx = h.max() or 1
    for i, v in enumerate(h):
        x = 20 + i * 3
        d.rectangle([x, 10 + H - int(v / mx * H), x + 2, 10 + H], fill=(170, 170, 170) if ALBEDO_LO <= i <= ALBEDO_HI else (200, 70, 60))
    for edge in (ALBEDO_LO, ALBEDO_HI):
        d.line([20 + edge * 3, 10, 20 + edge * 3, 10 + H], fill=(240, 200, 60))
    d.text((20, H + 20), f"corridor albedo, sRGB luma 0..255, area-weighted over materials; yellow = {ALBEDO_LO}..{ALBEDO_HI} (docs/06)", fill=(220, 220, 220), font=font(13))
    im.save(path)


def check_texel(audit: dict) -> dict:
    rows, exempt = [], []
    for m in audit["materials"]:
        if not m["base_map"] or m["area_m2"] <= 0:
            continue
        d = float(m["texel_per_m_mean"])
        if TEXEL_EXEMPT.search(m["name"]):
            exempt.append(m["name"])
            continue
        rows.append({"name": m["name"], "mean": round(d, 1), "min": round(m["texel_per_m_min"], 1), "max": round(m["texel_per_m_max"], 1),
                     "area_m2": round(m["area_m2"], 1), "status": "PASS" if TEXEL_BAND[0] <= d <= TEXEL_BAND[1] else "FAIL"})
    fails = [r for r in rows if r["status"] == "FAIL"]
    return {"verdict": "FAIL" if fails else "PASS",
            "rule": f"area-weighted mean texels per metre of each textured corridor material inside {TEXEL_BAND} (WORKING_VALUE, no texel-density ADR yet; tiling and UV area from the mesh, base map size from the asset)",
            "materials_measured": len(rows), "fail": len(fails), "exempt": exempt, "exempt_rule": TEXEL_EXEMPT.pattern,
            "failing": sorted(fails, key=lambda r: r["mean"])[:25],
            "all": sorted(rows, key=lambda r: -r["area_m2"])[:40],
            "untextured_materials": len([m for m in audit["materials"] if not m["base_map"]])}


def check_texture_budget(audit: dict) -> dict:
    tex = audit["textures"]
    total = sum(t["est_android_bytes"] for t in tex) / 1e6
    per_tier = []
    for t in audit["tiers"]:
        per_tier.append({"tier": t["name"], "budget_mb": t["budgetTextureMB"], "corridor_textures_mb": round(total, 1),
                         "status": "PASS" if total <= t["budgetTextureMB"] else "FAIL"})
    big = [t for t in tex if max(t["eff_w"], t["eff_h"]) > TEX_MAX_DIM]
    raw = []
    for t in tex:
        fmt = t["format"]
        m = re.search(r"ASTC_(\d+)x(\d+)", fmt)
        bpp = 128.0 / (int(m[1]) * int(m[2])) if m else (4 if re.search(r"ETC2_RGB$|DXT1|ETC_RGB4", fmt) else (8 if re.search(r"ETC2_RGBA8|DXT5|BC7", fmt) else 32))
        if bpp >= UNCOMPRESSED_BPP and max(t["eff_w"], t["eff_h"]) > UNCOMPRESSED_MIN_DIM:
            raw.append({"path": t["path"], "format": fmt, "size": f"{t['eff_w']}x{t['eff_h']}"})
    top = sorted(tex, key=lambda t: -t["est_android_bytes"])[:12]
    bad = any(r["status"] == "FAIL" for r in per_tier) or big or raw
    return {"verdict": "FAIL" if bad else "PASS",
            "rule": "unique textures of corridor materials, estimated Android memory (importer max size and format, mips) vs the tier's budgetTextureMB (QualityProfile.asset; the same world texture set serves every tier); no texture above "
                    f"{TEX_MAX_DIM} px; no uncompressed texture above {UNCOMPRESSED_MIN_DIM} px. Scope: corridor only, not the whole region and not the truck",
            "textures": len(tex), "estimated_mb": round(total, 1), "per_tier": per_tier,
            "over_max_dim": [{"path": t["path"], "size": f"{t['eff_w']}x{t['eff_h']}"} for t in big],
            "uncompressed_large": raw[:20], "uncompressed_large_count": len(raw),
            "largest": [{"path": t["path"], "size": f"{t['eff_w']}x{t['eff_h']}", "format": t["format"], "mb": round(t["est_android_bytes"] / 1e6, 2)} for t in top]}


def check_meshes(audit: dict) -> dict:
    s = audit["mesh_summary"]
    probs = audit["meshes"]
    hard = [m for m in probs if (not m["has_normals"]) or m["nan_vertices"] > 0 or m.get("textured_without_uv0")]
    soft = [m for m in probs if not m["has_uv0"] and not m.get("textured_without_uv0")]
    return {"verdict": "FAIL" if (hard or s["unreadable_by_api"]) else "PASS",
            "rule": "meshes used in the corridor (scene renderers, prop/tree LODs, HLOD): normals present, no NaN vertices, UV0 present wherever a material with a base map uses the mesh; meshes without UV0 that only carry flat-colour materials are listed as notes",
            "meshes_checked": s["checked"], "missing_normals": s["missing_normals"], "missing_uv0_total": s["missing_uv0"], "nan": s["nan"],
            "failing": hard[:25], "note_flat_colour_without_uv0": [m["name"] for m in soft][:25], "note_flat_colour_without_uv0_count": len(soft)}


def check_ground(audit: dict) -> dict:
    g = audit["ground_check"]
    rows = audit.get("prototype_ground", [])
    bad_protos, exempt = [], []
    for r in rows:
        if r["floating"] + r["sunk"] == 0:
            continue
        mounted = ELEVATED_BY_DESIGN.search(r["name"]) and r["sunk"] == 0
        planted = VEGETATION.search(r["name"]) and r["floating"] == 0 and r.get("max_sunk_depth_m", 99) <= VEGETATION_SUNK_OK_M
        (exempt if mounted or planted else bad_protos).append(r)
    ren_bad = [o for o in audit["offenders"] if o["kind"].startswith("renderer_")]
    exempt_names = {r["name"] for r in exempt}
    inst_bad = [o for o in audit["offenders"] if o["kind"].startswith("instance_") and o["name"] not in exempt_names]
    fail = bool(bad_protos or ren_bad or g["renderers_no_ground"] == g["renderers_checked"] > 0)
    return {"verdict": "FAIL" if fail else "PASS",
            "rule": "ground = terrain + road-surface colliders (cooked like the player does); floating = lowest point > 0.30 m above the surface below it (renderers: no probe of 5 touches); sunk = ground above the lowest point by > 0.60 m with nothing below. "
                    "Exempt: prototypes mounted by design (" + ELEVATED_BY_DESIGN.pattern + f") from 'floating'; planted vegetation sunk <= {VEGETATION_SUNK_OK_M} m. Chunk-wide merged meshes (> 60 m) cannot be tested per building and are skipped.",
            "renderers_merged_skipped": g.get("renderers_merged_skipped", 0),
            "probe": g.get("probe"), "renderers_checked": g["renderers_checked"], "renderers_floating": g["renderers_floating"], "renderers_sunk": g["renderers_sunk"],
            "renderers_no_ground": g["renderers_no_ground"], "instances_probed": g["instances_probed"], "instances_floating": g["instances_floating"],
            "instances_sunk": g["instances_sunk"], "instances_no_ground": g["instances_no_ground"],
            "failing_prototypes": bad_protos[:25], "exempt_prototypes": [{"name": r["name"], "floating": r["floating"], "sunk": r["sunk"], "max_above_m": r["max_bottom_above_ground_m"], "max_sunk_m": r.get("max_sunk_depth_m", 0)} for r in exempt][:40],
            "failing_renderers": ren_bad[:25], "failing_instance_examples": inst_bad[:15]}


# ---------------------------------------------------------------- sheets
def find_renders(out: Path, tiers, lights):
    res = {}
    for t in tiers:
        for l in lights:
            d = out / "renders" / f"{t}-{l}"
            if d.exists():
                for f in d.glob("*.png"):
                    res.setdefault(norm(f.stem), {})[(t, l)] = f
    return res


def find_phone(phone_dir: Path, cam_id: str):
    if not phone_dir.exists():
        return []
    n = norm(cam_id)
    hits = [f for f in sorted(phone_dir.rglob("*")) if f.suffix.lower() in (".png", ".jpg", ".jpeg") and norm(f.stem).startswith(n)]
    return hits


def resolve_photos_root(arg: str | None, repo: Path) -> Path | None:
    cands = [Path(arg)] if arg else []
    cands.append(repo / "data" / "photos")
    try:
        common = subprocess.run(["git", "-C", str(repo), "rev-parse", "--git-common-dir"], capture_output=True, text=True, check=True).stdout.strip()
        cands.append((Path(common) if Path(common).is_absolute() else repo / common).resolve().parent / "data" / "photos")
    except Exception:
        pass
    return next((c for c in cands if c.exists()), None)


def caption(im: Image.Image, text: str, sub: str = "", color=(230, 230, 230)) -> Image.Image:
    bar = 44 if sub else 28
    out = Image.new("RGB", (im.width, im.height + bar), (22, 22, 22))
    out.paste(im, (0, bar))
    d = ImageDraw.Draw(out)
    d.text((6, 4), text, fill=color, font=font(15))
    if sub:
        d.text((6, 24), sub, fill=(160, 160, 160), font=font(12))
    return out


def placeholder(w: int, h: int, text: str) -> Image.Image:
    im = Image.new("RGB", (w, h), (40, 40, 40))
    d = ImageDraw.Draw(im)
    d.line([0, 0, w, h], fill=(70, 70, 70))
    d.line([0, h, w, 0], fill=(70, 70, 70))
    d.text((12, h // 2 - 10), text, fill=(200, 160, 90), font=font(16))
    return im


def fit(im: Image.Image, w: int, h: int) -> Image.Image:
    im = im.convert("RGB")
    s = min(w / im.width, h / im.height)
    r = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    canvas = Image.new("RGB", (w, h), (12, 12, 12))
    canvas.paste(r, ((w - r.width) // 2, (h - r.height) // 2))
    return canvas


def make_sheets(cams, renders, phone_dir, refs, photos_root, out: Path, tiers, lights, meta) -> dict:
    sdir = out / "sheets"
    sdir.mkdir(exist_ok=True)
    TW, TH = 760, 351
    SW, SH = 372, 172
    primary = ("Medium", "overcast")
    report = {}
    for cid in cams:
        n = norm(cid)
        r = renders.get(n, {})
        row1 = []
        prim = r.get(primary) or (next(iter(r.values())) if r else None)
        pkey = primary if primary in r else (next(iter(r.keys())) if r else None)
        if prim:
            row1.append(caption(fit(Image.open(prim), TW, TH), f"EDITOR render, {pkey[0]} / {pkey[1]}", meta["editor"]))
        else:
            row1.append(caption(placeholder(TW, TH, "EDITOR render missing"), "EDITOR render", "not produced", (230, 120, 100)))
        ph = find_phone(phone_dir, cid)
        if ph:
            rel = ph[0].relative_to(phone_dir) if phone_dir in ph[0].parents else ph[0].name
            row1.append(caption(fit(Image.open(ph[0]), TW, TH), "PHONE screencap", f"{rel}" + (f"  (+{len(ph) - 1} more)" if len(ph) > 1 else "")))
        else:
            row1.append(caption(placeholder(TW, TH, "no phone screencap yet"), "PHONE screencap", f"none matching '{cid}' under {phone_dir.name}/", (230, 120, 100)))
        ref = refs.get(n)
        refstat = "none mapped"
        if ref and photos_root and CC_OK.match(ref.get("license", "")) and (photos_root / ref["file"]).exists():
            row1.append(caption(fit(Image.open(photos_root / ref["file"]), TW, TH), f"REFERENCE photo ({ref['license']}, {ref.get('author', '?')})",
                                f"{ref['file'].split('/')[-1][:70]}  framing: {ref.get('framing', 'approximate')}"))
            refstat = ref["file"]
        else:
            why = "no CC0 photo mapped for this camera" if not ref else ("licence not CC0/PD, not embedded" if not CC_OK.match(ref.get("license", "")) else "photo file not found")
            row1.append(caption(placeholder(TW, TH, why), "REFERENCE photo", "gate3_reference_map.json", (160, 160, 160)))
            refstat = why
        row2 = []
        for t in tiers:
            for l in lights:
                f = r.get((t, l))
                row2.append(caption(fit(Image.open(f), SW, SH), f"EDITOR {t} / {l}") if f else caption(placeholder(SW, SH, "missing"), f"EDITOR {t} / {l}", color=(230, 120, 100)))
        W = max(sum(t.width for t in row1), sum(t.width for t in row2)) + 20
        H = max(t.height for t in row1) + max(t.height for t in row2) + 62
        sheet = Image.new("RGB", (W, H), (10, 10, 10))
        ImageDraw.Draw(sheet).text((10, 6), f"{cid}   {meta['title']}", fill=(255, 255, 255), font=font(18))
        x, y = 10, 32
        for t in row1:
            sheet.paste(t, (x, y)); x += t.width + 0
        x, y = 10, 32 + max(t.height for t in row1) + 14
        for t in row2:
            sheet.paste(t, (x, y)); x += t.width
        sheet.save(sdir / f"{cid}.png")
        report[cid] = {"sheet": f"sheets/{cid}.png", "editor_renders": len(r), "phone": [str(p) for p in ph[:3]], "reference": refstat}
    return report


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="bialystok-industrial-c")
    ap.add_argument("--repo", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--phone-dir", required=True)
    ap.add_argument("--photos-root")
    ap.add_argument("--tiers", default="Low,Medium,High")
    ap.add_argument("--lightings", default="overcast,lowsun")
    ap.add_argument("--git-sha", default="")
    a = ap.parse_args()
    repo, out, phone_dir = Path(a.repo), Path(a.out), Path(a.phone_dir)
    tiers, lights = a.tiers.split(","), a.lightings.split(",")
    out.mkdir(parents=True, exist_ok=True)

    cam_spec = json.loads((repo / "Data/Regions" / a.region / "gate3_cameras.json").read_text(encoding="utf-8"))
    cams = [c["id"] for c in cam_spec["cameras"]] + list(cam_spec.get("reuse_from_control_cameras", []))
    ref_file = repo / "Data/Regions" / a.region / "gate3_reference_map.json"
    refs = {}
    if ref_file.exists():
        for r in json.loads(ref_file.read_text(encoding="utf-8"))["references"]:
            refs[norm(r["camera"])] = r
    photos_root = resolve_photos_root(a.photos_root, repo)

    audit_path = out / "audit_raw.json"
    checks = {}
    audit = None
    if audit_path.exists():
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        checks["albedo_histogram"] = check_albedo(audit, repo, out)
        checks["texel_density"] = check_texel(audit)
        checks["textures_within_budget"] = check_texture_budget(audit)
        checks["meshes_normals_uv"] = check_meshes(audit)
        checks["objects_vs_terrain"] = check_ground(audit)
    else:
        print(f"no {audit_path}: run scripts/gate3-evidence.ps1 without -SkipAudit", file=sys.stderr)

    renders = find_renders(out, tiers, lights)
    expected = len(cams) * len(tiers) * len(lights)
    got = sum(len(v) for v in renders.values())
    meta = {"title": f"gate 3, region {a.region}, repo {a.git_sha}", "editor": f"Unity editor batchmode, repo {a.git_sha} (not a phone)"}
    sheets = make_sheets(cams, renders, phone_dir, refs, photos_root, out, tiers, lights, meta)
    missing_phone = [c for c, v in sheets.items() if not v["phone"]]
    checks["editor_renders_complete"] = {"verdict": "PASS" if got == expected else "FAIL", "rule": "every camera rendered for every tier x lighting",
                                         "expected": expected, "rendered": got,
                                         "missing": [f"{c}:{t}-{l}" for c in cams for t in tiers for l in lights if (t, l) not in renders.get(norm(c), {})][:40]}

    verdicts = {k: v["verdict"] for k, v in checks.items()}
    overall = "PASS" if all(v == "PASS" for v in verdicts.values()) and checks else "FAIL"
    result = {"schema": "truck-sim-pl/gate3-evidence/1", "region": a.region, "git_sha": a.git_sha, "overall": overall, "checks": checks, "verdicts": verdicts,
              "cameras": len(cams), "phone_screencaps_missing_for": missing_phone, "phone_dir": str(phone_dir),
              "references_embedded": [c for c, v in sheets.items() if v["reference"].endswith((".jpg", ".png", ".jpeg"))],
              "photos_root": str(photos_root) if photos_root else None, "sheets": sheets,
              "scope_note": "Editor-side data in the route corridor (G3-A/G3-B s ranges, 30 m). Not a phone measurement; visual-critic review (E8/T8) is a separate, human-agent step."}
    (out / "gate3-evidence.json").write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    write_md(result, audit, out)
    print(f"gate3 evidence: {overall}  " + "  ".join(f"{k}={v}" for k, v in verdicts.items()))
    print(f"  {out / 'gate3-evidence.md'}")
    sys.exit(0 if overall == "PASS" else 1)


def write_md(res: dict, audit: dict | None, out: Path):
    L = [f"# Gate 3 evidence (editor side), {res['region']}, repo {res['git_sha']}", "",
         f"Overall: **{res['overall']}**. {res['scope_note']}", "",
         "| Check | Verdict |", "|---|---|"]
    for k, v in res["verdicts"].items():
        L.append(f"| {k} | **{v}** |")
    L += ["", f"Phone screencaps: {res['cameras'] - len(res['phone_screencaps_missing_for'])}/{res['cameras']} cameras have one in `{res['phone_dir']}`. "
          f"References embedded for {len(res['references_embedded'])} cameras (CC0/PD only). Sheets: `sheets/<camera>.png`.", ""]
    for k, c in res["checks"].items():
        L += [f"## {k}: {c['verdict']}", "", c.get("rule", ""), ""]
        if k == "albedo_histogram":
            L += [f"{c['materials_checked']} materials, {c['fail']} FAIL, {c['warn']} WARN, {len(c['exempt'])} exempt (`{c['exempt_rule']}`). Histogram: `{c['histogram_png']}`.", ""]
            for r in c["failing"][:12]:
                L.append(f"- FAIL {r['name']}: mean {r['mean_srgb']}, p1 {r['p1']}, p99 {r['p99']}, {r['outside_frac']:.1%} outside")
        elif k == "texel_density":
            L += [f"{c['materials_measured']} textured materials measured ({c['untextured_materials']} flat-colour, {len(c['exempt'])} exempt impostors), {c['fail']} outside the band.", ""]
            for r in c["failing"][:12]:
                L.append(f"- FAIL {r['name']}: {r['mean']} texel/m (min {r['min']}, max {r['max']}, {r['area_m2']} m2)")
            L += ["", "Largest by area:"] + [f"- {r['name']}: {r['mean']} texel/m, {r['area_m2']} m2" for r in c["all"][:8]]
        elif k == "textures_within_budget":
            L += [f"{c['textures']} textures, estimated {c['estimated_mb']} MB on Android.", ""]
            L += [f"- {t['tier']}: {t['corridor_textures_mb']} MB vs budget {t['budget_mb']} MB: {t['status']}" for t in c["per_tier"]]
            L += [f"- over {TEX_MAX_DIM} px: {len(c['over_max_dim'])}; uncompressed large: {c['uncompressed_large_count']}", "", "Largest:"]
            L += [f"- {t['path'].split('/')[-1]}: {t['size']} {t['format']} {t['mb']} MB" for t in c["largest"][:6]]
        elif k == "meshes_normals_uv":
            L += [f"{c['meshes_checked']} meshes: missing normals {c['missing_normals']}, NaN {c['nan']}, missing UV0 {c['missing_uv0_total']} (flat-colour only: {c['note_flat_colour_without_uv0_count']}).", ""]
            L += [f"- FAIL {m['name']} ({m['path'].split('/')[-1]})" for m in c["failing"][:12]]
        elif k == "objects_vs_terrain":
            L += [f"Probe: `{c['probe']}`", "",
                  f"Renderers: {c['renderers_checked']} checked ({c['renderers_merged_skipped']} merged chunk meshes skipped), {c['renderers_floating']} floating, {c['renderers_sunk']} sunk, {c['renderers_no_ground']} without ground. "
                  f"Instances: {c['instances_probed']} probed, {c['instances_floating']} floating, {c['instances_sunk']} sunk, {c['instances_no_ground']} without ground.", ""]
            L += [f"- FAIL prototype {r['name']}: floating {r['floating']}, sunk {r['sunk']}, max above ground {r['max_bottom_above_ground_m']} m" for r in c["failing_prototypes"][:12]]
            L += [f"- FAIL renderer {r['name']}: {r['detail']}" for r in c["failing_renderers"][:12]]
            if c["exempt_prototypes"]:
                L += ["", "Exempt (mounted by design): " + ", ".join(r["name"] for r in c["exempt_prototypes"][:15])]
        elif k == "editor_renders_complete":
            L += [f"{c['rendered']}/{c['expected']} renders."] + [f"- missing {m}" for m in c["missing"][:10]]
        L.append("")
    (out / "gate3-evidence.md").write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    main()
