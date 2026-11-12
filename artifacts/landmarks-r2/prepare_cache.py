"""Copy only private map caches from main; preserve this session's fire-station maps."""
from pathlib import Path
import hashlib
import json
import shutil
from PIL import Image

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
MAIN=Path('C:/Users/matma/Documents/Claude/kamion')
spec=json.loads((ROOT/'art-source/world/materials/materials_spec.json').read_text(encoding='utf-8-sig'))
rows=[]
missing=set()
for name,entry in spec['sets'].items():
    info=entry.get('files',{}).get('Medium')
    if not info: continue
    for filename in info['files']:
        relative=Path('art-source/world/materials')/info['dir']/filename
        local,source=ROOT/relative,MAIN/relative
        action='retained_own_r1' if name=='fire_station' else 'retained_cache'
        if name!='fire_station' and source.exists():
            if not local.exists() or hashlib.sha256(local.read_bytes()).digest()!=hashlib.sha256(source.read_bytes()).digest():
                local.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(source,local)
                action='copied_main_cache'
            else: action='identical'
        valid=local.exists()
        if valid:
            try:
                with Image.open(local) as image: image.verify()
            except Exception:
                valid=False
        if not valid: missing.add(name)
        rows.append({'set':name,'file':relative.as_posix(),'action':action,'valid_png':valid})
result={'rows':rows,'missing_sets':sorted(missing),'all_ready':not missing}
(OUT/'material-cache.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('Missing sets:',','.join(sorted(missing)) or 'none')
print('Map files:',len(rows))
