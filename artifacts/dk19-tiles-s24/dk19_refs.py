"""Open-source street refs (KartaView/Panoramax, D43) near the mickiewicza control cameras."""
import json, sys, argparse
from pathlib import Path
WT = Path(r"C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\dk19-tiles-s24")
sys.path.insert(0, str(WT / "tools" / "refs"))
import open_sources as OS
from pyproj import Transformer
cams = json.loads((WT / "Data/Regions/bialystok-mickiewicza/control_cameras_place.authored.json").read_text(encoding="utf-8"))["cameras"]
ox, oy = 780043, 592127
tr = Transformer.from_crs(2180, 4326, always_xy=True)
pts = []
for i, c in enumerate(cams, 1):
    lon, lat = tr.transform(ox + c["pos_en"][0], oy + c["pos_en"][1])
    pts.append({"nr": i, "type": c["id"], "place": c["id"], "lat": lat, "lon": lon, "s_m": 0, "azimuth": c["heading_deg"]})
    print(i, c["id"], round(lat, 6), round(lon, 6), c["heading_deg"])
src = sys.argv[1]
a = OS.build_parser().parse_args(["--source", src, "--radius", "200", "--per-point", "4", "--max", "40",
    "--out", str(Path(r"C:\Users\matma\Documents\Claude\kamion\Data\raw\refs") / f"{src}-dk19"),
    "--art", str(WT / "artifacts/dk19-tiles-s24/refs" / src)])
e = OS.run(a, points=pts)
print("entries", len(e))
