"""Compose 960px diagnostic photo/render pairs from sealed gantry captures. Run under heavy."""
from pathlib import Path
import hashlib,html,json,math
from PIL import Image,ImageDraw,ImageFont,ImageOps
ROOT=Path(__file__).resolve().parents[2]
BASE=Path(__file__).with_name('pose-refinement1');INPUT=BASE/'inputs';OUT=BASE/'pairs'
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
plan=read(INPUT/'probe_plan.json');cameras=read(INPUT/'probe_cameras.json')['cameras']
assert 1<=len(plan['probes'])<=30 and len({p['probe'] for p in plan['probes']})==len(plan['probes'])
assert {c['id'] for c in cameras}=={p['probe'] for p in plan['probes']}
assert all(c['pose_confidence']=='C' for c in cameras)
assert plan['probe_cameras_sha256']==sha(INPUT/'probe_cameras.json')
assert plan['world_manifest_sha256']==sha(INPUT/'world_manifest.json')
assert plan['road_graph_sha256']==sha(INPUT/'road_graph.json')
input_files={'road_graph':'road_graph.json','probe_cameras':'probe_cameras.json','probe_plan':'probe_plan.json','import_receipt':'import_receipt.json',
             'production_cameras':'production_cameras.json','references':'references.json',
             'world_manifest':'world_manifest.json','materials_spec':'materials_spec.json'}
captures={}
for height in sorted({p['height'] for p in plan['probes']}):
    path=BASE/f'renders/1280x{height}/capture.json';capture=read(path)
    assert capture['status']=='OK' and capture['tier']=='Low' and capture['lighting']=='overcast'
    assert capture['diagnostic_only'] and capture['pose_confidence']=='C'
    assert capture['width']==1280 and capture['height']==height
    assert set(capture['cameras'])=={p['probe'] for p in plan['probes'] if p['height']==height}
    for key,name in input_files.items():assert capture['input_sha256'][key]==sha(INPUT/name),(key,height)
    captures[height]=capture
assert len({c['git_sha'] for c in captures.values()})==1,'mixed capture epoch'
OUT.mkdir(exist_ok=True);(OUT/'photos').mkdir(exist_ok=True)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',12)
rows=[];cards=[]
for p in plan['probes']:
    camera=p['probe'];capture=captures[p['height']]
    photo=ROOT/p['photo'];raw=BASE/f'renders/1280x{p["height"]}/{camera}.png'
    assert sha(photo)==p['photo_sha256'],'photo changed'
    assert sha(raw)==capture['render_sha256'][camera],'render changed'
    with Image.open(photo) as im:photo_image=im.convert('RGB')
    with Image.open(raw) as im:render=im.convert('RGB')
    assert render.size==(p['width'],p['height']) and photo_image.size==render.size
    pane_height=round(470*p['height']/p['width'])
    canvas=Image.new('RGB',(960,pane_height+140),(24,28,32));draw=ImageDraw.Draw(canvas)
    label=f'{camera} | C — diagnostyka, nie ocena D51'
    draw.text((8,5),label,font=font,fill='white')
    draw.text((8,25),'Zdjęcie — bez zmiany kadru',font=small,fill='#ddd')
    draw.text((498,25),'Render Low-overcast — ten sam FOV i proporcje',font=small,fill='#ddd')
    canvas.paste(ImageOps.contain(photo_image,(470,pane_height)),(0,44))
    canvas.paste(ImageOps.contain(render,(470,pane_height)),(490,44))
    parameters=f'Oś: {p["translation_axis"]}; przesunięcie {p["offset_m"]:+g} m; w lewo {p["left_delta_m"]:+g} m; h {p["horizon_y_fraction"]:.3f}; oko {p["nominal_eye_m"]:g} m'
    footer=[parameters,f'{p["author"]} | {p["license"]} | {p["page_url"]}',
            f'Photo SHA {p["photo_sha256"][:16]}… | Render SHA {capture["render_sha256"][camera][:16]}… | kod {capture["git_sha"][:8]}',
            'Poza i nominalne oko WORKING_VALUE. Portal + niezależna trwała kotwica; brak automatycznej promocji.']
    draw.multiline_text((8,pane_height+51),'\n'.join(footer),font=small,fill='#ddd',spacing=3)
    dest=OUT/(camera+'.png');canvas.save(dest)
    photo_name=photo.name;photo_copy=OUT/'photos'/photo_name
    if photo_copy.exists():assert sha(photo_copy)==p['photo_sha256']
    else:photo_copy.write_bytes(photo.read_bytes())
    rows.append({'probe':camera,'translation_axis':p['translation_axis'],'offset_m':p['offset_m'],
                 'left_delta_m':p['left_delta_m'],'horizon_y_fraction':p['horizon_y_fraction'],
                 'nominal_eye_m':p['nominal_eye_m'],'pose_confidence':'C',
                 'photo_sha256':p['photo_sha256'],'raw_sha256':capture['render_sha256'][camera],
                 'sheet_sha256':sha(dest),'width':960,'capture_git_sha':capture['git_sha']})
    cards.append(f'<article><h2>{html.escape(camera)}</h2><p>{html.escape(parameters)}</p>'
                 f'<a href="{html.escape(dest.name)}"><img loading="lazy" src="{html.escape(dest.name)}" width="960" alt="Zdjęcie i render; hipoteza C"></a>'
                 f'<p><a href="photos/{html.escape(photo_name)}">Natywne zdjęcie</a> · '
                 f'<a href="../renders/1280x{p["height"]}/{html.escape(camera)}.png">Natywny render</a> · '
                 f'<a href="{html.escape(p["page_url"],quote=True)}">Źródło: {html.escape(p["author"])}</a></p></article>')
body='<!doctype html><html lang="pl"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>SBS r3 — hipotezy przy bramownicy</title><style>body{background:#181c20;color:#eee;font:16px Arial;max-width:960px;margin:auto;padding:12px}img{max-width:100%;height:auto}a{color:#9df}h2{font-size:18px;overflow-wrap:anywhere}article{margin:24px 0}</style><h1>Hipotezy C — druga partia — zdjęcie i render</h1><p>Diagnostyka Low-overcast. FOV pozostaje stały; warianty pozycji, pitch i nominalnego oka opisano w planie i nagłówkach. To nie ocena D51 ani awans produkcyjnej pozy. Ujemne przesunięcie oznacza cofnięcie wzdłuż oryginalnego kierunku spojrzenia.</p>'+''.join(cards)+'</html>'
(OUT/'index.html').write_text(body,encoding='utf-8')
(OUT/'audit.json').write_text(json.dumps({'diagnostic_only':True,'gate_status':'UNVERIFIED','pose_confidence':'C','count':len(rows),'capture_git_sha':next(iter(captures.values()))['git_sha'],'input_sha256':{key:sha(INPUT/name) for key,name in input_files.items()},'pairs':rows},indent=2)+'\n',encoding='utf-8')
print('Composed and SHA-verified diagnostic refinement pairs at width960; no production source writes')

