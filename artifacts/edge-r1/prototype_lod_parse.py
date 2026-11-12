"""Read-only parser feasibility audit for the next skyline round."""
import json
import math
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
local=lambda tag:tag.rsplit('}',1)[-1]
path=ROOT/'Data/raw/gugik/lod1-2024-2061/2061_lod1_2024.zip'
records={}
examples=[]
with zipfile.ZipFile(path) as archive:
    for name in archive.namelist():
        if not name.lower().endswith(('.gml','.xml')):
            continue
        with archive.open(name) as stream:
            for _,element in ET.iterparse(stream,events=('end',)):
                if local(element.tag) != 'Building':
                    continue
                building_id=None
                height=None
                for child in element:
                    if local(child.tag) == 'stringAttribute' and child.get('name') == 'buildingId':
                        building_id=next((value.text.strip() for value in child
                                          if local(value.tag) == 'value' and value.text),'')
                    if local(child.tag) == 'measuredHeight' and child.text:
                        try:
                            height=float(child.text)
                        except ValueError:
                            pass
                if building_id and height is not None and math.isfinite(height) and height > 0:
                    records[building_id]=height
                    if len(examples)<6:
                        examples.append(dict(id=building_id,height=height,member=name))
                element.clear()

gis=json.loads((ROOT/'Data/raw/derived/bialystok-industrial-c/world/far_field_gis_cache.json').read_text())
guid=re.compile(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}')
normalized={match[0].upper():height for key,height in records.items() if (match:=guid.search(key))}
direct=[b for b in gis['buildings'] if b['id'] in records]
normal=[b for b in gis['buildings'] if b['id'].upper() in normalized]
result=dict(parsed_records=len(records),examples=examples,direct_ring_matches=len(direct),
            guid_ring_matches=len(normal),source='pinned local GUGiK LoD1 archive; streaming namespace-independent parse',
            note='Feasibility audit only. Production generator, cache, meshes and manifests unchanged.')
(HERE/'lod-parser-feasibility.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
