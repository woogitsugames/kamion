"""c-regen-s22: frame_estimate / far_field / lamps before (main, git) vs after (worktree)."""
import json, sys
from pathlib import Path
wt = Path(__file__).resolve().parents[3]
for r in sys.argv[1:] or ["bialystok-industrial-c", "bialystok-dojlidy"]:
    b = wt / "artifacts/c-regen-s22/before/data" / r
    a = wt / "Data/Regions" / r / "generated"
    qb, qa = (json.loads((p / "streetscape_qa.json").read_text(encoding="utf-8")) for p in (b, a))
    fb = {f["camera"]: f for f in qb["mesh_budget"]["frame_estimate"]}
    fa = {f["camera"]: f for f in qa["mesh_budget"]["frame_estimate"]}
    print(f"== {r}: cameras before {len(fb)} after {len(fa)}")
    over = []
    for c in sorted(fa):
        x, y = fb.get(c), fa[c]
        if not x:
            print(f"  NEW {c}: high {y['tris_high']} low {y['tris_low']}"); continue
        dh, dl = y["tris_high"] - x["tris_high"], y["tris_low"] - x["tris_low"]
        pl = 100.0 * dl / x["tris_low"]
        flag = ("  HIGH>=2M" if y["tris_high"] >= 2_000_000 else "") + ("  LOW>+2%" if pl > 2.0 else "")
        if flag: over.append(c)
        print(f"  {c:34s} high {x['tris_high']:>8} -> {y['tris_high']:>8} ({dh:+7d})  low {x['tris_low']:>7} -> {y['tris_low']:>7} ({dl:+6d}, {pl:+.2f} %){flag}")
    print("  max high:", max(f["tris_high"] for f in fa.values()), " over:", over)
    for tag, p in (("before", b), ("after", a)):
        ff = json.loads((p / "far_field_qa.json").read_text(encoding="utf-8"))
        t = ff["tiers"]
        print(f"  far_field {tag}: Low {t['Low']['total_triangles']} High {t['High']['total_triangles']}",
              {k: v for k, v in ff.items() if "powiat" in k or "missing" in k})
        print("    sectors Low:", {k: v["triangles"] for k, v in t["Low"]["sectors"].items()})
    for tag, q in (("before", qb), ("after", qa)):
        s = json.dumps(q); i = s.find('"lamps": {"by_family"')
        d = json.JSONDecoder().raw_decode(s[i + len('"lamps": '):])[0]
        print(f"  lamps {tag}:", d.get("by_family"), {k: (len(v) if isinstance(v, list) else v) for k, v in d.items() if k.startswith(("policy", "led_"))})
