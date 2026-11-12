"""osm_supports.py: nodes / ways tagged bridge:support or man_made=bridge (and any bridge=* way) in the window of the Biezenstwa
viaduct (region-local E 400..700, N -800..-620) of the Geofabrik extract. ADR 0144 source check for pier rows."""
import sys, glob
import osmium
from pyproj import Transformer
tr = Transformer.from_crs(2180, 4326, always_xy=True)
ox, oy = 777995.0, 596223.0
lo = tr.transform(ox + 400, oy - 800); hi = tr.transform(ox + 700, oy - 620)
class H(osmium.SimpleHandler):
    def __init__(s): super().__init__(); s.n = []; s.w = []
    def node(s, n):
        if lo[0] <= n.location.lon <= hi[0] and lo[1] <= n.location.lat <= hi[1]:
            t = dict(n.tags)
            if "bridge:support" in t or t.get("man_made") in ("bridge", "pier") or "pier" in str(t):
                s.n.append((n.id, t))
    def way(s, w):
        t = dict(w.tags)
        if "bridge:support" in t or t.get("man_made") == "bridge":
            s.w.append((w.id, t))
h = H(); h.apply_file(glob.glob("Data/raw/osm/*.osm.pbf")[0])
print("support nodes in window:", len(h.n), h.n[:10])
print("bridge:support / man_made=bridge ways (whole extract):", len(h.w), h.w[:5])
