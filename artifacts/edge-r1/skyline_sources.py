"""Inventory existing skyline source heights while Unity owns the render slot."""
import collections
import json
import sys
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tools/worldgen'))
from streetscape import far_field as FF

gis=json.loads((ROOT/'Data/raw/derived/bialystok-industrial-c/world/far_field_gis_cache.json').read_text())
result={}
for sector in FF.SECTORS:
    buildings=[]
    for building in gis['buildings']:
        centre=np.array(building['rect']).mean(axis=0)
        if FF.sector_of(*centre) == sector:
            buildings.append(building)
    heights=collections.Counter(round(float(b['h']),2) for b in buildings)
    result[sector]=dict(
        source_buildings=len(buildings),
        typologies=dict(collections.Counter(b['typ'] for b in buildings)),
        heights_m_most_common=heights.most_common(12),
        tall_buildings=[dict(id=b['id'],height_m=b['h'],storeys=b.get('storeys'),
                             centre_en=np.array(b['rect']).mean(axis=0).round(2).tolist())
                        for b in sorted(buildings,key=lambda b:b['h'],reverse=True)[:12]])
result['note']='Source inventory only, no occlusion or rendered coverage measurement; height provenance requires checking the LoD join.'
(HERE/'skyline-source-inventory.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
for sector in FF.SECTORS:
    print(sector,result[sector]['source_buildings'],result[sector]['typologies'])
