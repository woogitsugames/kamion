"""ADR 0097: house wall / roof shares and same-tone nearest neighbours, old hash palette vs house_palette."""
import json, sys
from collections import Counter
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
import numpy as np, yaml
from streetscape import buildings_mesh as BM
rdir = REPO / "Data" / "Regions" / "bialystok-industrial-c"
reg = yaml.safe_load((rdir / "region.yaml").read_text(encoding="utf-8"))
blds = BM.load(json.loads((rdir / "buildings.geojson").read_text(encoding="utf-8")), (reg["origin"]["x"], reg["origin"]["y"]), [])
hs = [b for b in blds if b["typ"] == "house"]
cen = np.array([b["poly"].centroid.coords[0] for b in hs])
OLD_W = ["plaster_beige", "plaster_cream", "plaster_light", "plaster_grey", "plaster_cream", "plaster_beige"]
OLD_R = ["roof_tiles_red", "roof_metal_graphite", "roof_tiles_brown", "roof_tiles_red", "roof_tiles_brown", "roof_metal_graphite", "roof_tiles_red"]
old = {b["id"]: (BM.hpick(b["id"], OLD_W), BM.hpick(b["id"], OLD_R, "roof")) for b in hs}
new = BM.house_palette(blds)
for name, pal in (("ADR 0094 hash", old), ("ADR 0097 neighbours", new)):
    w = Counter(pal[b["id"]][0] for b in hs)
    same_w = same_r = 0
    for i, b in enumerate(hs):
        d = np.hypot(*(cen - cen[i]).T); d[i] = 1e9; j = int(np.argmin(d))
        same_w += pal[b["id"]][0] == pal[hs[j]["id"]][0]
        same_r += pal[b["id"]][1] == pal[hs[j]["id"]][1]
    warm = (w["plaster_cream"] + w["plaster_beige"]) / len(hs)
    print(f"{name}: n {len(hs)}, warm {warm:.0%}, nearest neighbour same wall {same_w / len(hs):.0%}, same roof {same_r / len(hs):.0%}, {dict(w)}")
