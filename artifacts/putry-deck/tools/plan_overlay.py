"""ADR 0133: generated bridge meshes (chunk GLB, layer 'bridge') drawn over the GUGiK 0.08 m mosaic + lamp points."""
import sys, json, glob
sys.path.insert(0, 'C:/Users/matma/Documents/Claude/kamion/artifacts/sbs-poses/tools')
sys.path.insert(0, 'C:/Users/matma/Documents/Claude/kamion/.claude/worktrees/putry-deck/artifacts/putry-deck/tools')
import deckray
from pathlib import Path
from ortho_mosaic import mosaic, px
from PIL import ImageDraw
world = Path(sys.argv[1]); out = sys.argv[2]; inst_dir = Path(sys.argv[3]) if len(sys.argv) > 3 else world
deckray.WORLD = world
W = mosaic(); d = ImageDraw.Draw(W, 'RGBA')
col = {'road_asphalt': (0, 160, 255, 70)}
for f in sorted(world.glob('chunk_*[0-9].glb')):
    for name, prims in deckray.load(f).items():
        if name != 'bridge': continue
        for pos, idx, mat in prims:
            c = col.get(mat, (255, 140, 0, 50))
            for tri in idx:
                P = [px(-pos[i][0], pos[i][2]) for i in tri]
                if all(-50 < u < W.size[0] + 50 and -50 < v < W.size[1] + 50 for u, v in P):
                    d.polygon(P, fill=c)
for fn in glob.glob(str(inst_dir / 'instances_*.json')):
    for it in json.load(open(fn))['instances']:
        if it['p'].startswith('lamp'):
            u, v = px(it['e'], it['n'])
            d.ellipse([u - 14, v - 14, u + 14, v + 14], outline=(255, 0, 0, 255), width=5)
ref = json.load(open('C:/Users/matma/Documents/Claude/kamion/.claude/worktrees/putry-deck/artifacts/putry-deck/data/median_lamps_ortho.json'))
for k, e, n in ref:
    u, v = px(e, n); d.rectangle([u - 10, v - 10, u + 10, v + 10], outline=(0, 255, 0, 255), width=5)
W.crop((3000, 400, 8000, 3200)).resize((1500, 840)).save(out, quality=88)
