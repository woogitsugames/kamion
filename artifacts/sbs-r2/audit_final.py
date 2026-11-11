"""SBS r2 final audit: bind every frame, preserve byte-exact inputs, export all counters and overview PNGs."""
import hashlib,json,math,subprocess,sys,zipfile
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/'artifacts/sbs-r2';EVIDENCE=ART/'evidence';REGION=EVIDENCE/'inputs'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
refs=read(REGION/'sbs_references.json')['references'];cameras=read(REGION/'sbs_cameras.json')['cameras']
ids={r['camera'] for r in refs};eligible={r['camera'] for r in refs if r['pose_confidence'] in ('A','B')}
assert len(ids)==len(refs)==42 and len(eligible)==25
sources={'cameras_sha256':REGION/'sbs_cameras.json','references_sha256':REGION/'sbs_references.json',
         'world_manifest_sha256':REGION/'world_manifest.json','materials_spec_sha256':REGION/'materials_spec.json'}
source_hashes={k:sha(p) for k,p in sources.items()}
for r in refs:
    assert sha(ROOT/r['photo'])==r['sha256']
    assert sha(ROOT/r.get('comparison_photo',r['photo']))==r['comparison_sha256']
summary={'current_frame_gate_status':'UNVERIFIED','last_review_gate_status':'FAIL','note':'Editor evidence, no phone measurement; B approximate, C excluded. Counter comparison is camera-bound; all runtime/world differences must be reported separately.','states':{},'source_hashes':source_hashes,'captures':[]}
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
    assert metrics['render_captures']==captures
    assert metrics['cameras_sha256']==source_hashes['cameras_sha256']
    for pair in metrics['pairs']:
        ref=next(r for r in refs if r['camera']==pair['camera'])
        assert pair['render_sha256']==captured[pair['camera']] and pair['comparison_sha256']==ref['comparison_sha256']
        assert pair['tier']+'-'+pair['lighting']==state
    assert metrics['provenance_status']=='RECORDED' and not metrics['missing_renders']
    assert {m['camera'] for m in metrics['pairs']}==eligible
    assert {p.stem for p in sheet_dir.glob('*.png')}==eligible
    assert len(metrics['rejected_poses'])==17
    diagnostics=read(EVIDENCE/'diagnostics'/state/'metrics.json')
    assert {m['camera'] for m in diagnostics['pairs']}==ids
    diagnostic_dir=EVIDENCE/'diagnostics'/state
    assert {p.stem for p in diagnostic_dir.glob('*.png')}==ids
    for image_path in diagnostic_dir.glob('*.png'):
        with Image.open(image_path) as im:
            assert im.width==960
            im.verify()
    assert diagnostics['render_captures']==metrics['render_captures']
    assert diagnostics['photometry_sha256']==metrics['photometry_sha256']
    assert all(m['pose_confidence']==next(r['pose_confidence'] for r in refs if r['camera']==m['camera']) for m in diagnostics['pairs'])
    for name,key in (('sbs_photometry.json','photometry_sha256'),('sbs_landmarks.json','landmarks_sha256')):
        assert metrics[key]==(sha(REGION/name) if (REGION/name).exists() else None)
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
with zipfile.ZipFile(EVIDENCE/'inputs.zip') as archive:
    assert set(archive.namelist())=={p.name for p in REGION.iterdir() if p.is_file()}
    for name in archive.namelist():assert archive.read(name)==(REGION/name).read_bytes()
world=read(REGION/'world_manifest.json')
for chunk in world['chunks']:
    assert sha(ROOT/chunk['file'])==chunk['sha256']
    assert sha(ROOT/chunk['low']['file'])==chunk['low']['sha256']
summary['verified_glb_chunks']=len(world['chunks'])
summary['verified_glb_files_per_tier']={'High':len(world['chunks']),'Low':len(world['chunks'])}
review=read(REGION/'sbs_recognition.json');summary['recognition_source']=review['source_review'];summary['recognition_counts']=review['counts']
assert review['gate_result']=='FAIL' and len(review['assessments'])==25
old_world=read(ROOT/'artifacts/sbs-r1/evidence/inputs/world_manifest.json')
old_chunks={c['file']:c['sha256'] for c in old_world['chunks']}
old_low_chunks={c['low']['file']:c['low']['sha256'] for c in old_world['chunks']}
summary['low_world_chunks_changed_since_r1']=sum(old_low_chunks.get(c['low']['file'])!=c['low']['sha256'] for c in world['chunks'])
summary['world_chunks_changed_since_r1']=sum(old_chunks.get(c['file'])!=c['sha256'] for c in world['chunks'])
subprocess.run([sys.executable,str(ART/'summarize_stats.py'),'--renders',str(EVIDENCE/'renders'),
                '--baseline',str(ROOT/'artifacts/sbs-r1/evidence/renders'),'--output',str(ART/'counters')],check=True,cwd=ROOT)
counters=read(ART/'counters/camera-counters.json')['cameras']
assert {(r['state'],r['camera']) for r in counters}=={(state,camera) for state in summary['states'] for camera in ids}
summary['counter_rows']=len(counters)
summary['low_draw_increases']=[r['camera']+':'+r['state'] for r in counters if r['state'].startswith('Low-') and r.get('historical_delta_draws_total_est',0)>0]
summary['low_triangle_increases_over_2pct']=[r['camera']+':'+r['state'] for r in counters if r['state'].startswith('Low-') and r.get('historical_delta_tris_total_k',0)>0.02*(r['tris_total_k']-r.get('historical_delta_tris_total_k',0))]
summary['same_camera_input_as_r1']=source_hashes['cameras_sha256']==read(ROOT/'artifacts/sbs-r1/evidence/sheets/Low-overcast/metrics.json')['cameras_sha256']
(ART/'AUDIT.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print('VERIFIED: 42 photos, 168 final renders, 100 eligible sheets, 68 exclusions, 28 overview pages, one render epoch.')
