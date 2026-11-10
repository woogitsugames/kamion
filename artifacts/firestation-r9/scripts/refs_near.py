"""List locally cached open reference photos near JRG2 with bearing to the building vs camera heading."""
import json, math, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
LAT, LON = 53.157322, 23.156306
RADIUS = float(sys.argv[1]) if len(sys.argv) > 1 else 160.0
stores = {
    "mapillary": REPO / "Data/raw/mapillary/bialystok-industrial-c",
    "mapillary_fs": REPO / "Data/raw/mapillary/fire-station",
    "kartaview": REPO / "Data/raw/refs/kartaview",
    "panoramax": REPO / "Data/raw/refs/panoramax",
    "commons": REPO / "Data/raw/refs/commons",
    "openverse": REPO / "Data/raw/refs/openverse",
}
for name, d in stores.items():
    mf = d / "manifest.jsonl"
    if not mf.exists():
        continue
    for ln in mf.read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        m = json.loads(ln)
        if m.get("lat") is None:
            continue
        dn = (LAT - m["lat"]) * 111320.0
        de = (LON - m["lon"]) * 111320.0 * math.cos(math.radians(LAT))
        dist = math.hypot(dn, de)
        if dist > RADIUS:
            continue
        brg = math.degrees(math.atan2(de, dn)) % 360
        hd = m.get("compass_angle", m.get("heading"))
        off = None if hd is None else round(((brg - hd + 180) % 360) - 180)
        print(name, m["file"], "dist", round(dist), "bearing_to_bldg", round(brg), "heading", None if hd is None else round(hd), "off", off,
              m.get("captured_at"), m.get("author"), m.get("license"), m.get("is_pano", ""))
