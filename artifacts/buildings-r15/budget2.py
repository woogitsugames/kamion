"""Draw budget on the control cameras, MeshRenderer draws AND instanced draws reported separately (review 0107 P1-r7-a).
    python budget2.py <ref dir> <round dir> [<round dir> ...] [--all]
Each dir holds stats.txt of scripts/visual-qa.ps1 (editor estimate, before SRP batching):
    <cam>: objects=N drawsEst=N shadowDrawsEst=N trisK=N
      <cam> instanced (props+trees): draws N, instances N, triangles Nk, cells N, forest HLOD cells N
Prints per round the deltas against the first dir: sum and worst camera of MeshRenderer draws, shadow draws,
instanced draws, their total, and triangles (mesh k + instanced k)."""
import re
import sys
from pathlib import Path


def load(d):
    out = {}
    for ln in (Path(d) / "stats.txt").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(\S+): objects=(\d+) drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)", ln)
        if m:
            out[m.group(1)] = {"mr": int(m.group(3)), "sh": int(m.group(4)), "tk": int(m.group(5)), "inst": None, "itk": 0, "ninst": 0}
            continue
        m = re.match(r"^\s+(\S+) instanced \(props\+trees\): draws (\d+), instances (\d+), triangles (\d+)k", ln)
        if m and m.group(1) in out:
            out[m.group(1)].update(inst=int(m.group(2)), ninst=int(m.group(3)), itk=int(m.group(4)))
    return out


args = [a for a in sys.argv[1:] if not a.startswith("--")]
ref = load(args[0])
for d in args[1:]:
    cur = load(d)
    cams = [c for c in ref if c in cur and ref[c]["inst"] is not None and cur[c]["inst"] is not None]
    print(f"== {d} vs {args[0]}: {len(cams)} cameras")
    for key, name in (("mr", "MeshRenderer draws"), ("sh", "shadow draws (MeshRenderer)"), ("inst", "instanced draws"),
                      ("ninst", "instances"), ("tk", "mesh tris k"), ("itk", "instanced tris k")):
        a, b = sum(ref[c][key] for c in cams), sum(cur[c][key] for c in cams)
        w = sorted(cams, key=lambda c: -(cur[c][key] - ref[c][key]))[:4]
        print(f"  {name:28s} {a:7d} -> {b:7d} ({b - a:+d}); worst: " +
              ", ".join(f"{c} {ref[c][key]}->{cur[c][key]} ({cur[c][key] - ref[c][key]:+d})" for c in w))
    tot = {c: (cur[c]["mr"] + cur[c]["inst"]) - (ref[c]["mr"] + ref[c]["inst"]) for c in cams}
    w = sorted(cams, key=lambda c: -tot[c])[:6]
    print(f"  {'MeshRenderer + instanced':28s} sum {sum(tot.values()):+d}; worst: " + ", ".join(f"{c} {tot[c]:+d}" for c in w))
    b = sorted(cams, key=lambda c: tot[c])[:3]
    print(f"  {'':28s} best: " + ", ".join(f"{c} {tot[c]:+d}" for c in b))
    if "--all" in sys.argv:
        for c in cams:
            print(f"    {c:28s} mr {ref[c]['mr']:4d}->{cur[c]['mr']:4d} sh {ref[c]['sh']:4d}->{cur[c]['sh']:4d} "
                  f"inst {ref[c]['inst']:4d}->{cur[c]['inst']:4d} tris {ref[c]['tk'] + ref[c]['itk']:5d}k->{cur[c]['tk'] + cur[c]['itk']:5d}k")
