import json
from pathlib import Path
rural, verge_only, none = [], [], []
for d in sorted(Path("Data/Regions").iterdir()):
    m = d / "generated/world_manifest.json"
    q = d / "generated/streetscape_qa.json"
    if not m.exists():
        continue
    man = json.loads(m.read_text(encoding="utf-8"))
    vf = (man.get("verge_flora") or {}).get("triangles", 0)
    fp = {}
    if q.exists():
        fp = (json.loads(q.read_text(encoding="utf-8")).get("vegetation") or {}).get("field_plants") or {}
    n = sum(fp.values())
    if n and not d.name.startswith("bialystok-"):
        rural.append((d.name, n, vf))
    elif vf:
        verge_only.append((d.name, vf))
    else:
        none.append(d.name)
print("rural (plants + verge):", len(rural)); print(" ".join(t for t, _, _ in rural))
print("verge tufts only:", len(verge_only)); print(" ".join(t for t, _ in verge_only))
print("no change:", len(none)); print(" ".join(none))
Path("artifacts/fields2-s24/tile_list.json").write_text(json.dumps({"rural_plants_and_verge": rural, "verge_tufts_only": verge_only, "no_change": none}, indent=1), encoding="utf-8")
