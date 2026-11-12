"""ADR 0143: project Putry median lamp forks (instances lamp_double*, fork = base + 10.9 m) through 494288 cameras;
compare with photo forks measured on look/z494-lamps.png (1280x960 rectified photo)."""
import json, glob, sys, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import poselib as P, proj
PH = [(222, 455), (228, 557), (186, 611), (124, 630), (58, 655)]
lamps = []
for f in glob.glob(str(P.ROOT / 'Data/raw/derived/bialystok-industrial-c/world/instances_*.json')):
    for it in json.load(open(f, encoding='utf-8'))['instances']:
        if 'lamp_double' in it['p'] and -700 < it['e'] < -400 and -80 < it['n'] < 80:
            lamps.append((it['e'], it['n'], it['z']))
lamps.sort(key=lambda t: -t[1])
cams = json.load(open(sys.argv[1], encoding='utf-8'))['cameras']
for c in cams:
    if '494288' not in c['id']: continue
    pts = [(e, n, z + 10.9) for e, n, z in lamps]
    pr = proj.project(c, pts, 1280, 960)
    vis = [(round(x * 1280), round(y * 960)) for (x, y), (e, n, z) in zip(pr, lamps)
           if ((e - c['pos'][0]) * (c['look_at'][0] - c['pos'][0]) + (n - c['pos'][1]) * (c['look_at'][1] - c['pos'][1])) > 0 and -100 < x * 1280 < 1380]
    vis.sort(key=lambda p: p[1])
    print(c['id'], 'proj forks (x,y) near->far:', vis[:6])
print('photo forks:', PH)
print('lamps', [(round(e,1), round(n,1), round(z,2)) for e, n, z in lamps])
