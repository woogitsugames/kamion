"""Read-only CPU identification of the historical four-tile fleet sheet."""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
MAIN=Path('C:/Users/matma/Documents/Claude/kamion')
ART=ROOT/'artifacts/car-paint-r1'
base=MAIN/'artifacts/cars-r10'
doc=json.loads((base/'car_cams.json').read_text(encoding='utf-8'))
poses={c['id']:c for c in doc['cameras']}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
result=dict(note='Historical sheet identity and frozen source poses only; current-world visibility must be rendered anew.',
            source_camera_json_sha256=sha(base/'car_cams.json'),
            source_camera_builder_sha256=sha(base/'add_dark_cams.py'),conditions=[])
for condition in ('High-overcast','High-clear'):
    folder=base/'m3'/condition
    sheet=Image.open(folder/'sheet_far.jpg').convert('RGB')
    # Montage 2x2, each 800x369 picture plus4px border on every side.
    assert sheet.size==(1616,754),sheet.size
    crops=[sheet.crop((4+x*808,4+y*377,804+x*808,373+y*377)) for y in range(2) for x in range(2)]
    small=[np.asarray(im.resize((160,74),Image.Resampling.LANCZOS),float) for im in crops]
    scores=[[] for _ in crops]
    for path in sorted(folder.glob('*.png')):
        im=Image.open(path).convert('RGB')
        if im.size!=(2340,1080):continue
        arr=np.asarray(im.resize((800,369),Image.Resampling.LANCZOS).resize((160,74),Image.Resampling.LANCZOS),float)
        for j,tile in enumerate(small):scores[j].append((float(np.abs(tile-arr).mean()),path))
    tiles=[]
    for j,candidates in enumerate(scores):
        candidates.sort(key=lambda q:q[0])
        first,second=candidates[:2]
        path=first[1]
        full=np.asarray(Image.open(path).convert('RGB').resize((800,369),Image.Resampling.LANCZOS),float)
        error=float(np.abs(full-np.asarray(crops[j],float)).mean())
        camera=poses.get(path.stem)
        assert camera is not None,path
        assert error<3 and second[0]>first[0]+1,(j,error,first,second)
        tiles.append(dict(tile=j+1,camera=path.stem,png_sha256=sha(path),
                          full_tile_mae=error,small_tile_mae=first[0],runner_up=second[1].stem,
                          runner_up_mae=second[0],source_pose=camera))
    result['conditions'].append(dict(condition=condition,sheet_sha256=sha(folder/'sheet_far.jpg'),tiles=tiles))
(ART/'r4-sheet-far-match.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
for c in result['conditions']:
    print(c['condition'],[(t['camera'],round(t['full_tile_mae'],3),round(t['runner_up_mae'],3)) for t in c['tiles']])
