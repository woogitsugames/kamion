import json,sys,yaml
from pathlib import Path
from shapely.geometry import Point
sys.path.insert(0,'tools/worldgen')
from streetscape import buildings_mesh as BM, knyszyn_church_0227 as KC, knyszyn_townhall_0227 as KT
r=Path('Data/Regions/knyszyn');fc=json.loads((r/'buildings.geojson').read_text(encoding='utf8'))
ov=yaml.safe_load((r/'overrides.yaml').read_text(encoding='utf8'))['overrides']
hero={**KC.hero_targets("knyszyn",fc),**KT.hero_targets("knyszyn",fc)}
b=BM.load(fc,(761611.,612607.),ov,hero=hero); pal=BM.house_palette(b)
p=Point(760943.5-761611,612382.3-612607)
lines=['# Typologia zabudowy wokół fontanny — WIP','', 'Zakres: bryły do 85 m od punktu fontanny; odległość do obrysu. Geometria BDOT i wysokości GUGiK są SOURCED względem datasetu; dane dachów i fasad generatora są WORKING_VALUE, chyba że jawny override opisuje ESTIMATED. Identyfikacja każdej fasady ze zdjęciem pozostaje otwarta.','', '| Obrys | Odległość m | Typ | Wysokość m / źródło | Dach | Elewacja |','|---|---:|---|---|---|---|']
for x in sorted((x for x in b if x['poly'].distance(p)<85),key=lambda x:x['poly'].distance(p)):
 pr=x['props'];i=x['id'];wall,roof=pal.get(i,('reguła / WORKING_VALUE','reguła / WORKING_VALUE'))
 selected=x['ovr'].get('roof_material')
 if selected: roof=selected+' / ESTIMATED'
 elif i in pal: roof=roof+' / WORKING_VALUE'
 if i in pal: wall=wall+' / WORKING_VALUE'
 if i in hero: roof='landmark / ESTIMATED'; wall='landmark / ESTIMATED'
 h=pr.get('height_m');src=pr.get('height_source','UNVERIFIED')
 lines.append(f"| `{i}` | {x['poly'].distance(p):.1f} | {x['typ']} / WORKING_VALUE | {h} / {src} | {roof} | {wall} |")
Path('artifacts/knyszyn-rynek-0227/TYPOLOGIA.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
print('rows',len(lines)-6)

