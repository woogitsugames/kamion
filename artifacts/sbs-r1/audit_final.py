"""SBS r1 final audit: bind every frame, preserve byte-exact inputs, export all counters and overview PNGs."""
import hashlib,json,math,subprocess,sys,zipfile
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/'artifacts/sbs-r1';EVIDENCE=ART/'evidence';REGION=ROOT/'Data/Regions/bialystok-industrial-c'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
refs=read(REGION/'sbs_references.json')['references'];cameras=read(REGION/'sbs_cameras.json')['cameras']
ids={r['camera'] for r in refs};eligible={r['camera'] for r in refs if r['pose_confidence'] in ('A','B')}
assert len(ids)==len(refs)==42 and len(eligible)==25
sources={'cameras_sha256':REGION/'sbs_cameras.json','references_sha256':REGION/'sbs_references.json',
         'world_manifest_sha256':REGION/'generated/world_manifest.json','materials_spec_sha256':ROOT/'art-source/world/materials/materials_spec.json'}
source_hashes={k:sha(p) for k,p in sources.items()}
for r in refs:
    assert sha(ROOT/r['photo'])==r['sha256']
    assert sha(ROOT/r.get('comparison_photo',r['photo']))==r['comparison_sha256']
summary={'gate_status':'UNVERIFIED','note':'Editor evidence, no phone measurement; B approximate, C excluded. Historical counter deltas are not isolated SBS runtime cost.','states':{},'source_hashes':source_hashes,'captures':[]}
for state in ('Low-overcast','Low-clear','High-overcast','High-clear'):
    render_dir=EVIDENCE/'renders'/state;sheet_dir=EVIDENCE/'sheets'/state
    captures=[read(p) for p in sorted(render_dir.glob('capture-*.json'))]
    captured={camera:digest for c in captures for camera,digest in c['render_sha256'].items()}
    assert set(captured)==ids and sum(len(c['cameras']) for c in captures)==len(ids)
    assert {p.stem for p in render_dir.glob('*.png')}==ids
    for c in captures:
        assert c['status']=='OK' and c['tier']+'-'+c['lighting']==state
        for k,v in source_hashes.items():assert c[k]==v,(state,k)
        summary['captures'].append(c)
    for camera,digest in captured.items():
        p=render_dir/(camera+'.png');assert sha(p)==digest
        with Image.open(p) as im:im.verify()
    metrics=read(sheet_dir/'metrics.json')
    assert metrics['provenance_status']=='RECORDED' and not metrics['missing_renders']
    assert {m['camera'] for m in metrics['pairs']}==eligible
    assert {p.stem for p in sheet_dir.glob('*.png')}==eligible
    assert len(metrics['rejected_poses'])==17
    group=[r for r in refs if r['camera'] in eligible]
    overview_dir=ART/'overview'/state;overview_dir.mkdir(parents=True,exist_ok=True)
    for page in range(math.ceil(len(group)/4)):
        batch=group[page*4:page*4+4]
        canvas=Image.new('RGB',(960,500),'#202020');d=ImageDraw.Draw(canvas)
        d.text((8,6),f'{state} | approximate B poses only | page {page+1} | no gate PASS',fill='white')
        for i,r in enumerate(batch):
            p=sheet_dir/(r['camera']+'.png')
            with Image.open(p) as im:
                assert im.width==960
                h=round(470*r['height']/r['width'])
                panel=im.crop((0,24,960,24+h)).resize((480,round(h/2)),Image.Resampling.LANCZOS)
            x,y=(i%2)*480,32+(i//2)*230
            d.text((x+4,y),r['camera'],fill='white');canvas.paste(panel,(x,y+19))
        canvas.save(overview_dir/f'page-{page+1:02d}.png')
    summary['states'][state]={'renders':len(captured),'gate_sheets':len(metrics['pairs']),'rejected_poses':17,'overview_pages':math.ceil(len(group)/4)}
for k in ('git_sha','main_sha','cameras_sha256','references_sha256','world_manifest_sha256','materials_spec_sha256'):
    assert len({c[k] for c in summary['captures']})==1,('mixed epoch',k)
summary['render_git_sha']=summary['captures'][0]['git_sha'];summary['main_base_sha']=summary['captures'][0]['main_sha']
snapshot=EVIDENCE/'inputs';snapshot.mkdir(parents=True,exist_ok=True)
for p in sorted(REGION.glob('sbs_*.json')):
    if p.name!='sbs_pose_probes.json':(snapshot/p.name).write_bytes(p.read_bytes())
(snapshot/'world_manifest.json').write_bytes(sources['world_manifest_sha256'].read_bytes())
(snapshot/'materials_spec.json').write_bytes(sources['materials_spec_sha256'].read_bytes())
with zipfile.ZipFile(EVIDENCE/'inputs.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for p in sorted(snapshot.iterdir()):archive.write(p,p.name)
(EVIDENCE/'inputs.zip.sha256').write_text(sha(EVIDENCE/'inputs.zip')+'\n',encoding='utf-8')
(ART/'AUDIT.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
subprocess.run([sys.executable,str(ART/'summarize_stats.py'),'--renders',str(EVIDENCE/'renders'),
                '--baseline','C:/Users/matma/Documents/Claude/kamion/artifacts/sbs-gate3/renders','--output',str(ART/'counters')],check=True,cwd=ROOT)
print('VERIFIED: 42 photos, 168 final renders, 100 eligible sheets, 68 exclusions, 28 overview pages, one render epoch.')
