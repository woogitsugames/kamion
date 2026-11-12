"""Inspect the pinned LoD archive's real identifier/height layout, without modifying inputs."""
import json
import re
import sys
import zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tools/worldgen'))
from streetscape import far_field as FF

path=ROOT/'Data/raw/gugik/lod1-2024-2061/2061_lod1_2024.zip'
with zipfile.ZipFile(path) as archive:
    members=[dict(name=entry.filename,bytes=entry.file_size) for entry in archive.infolist()]
    xml=[entry for entry in archive.namelist() if entry.lower().endswith(('.xml','.gml'))]
    layouts=[]
    for name in xml[:4]:
        raw=archive.read(name).decode('utf-8',errors='replace')
        layouts.append(dict(name=name,
                            measured_height_tags=len(re.findall(r'<[^/>]*measuredHeight\b',raw)),
                            building_id_matches=re.findall(r'.{0,80}buildingId.{0,160}',raw)[:3],
                            height_examples=re.findall(r'<[^/>]*measuredHeight\b[^>]*>[^<]*',raw)[:3],
                            building_id_tag_examples=re.findall(r'<[^>]+(?:id|Id)=["\'][^"\']+["\'][^>]*>',raw)[:3]))
heights=FF._extract_lod1_heights(path)
gis=json.loads((ROOT/'Data/raw/derived/bialystok-industrial-c/world/far_field_gis_cache.json').read_text())
matching=sum(building['id'] in heights for building in gis['buildings'])
result=dict(archive=str(path.relative_to(ROOT)),members=members,
            layouts=layouts,current_extracted_heights=len(heights),
            current_ring_identifier_matches=matching,ring_buildings=len(gis['buildings']))
(HERE/'lod-join-audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('archive XML/GML:',len(xml),'height records:',len(heights),'ring joins:',matching)
for item in layouts:
    print(item['name'],item['measured_height_tags'],item['building_id_matches'][:1])
