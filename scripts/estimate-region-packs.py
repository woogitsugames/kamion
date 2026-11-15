"""ESTIMATED region pack sizes per region and tier (ADR 0234 §7). No Unity, no Data/raw: cited WORLD_MEMORY values
from the import logs quoted in the region ADRs, the APK-share factor k from ADR 0229 and the chunk GLB byte sums from
Data/Regions/<id>/generated/world_manifest.json (git) as a cross-check.

    python scripts/estimate-region-packs.py            # markdown table to stdout
    python scripts/estimate-region-packs.py --json     # machine-readable

Every number printed is ESTIMATED until `pwsh scripts/build-region-packs.ps1` prints the real bundle sizes.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# WORLD_MEMORY (MB) from scripts/import-region.ps1 runs, as quoted in the ADRs (date of the import differs per region).
WORLD_MEMORY = {
    # region: (low, high, source)
    "bialystok-industrial-c": (124.2, 267.0, "ADR 0188 (import-c-r4.log); HANDOVER s20 regen: Low 123.0 / High 265.8"),
    "bialystok-dojlidy": (99.6, 214.9, "ADR 0188 (import-doj-r4.log)"),
    "bialystok-maczka": (153.2, 420.4, "ADR 0208 (maczka r2)"),
    "bialystok-kleeberga": (156.7, 356.8, "ADR 0206"),
    "bialystok-knyszynska": (116.0, 260.2, "ADR 0208"),
    "dk65-01": (68.2, 165.9, "ADR 0205"),
    "dk65-02": (60.2, 139.3, "ADR 0210 (import r1 with water)"),
    "dk65-03": (50.5, 131.7, "ADR 0207"),
    "dk65-04": (76.1, 181.5, "ADR 0207"),
    "dk65-05": (75.5, 176.5, "ADR 0207"),
    "dk65-06": (59.0, 136.1, "ADR 0214 (r3)"),
    "dk65-07": (59.1, 136.5, "ADR 0214 (r3)"),
    "dk65-08": (55.5, 122.7, "ADR 0214 (r3)"),
    "dk65-09": (51.4, 122.4, "ADR 0214 (r3)"),
    "dk65-10": (49.0, 117.3, "ADR 0214 (r3)"),
    "dk65-11": (48.2, 113.0, "ADR 0214 (r3)"),
    "knyszyn-s": (40.8, 106.8, "ADR 0212 (Low) / ADR 0204 (High)"),
    "knyszyn": (95.5, 216.7, "ADR 0204 / ADR 0212"),
    "knyszyn-w": (54.0, 129.2, "ADR 0212 (Low) / ADR 0209 (High)"),
    "dk65-monki-01": (46.6, 113.6, "ADR 0212"),
    "dw671-tykocin-01": (45.7, 119.4, "ADR 0212"),
}

# MB of packed (LZ4/LZ4HC) build content per MB of WORLD_MEMORY, ADR 0229: k_min from the region C world share of the
# APK (71 MB / 88 MB, PERFORMANCE_BUDGETS §WorldC v3), k_max from APK 224 MB - no-world APK 58.07 - PBR 21 MB over 124.2.
K_MIN, K_MAX = 0.81, 1.18

# Shared bundle (truck + trailer Low/Medium, world PBR textures, prop/tree libraries, shaders), raw MB from the APK audit
# in docs/PERFORMANCE_BUDGETS.md (2026-11-10 rows): PBR 21.1, truck/trailer meshes ~22.6, other textures ~30 (55.4 total
# textures - 21.1 PBR - 4.2 world). Packed range = raw x [0.6, 1.0] (ASTC barely compresses, meshes ~2x): ESTIMATED.
COMMON_RAW_MB = 21.1 + 22.6 + 30.0
COMMON_K = (0.6, 1.0)

# Region C stays in the base APK (ADR 0234 §1); D67 corridor order (ADR 0229 set "d67" + the optional ones).
BASE_REGION = "bialystok-industrial-c"
D67 = ["bialystok-maczka", "bialystok-kleeberga", "bialystok-knyszynska", *[f"dk65-{i:02d}" for i in range(1, 12)],
       "knyszyn-s", "knyszyn"]
OPTIONAL = ["bialystok-dojlidy", "knyszyn-w", "dk65-monki-01", "dw671-tykocin-01"]


def glb_sums(region: str) -> tuple[float, float]:
    path = REPO / "Data" / "Regions" / region / "generated" / "world_manifest.json"
    if not path.exists():
        return float("nan"), float("nan")
    chunks = json.loads(path.read_text(encoding="utf-8"))["chunks"]
    high = sum(c.get("bytes", 0) for c in chunks) / 1e6
    low = sum((c.get("low") or {}).get("bytes", 0) for c in chunks) / 1e6
    return low, high


def rows() -> list[dict]:
    out = []
    for region in [BASE_REGION, *D67, *OPTIONAL]:
        low, high, src = WORLD_MEMORY[region]
        glb_low, glb_high = glb_sums(region)
        out.append({
            "region": region,
            "set": "base" if region == BASE_REGION else ("d67" if region in D67 else "optional"),
            "world_memory_low_mb": low, "world_memory_high_mb": high, "source": src,
            "pack_low_mb": [round(low * K_MIN), round(low * K_MAX)],
            "pack_high_mb": [round(high * K_MIN), round(high * K_MAX)],
            "glb_low_mb": round(glb_low, 1), "glb_high_mb": round(glb_high, 1),
        })
    return out


def fmt(r: list[int]) -> str:
    return f"{r[0]}–{r[1]}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    data = rows()
    common = [round(COMMON_RAW_MB * COMMON_K[0]), round(COMMON_RAW_MB * COMMON_K[1])]
    if a.json:
        json.dump({"status": "ESTIMATED", "k": [K_MIN, K_MAX], "common_mb": common, "regions": data}, sys.stdout, indent=2)
        print()
        return 0
    print(f"ESTIMATED (k = {K_MIN}–{K_MAX} MB pack per MB WORLD_MEMORY; common bundle {fmt(common)} MB, needed once)\n")
    print("| region | set | WORLD_MEMORY Low / High MB | pack Low MB | pack High MB | GLB Low / High MB (git manifest) |")
    print("|---|---|---|---|---|---|")
    for r in data:
        print(f"| {r['region']} | {r['set']} | {r['world_memory_low_mb']:.1f} / {r['world_memory_high_mb']:.1f} | "
              f"{fmt(r['pack_low_mb'])} | {fmt(r['pack_high_mb'])} | {r['glb_low_mb']:.0f} / {r['glb_high_mb']:.0f} |")
    for name, sel in (("d67 (16, bez C)", [r for r in data if r["set"] == "d67"]),
                      ("optional (4)", [r for r in data if r["set"] == "optional"])):
        lo = [sum(r["pack_low_mb"][i] for r in sel) for i in (0, 1)]
        hi = [sum(r["pack_high_mb"][i] for r in sel) for i in (0, 1)]
        print(f"| **sum {name}** | | | **{fmt(lo)}** | **{fmt(hi)}** | |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
