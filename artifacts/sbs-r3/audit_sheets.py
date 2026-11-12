"""Supplement baseline audit with decoded sheet bytes and diagnostic identities. Heavy pool required."""
from pathlib import Path
import hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/'artifacts/sbs-r3';EVIDENCE=ART/'evidence'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
refs={r['camera']:r for r in read(EVIDENCE/'inputs/sbs_references.json')['references']}
rows=[]
for state in ('Low-overcast','Low-clear','High-overcast','High-clear'):
    captured={camera:digest for p in (EVIDENCE/'renders'/state).glob('capture-*.json') for camera,digest in read(p)['render_sha256'].items()}
    for group in ('sheets','diagnostics'):
        directory=EVIDENCE/group/state
        metrics=read(directory/'metrics.json')
        for pair in metrics['pairs']:
            camera=pair['camera'];ref=refs[camera]
            assert pair['render_sha256']==captured[camera]
            assert pair['comparison_sha256']==ref['comparison_sha256']
            assert pair['photo_sha256']==ref['sha256']
            assert pair['tier']+'-'+pair['lighting']==state
            assert pair['pose_confidence']==ref['pose_confidence']
            path=directory/(camera+'.png')
            with Image.open(path) as image:
                assert image.width==960
                image.verify()
            rows.append({'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path)})
assert len(rows)==268 and len({r['path'] for r in rows})==268
current=read(ROOT/'Data/Regions/bialystok-industrial-c/sbs_recognition.json')
candidate=read(ART/'recognition-r3-baseline.json')
for key in ('assessments','history','counts','gate_result','source_review_sha256','render_git_sha'):
    assert current[key]==candidate[key],key
(ART/'SHEET-AUDIT.json').write_text(json.dumps({'status':'VERIFIED','sheet_count':268,'eligible':100,'diagnostic':168,
    'current_registry_matches_reviewed_candidate':True,'current_registry_sha256':sha(ROOT/'Data/Regions/bialystok-industrial-c/sbs_recognition.json'),
    'files':rows},indent=2)+'\n',encoding='utf-8')
print('VERIFIED:268 decoded 960px sheets, all diagnostic identities, current review registry matches candidate')
