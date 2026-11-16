"""c-regen3-s23: budget and QA gate after the regeneration. before = artifacts/c-regen3-s23/before/data (git HEAD), after = worktree.

Exit 1 when: a camera has tris_high >= 2 000 000, a camera's Low grows by more than 2 %, far_field Low > 30 000 (test limit),
pavements tris_in != tris_out (ADR 0237), or gate3 landmarks are stale / the ADR 0236 key is missing after the rebuild.
Limits are the ones used by c-regen-s22 (docs/reports/INTEGRATION-2026-11-15-c-regen-s22.md).
"""
import json
import sys
from pathlib import Path

WT = Path(__file__).resolve().parents[3]
ART = WT / "artifacts/c-regen3-s23"
HIGH_LIMIT, LOW_GROWTH_PCT, FAR_LOW_LIMIT = 2_000_000, 2.0, 30_000


def find(o, key, path=""):
    """Every value stored under `key` anywhere in the document, with its path."""
    if isinstance(o, dict):
        for k, v in o.items():
            p = f"{path}.{k}" if path else k
            if k == key:
                yield p, v
            yield from find(v, key, p)
    elif isinstance(o, list):
        for i, v in enumerate(o[:50]):
            yield from find(v, key, f"{path}[{i}]")


def short(v, n=300):
    s = json.dumps(v, ensure_ascii=False)
    return s if len(s) <= n else s[:n] + f"... ({len(s)} chars)"


def main():
    red = []
    for r in sys.argv[1:] or ["bialystok-industrial-c", "bialystok-dojlidy"]:
        b, a = ART / "before/data" / r, WT / "Data/Regions" / r / "generated"
        qb, qa = (json.loads((p / "streetscape_qa.json").read_text(encoding="utf-8")) for p in (b, a))
        fb = {f["camera"]: f for f in qb["mesh_budget"]["frame_estimate"]}
        fa = {f["camera"]: f for f in qa["mesh_budget"]["frame_estimate"]}
        print(f"== {r}: cameras before {len(fb)} after {len(fa)}")
        for c in sorted(fa, key=lambda c: -fa[c]["tris_high"]):
            x, y = fb.get(c), fa[c]
            if not x:
                print(f"  NEW {c}: high {y['tris_high']} low {y['tris_low']}")
                if y["tris_high"] >= HIGH_LIMIT:
                    red.append(f"{r}/{c} high {y['tris_high']}")
                continue
            dh, dl = y["tris_high"] - x["tris_high"], y["tris_low"] - x["tris_low"]
            pl = 100.0 * dl / x["tris_low"]
            flag = ""
            if y["tris_high"] >= HIGH_LIMIT:
                flag += "  HIGH>=2M"; red.append(f"{r}/{c} high {y['tris_high']}")
            if pl > LOW_GROWTH_PCT:
                flag += "  LOW>+2%"; red.append(f"{r}/{c} low {pl:+.2f} %")
            print(f"  {c:34s} high {x['tris_high']:>8} -> {y['tris_high']:>8} ({dh:+7d})  low {x['tris_low']:>7} -> {y['tris_low']:>7} "
                  f"({dl:+6d}, {pl:+.2f} %)  mats {x.get('materials_high')} -> {y.get('materials_high')}{flag}")
            cats = {k: y["by_category_high"].get(k, 0) - x["by_category_high"].get(k, 0)
                    for k in set(x.get("by_category_high", {})) | set(y.get("by_category_high", {}))}
            cats = {k: v for k, v in cats.items() if v}
            if cats:
                print(f"      by category (High): {cats}")
        mx = max(fa.values(), key=lambda f: f["tris_high"])
        print(f"  max high: {mx['camera']} {mx['tris_high']}  (headroom to 2 M: {HIGH_LIMIT - mx['tris_high']})")
        for tag, p in (("before", b), ("after", a)):
            ff = json.loads((p / "far_field_qa.json").read_text(encoding="utf-8"))["tiers"]
            print(f"  far_field {tag}: Low {ff['Low']['total_triangles']} High {ff['High']['total_triangles']}")
            if tag == "after" and ff["Low"]["total_triangles"] > FAR_LOW_LIMIT:
                red.append(f"{r} far_field Low {ff['Low']['total_triangles']}")
        # ADR 0237 / 0236 checks named by the reviews (#125 P1-L, #124 P1-L)
        pav = list(find(qa, "pavements"))
        if not pav:
            red.append(f"{r}: no `pavements` report - build_world hook did not run"); print("  pavements: MISSING")
        for p, v in pav:
            print(f"  {p}: {short(v)}")
            if isinstance(v, dict) and v.get("enabled") is False:
                red.append(f"{r} pavements disabled (no pavement_rules override found - overrides.yaml merge lost it?)")
            if isinstance(v, dict) and "tris_in" in v and v.get("tris_in") != v.get("tris_out"):
                red.append(f"{r} pavements tris_in {v.get('tris_in')} != tris_out {v.get('tris_out')}")
        for key in ("overrides_stale", "crossing_kerb", "kerb_drops", "diagrams_replaced", "gate3_landmarks", "stale", "lamps"):
            for p, v in find(qa, key):
                if key == "stale" and "gate3" not in p:
                    continue
                if key == "lamps" and p != "furniture.lamps":
                    continue
                if key == "lamps":
                    v ={k: (len(x) if isinstance(x, list) else x) for k, x in v.items() if k.startswith(("by_family", "policy", "led_"))} if isinstance(v, dict) else v
                print(f"  {p}: {short(v)}")
                if key == "stale" and v:
                    red.append(f"{r} {p} = {short(v, 120)}")
        if r == "bialystok-industrial-c" and not list(find(qa, "diagrams_replaced")):
            red.append("C: furniture.roundabout_signs.diagrams_replaced missing (ADR 0236 not in the build; gate3 test would skip)")
        mb, ma = (json.loads((p / "world_manifest.json").read_text(encoding="utf-8")) for p in (b, a))
        nb, na = (len(m.get("materials", [])) for m in (mb, ma))
        print(f"  world_manifest materials: {nb} -> {na}")
    print("RED:" if red else "GREEN: all limits kept", *red, sep="\n  " if red else " ")
    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main())
