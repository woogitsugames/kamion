"""ADR 0211 dev: fast stand-in for build_world up to the terrain conform (no plots / streetscape), pickled for the
tunnel module. Approximate zc (roads only, no paved areas) - only for developing roads/tunnels.py offline.
usage: uv run --project tools/worldgen python artifacts/tunnel-0211/dev_dump.py --region bialystok-kleeberga"""
import argparse
import pickle
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
import numpy as np  # noqa: E402
from roads import pipeline  # noqa: E402
from roads import standards as S  # noqa: E402
from terrain_mesh import conform as CF  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--region", default="bialystok-kleeberga")
a = ap.parse_args()
t0 = time.time()
w0 = pipeline.build(a.region)
deck_parts = [p for p in w0.buf.parts if p.layer == "bridge" and not p.src.endswith(":parapet")]
for p in deck_parts:
    p.footprint = True
deck, deck_mask = CF.rasterise(deck_parts, w0.hf)
thick = S.BRIDGE_DECK_THICKNESS + S.BRIDGE_KERB_H
clean, bad = CF.clean_under_bridges(w0.hf.z, deck, deck_mask, thick)
hf = pipeline.P.Heightfield(clean, w0.hf.bbox, (w0.hf.ox, w0.hf.oy))
w = pipeline.build(a.region, hf=hf)
print("pipeline", round(time.time() - t0), "s")
road_z, rmask = CF.rasterise([p for p in w.buf.parts if p.layer == "road"], w.hf)
deck_parts = [p for p in w.buf.parts if p.layer == "bridge" and not p.src.endswith(":parapet")]
for p in deck_parts:
    p.footprint = True
deck, deck_mask = CF.rasterise(deck_parts, w.hf)
for p in deck_parts:
    p.footprint = False
zjoin = np.where(rmask, road_z, -np.inf)
zc, dist = CF.conform(w.hf, zjoin, rmask)
zc = CF.clamp_under_decks(zc, deck, deck_mask, thick, rmask)
zc = CF.tidy(zc, zjoin, rmask, dist)
out = REPO / "artifacts" / "tunnel-0211" / "dev_dump.pkl"
w.ctx = None
with open(out, "wb") as f:
    pickle.dump({"w": w, "zc": zc, "mask": rmask, "deck": deck, "deck_mask": deck_mask}, f)
print("dumped", out, round(time.time() - t0), "s")
