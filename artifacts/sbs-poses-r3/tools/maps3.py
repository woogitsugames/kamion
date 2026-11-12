import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import poselib as P
rnd=sys.argv[1]; key=sys.argv[2]; half=float(sys.argv[3])
cams=json.load(open(Path(__file__).parents[1]/rnd/'cameras.json'))['cameras']
sel=[c for c in cams if key in c['id']]
cols=['red','yellow','cyan','white','orange','lime','magenta']
import math
c0=sel[-1]['pos'][:2]
cx=sum(c['pos'][0] for c in sel)/len(sel); cy=sum(c['pos'][1] for c in sel)/len(sel)
out=str(Path(__file__).parents[1]/'maps'/f'{rnd}-{key}.png'); P.draw_map(out,[cx,cy],half,[(c['id'].split('-')[-1],c,cols[i%7],41.8 if '494288' in key else 90) for i,c in enumerate(sel)],scale=3)
