"""ADR 0101: ratio-based material calibration check for World PBR pigments (P1-2 of REVIEW s10-0086).

Every calibrated pigment is judged on >= 2 cameras (one lit and one shaded side of the sun in `clear`) and always as a
ratio to a neutral reference ROI in the SAME frame (sky, plinth, asphalt...), never as an absolute sRGB level copied
from a photo taken under other weather/exposure/white balance. Absolute photo levels are used only to derive the
target ratio from the same pair of surfaces in the photograph (`photo_refs` in the spec).

ROIs are given in a 960 px-wide view (like artifacts/tint-gamma-r1/measure_rois.py); statistics read the full-size
PNG. Ratios:
  * `ratio_level`  = mean display level (mean of R,G,B in sRGB 0..255) target / reference - the convention of
                     ADR 0069 (cassette/plinth 36-40/105) and the s10 review (hall/sky 0.6..0.88);
  * `ratio_linear` = mean linear luminance target / reference (informative, not used for pass/fail).
Clip: fraction of ROI pixels with any channel >= 250 (`clip_250`); rib/relief readability: `spread` = p90 - p10 luma.

Usage:
  uv run --project tools/worldgen python tools/worldgen/qa/tint_ratio.py --round artifacts/tint-r2/r1 \
      [--spec tools/worldgen/qa/tint_ratio_spec.json] [--before artifacts/tint-r2/baseline] [--out file.json]
The round directory holds <Tier>-<lighting>/<camera>.png (WorldPbrTintRound layout). Exit code 1 if any check fails.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SPEC = Path(__file__).with_name("tint_ratio_spec.json")
LUMA = np.array([0.2126, 0.7152, 0.0722])


def srgb_to_linear(v: np.ndarray) -> np.ndarray:
    c = v / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def roi_pixels(path: Path, box960) -> np.ndarray:
    with Image.open(path) as im:
        scale = im.width / 960.0
        crop = im.convert("RGB").crop(tuple(round(x * scale) for x in box960))
        return np.asarray(crop, dtype=np.float64)


def roi_stats(a: np.ndarray) -> dict:
    luma = a @ LUMA
    mean = a.mean(axis=(0, 1))
    return {
        "mean_rgb": [round(float(x), 2) for x in mean],
        "level": float(mean.mean()),
        "lin_luma": float((srgb_to_linear(a) @ LUMA).mean()),
        "p10": float(np.percentile(luma, 10)),
        "p90": float(np.percentile(luma, 90)),
        "spread": float(np.percentile(luma, 90) - np.percentile(luma, 10)),
        "clip_250": float(np.any(a >= 250, axis=2).mean()),
    }


def compare(target: dict, ref: dict) -> dict:
    return {
        "ratio_level": target["level"] / max(ref["level"], 1e-6),
        "ratio_linear": target["lin_luma"] / max(ref["lin_luma"], 1e-9),
    }


def validate_spec(spec: dict) -> list[str]:
    """Method rules of ADR 0101; returns a list of violations (empty = valid)."""
    errors = []
    for mat, entry in spec["materials"].items():
        checks = entry.get("checks", [])
        cams = {c["camera"] for c in checks}
        sides = {c.get("side") for c in checks}
        if len(cams) < 2:
            errors.append(f"{mat}: needs >= 2 cameras, has {sorted(cams)}")
        if entry.get("calibrated", True) and not {"lit", "shaded"} <= sides:
            errors.append(f"{mat}: calibrated pigment needs a lit and a shaded check, has {sorted(s or '-' for s in sides)}")
        for c in checks:
            if "ref_roi" not in c or "ref" not in c:
                errors.append(f"{mat}/{c.get('id')}: no neutral reference ROI in the same frame")
            for key in ("roi", "ref_roi"):
                box = c.get(key)
                if box and not (0 <= box[0] < box[2] <= 960 and 0 <= box[1] < box[3]):
                    errors.append(f"{mat}/{c.get('id')}: bad {key} {box}")
    return errors


def _limit_ok(value: float, rng) -> bool:
    return rng is None or (rng[0] <= value <= rng[1])


def mask_fraction(mask_png: Path, box960) -> float:
    """Share of the ROI covered by a VisualQaRunner -qaMask render (flat magenta material slots)."""
    a = roi_pixels(mask_png, box960)
    return float(((a[..., 0] > 235) & (a[..., 1] < 25) & (a[..., 2] > 235)).mean())


def check_placement(spec: dict, masks_dir: Path) -> list[str]:
    """ROI on the material, reference off it (renderer masks only; instanced props/heroes have none)."""
    problems = []
    for mat, entry in spec["materials"].items():
        for c in entry["checks"]:
            # a check can name the scene its mask comes from (Low draws an HLOD where High has the chunk renderers)
            mdir = Path(f"{masks_dir}-{c['mask_scene']}") if c.get("mask_scene") else masks_dir
            png = mdir / mat / f"{c['camera']}_mask.png"
            if not png.exists() or mask_fraction(png, [0, 0, 960, 9999]) == 0.0:
                continue                      # no renderer slot (instanced/hero): use a change mask instead
            on, off = mask_fraction(png, c["roi"]), mask_fraction(png, c["ref_roi"])
            if on < 0.9 or off > 0.02:
                problems.append(f"{mat}/{c['id']}: ROI on mask {on:.2f} (>= 0.9), reference on mask {off:.2f} (<= 0.02)")
    return problems


def evaluate(spec: dict, round_dir: Path, before_dir: Path | None = None) -> dict:
    rows, failures = [], []
    for mat, entry in spec["materials"].items():
        for c in entry["checks"]:
            for cond_dir in sorted(p for p in round_dir.iterdir() if p.is_dir()):
                cond = cond_dir.name                      # e.g. High-clear
                lighting = cond.split("-", 1)[1] if "-" in cond else cond
                png = cond_dir / f"{c['camera']}.png"
                if not png.exists():
                    continue
                t, r = roi_stats(roi_pixels(png, c["roi"])), roi_stats(roi_pixels(png, c["ref_roi"]))
                row = {"material": mat, "check": c["id"], "side": c.get("side"), "camera": c["camera"],
                       "condition": cond, "target": t, "ref_name": c["ref"], "ref": r, **compare(t, r)}
                if before_dir is not None and (before_dir / cond / png.name).exists():
                    bp = before_dir / cond / png.name
                    bt, br = roi_stats(roi_pixels(bp, c["roi"])), roi_stats(roi_pixels(bp, c["ref_roi"]))
                    row["before"] = {"target": bt, "ref": br, **compare(bt, br)}
                verdict = []
                lim = c.get("limits", {}).get(lighting, {})
                if not _limit_ok(row["ratio_level"], lim.get("ratio_level")):
                    verdict.append(f"ratio_level {row['ratio_level']:.3f} outside {lim['ratio_level']}")
                if "clip_max" in lim and t["clip_250"] > lim["clip_max"]:
                    verdict.append(f"clip_250 {t['clip_250']:.3f} > {lim['clip_max']}")
                if "spread_min" in lim and t["spread"] < lim["spread_min"]:
                    verdict.append(f"spread {t['spread']:.1f} < {lim['spread_min']}")
                if "ref_drift_max" in lim and "before" in row:
                    drift = abs(r["level"] - row["before"]["ref"]["level"])
                    if drift > lim["ref_drift_max"]:
                        verdict.append(f"reference moved {drift:.1f} levels (> {lim['ref_drift_max']})")
                row["pass"] = not verdict
                row["fail_reasons"] = verdict
                if verdict and c.get("gate", True):
                    failures.append(f"{mat}/{c['id']}/{cond}: " + "; ".join(verdict))
                rows.append(row)
    return {"round": str(round_dir), "rows": rows, "failures": failures}


def photo_ratios(spec: dict) -> list[dict]:
    """Target ratios measured on the reference photographs (same pair of surfaces, same frame)."""
    out = []
    for p in spec.get("photo_refs", []):
        path = ROOT / p["file"]
        if not path.exists():
            out.append({**p, "missing": True})
            continue
        t, r = roi_stats(roi_pixels(path, p["roi"])), roi_stats(roi_pixels(path, p["ref_roi"]))
        out.append({**p, "target": t, "ref": r, **compare(t, r)})
    return out


def table(result: dict) -> str:
    lines = ["material/check                condition       target    ref   ratio  before  clip250 spread  ok"]
    for r in result["rows"]:
        b = r.get("before")
        before = f"{b['ratio_level']:6.3f}" if b else "   -  "
        lines.append(f"{r['material'][:14]:14s}/{r['check'][:14]:14s} {r['condition']:14s} {r['target']['level']:7.1f} "
                     f"{r['ref']['level']:6.1f} {r['ratio_level']:6.3f} {before} {r['target']['clip_250']:7.3f} "
                     f"{r['target']['spread']:6.1f}  {'ok' if r['pass'] else 'FAIL'}")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    ap.add_argument("--round", type=Path, required=True)
    ap.add_argument("--before", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--masks", type=Path, help="dir with <material>/<camera>_mask.png (run-masks.ps1) to verify ROI placement")
    args = ap.parse_args(argv)
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    errors = validate_spec(spec)
    if errors:
        print("SPEC INVALID:\n  " + "\n  ".join(errors))
        return 2
    if args.masks:
        placement = check_placement(spec, args.masks)
        print("ROI PLACEMENT: " + ("; ".join(placement) if placement else "ok"))
        if placement:
            return 2
    result = evaluate(spec, args.round, args.before)
    result["photo_refs"] = photo_ratios(spec)
    print(table(result))
    for p in result["photo_refs"]:
        if not p.get("missing"):
            print(f"photo {p['id']}: target {p['target']['level']:.1f} / ref {p['ref']['level']:.1f} = {p['ratio_level']:.3f}")
    print("FAILURES:\n  " + "\n  ".join(result["failures"]) if result["failures"] else "ALL CHECKS PASS")
    if args.out:
        args.out.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    return 1 if result["failures"] else 0


if __name__ == "__main__":
    sys.exit(main())
