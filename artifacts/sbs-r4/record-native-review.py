"""Record a completed independent review. Light JSON and file hashing only."""
from pathlib import Path
from collections import Counter
from datetime import datetime
import copy,hashlib,json

ROOT=Path(__file__).resolve().parents[2];ART=Path(__file__).resolve().parent
REGION=ROOT/'Data/Regions/bialystok-industrial-c'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
write=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
request=read(ART/'recognition-native-request.json')
native=read(ART/'independent-native-review.json')
capture=read(ART/'full-render-completed.json')
refs=read(ART/'evidence/inputs/sbs_references.json')['references']
eligible={r['camera'] for r in refs if r['pose_confidence'] in ('A','B')}
assert len(eligible)==request['count']==native['count']==25
assert native['reviewed_run']=='sbs-r4' and native['reviewed_state']=='Low-overcast'
assert native['render_git_sha']==capture['git_sha'] and capture['exit_code']==0
assert not native['missing_camera_ids'] and len(native['viewed_camera_ids'])==25
assert set(native['viewed_camera_ids'])==eligible and native['excluded_C']==17
rows=native['assessments'];assert len(rows)==25 and {r['camera'] for r in rows}==eligible
assert len(request['rows'])==25 and {r['camera'] for r in request['rows']}==eligible
bindings={r['camera']:r for r in request['rows']}
for row in rows:
    bound=bindings[row['camera']]
    assert row['result'] in ('RECOGNISABLE','PARTIAL','NOT_RECOGNISABLE')
    assert row['reason'].strip()
    for key,path_key in (('render_sha256','raw'),('comparison_sha256','photo')):
        assert row[key]==bound[key]==sha(ROOT/bound[path_key]),(row['camera'],key)
    assert bound['render_git_sha']==capture['git_sha']
counts=dict(Counter(row['result'] for row in rows))
assert counts==native['counts']
if counts.get('PARTIAL',0) or counts.get('NOT_RECOGNISABLE',0):assert native['gate_result']=='FAIL'
for name in ('sbs_cameras.json','sbs_references.json'):
    assert sha(REGION/name)==sha(ART/'evidence/inputs'/name)
registry=REGION/'sbs_recognition.json';old=read(registry);old_sha=sha(registry)
assert old['reviewed_run']=='sbs-r3','Already recorded or unexpected registry; do not overwrite newer review'
old_indices={r['camera']:r for r in old['assessments']}
assert set(old_indices)==eligible
for row in rows:
    for key in ('index','station'):
        if key in old_indices[row['camera']]:row[key]=old_indices[row['camera']][key]
review_path=ART/'REVIEW-D51-BASELINE.md'
review={'schema':'kamion/sbs-recognition/1','criterion':'D51','gate_result':native['gate_result'],
        'reviewed_run':'sbs-r4','reviewed_stage':'baseline before production pose corrections',
        'reviewed_state':'Low-overcast','review_date':datetime.now().date().isoformat(),
        'recorded_at':datetime.now().astimezone().isoformat(),'reviewer':'sbs_visual_review, independent native-pair inspection',
        'source_review':review_path.relative_to(ROOT).as_posix(),'source_review_sha256':sha(review_path),
        'native_review_json_sha256':sha(ART/'independent-native-review.json'),
        'request_sha256':sha(ART/'recognition-native-request.json'),
        'review_method':'25 native raw images and 25 corresponding source photos; no 960px sheets inspected',
        'sheet_review_status':'NOT_REVIEWED','render_git_sha':capture['git_sha'],
        'world_manifest_sha256':capture['world_manifest_sha256'],
        'materials_spec_sha256':capture['materials_spec_sha256'],'counts':counts,
        'assessments':sorted(rows,key=lambda r:r['index'])}
history=old.pop('history',[]);history=[old,*history]
assert len({(r['reviewed_run'],r['reviewed_state'],r.get('render_git_sha')) for r in history})==len(history)
write(ART/'recognition-r4-baseline.json',review)
current=copy.deepcopy(review);current['history']=history
temp=registry.with_suffix('.sbs-r4.tmp');write(temp,current);temp.replace(registry)
write(ART/'recognition-recorded.json',{'recorded_at':review['recorded_at'],'count':25,'excluded_C':17,
    'counts':counts,'gate_result':review['gate_result'],'previous_registry_sha256':old_sha,
    'current_registry_sha256':sha(registry),'native_record_sha256':sha(ART/'recognition-r4-baseline.json'),
    'history_runs':[r['reviewed_run'] for r in history],'source_review_sha256':sha(review_path),
    'method':'Fresh independent native inspection; source bytes rehashed, no sheet inspection claimed'})
print('Recorded fresh native D51:',counts,'history:',[r['reviewed_run'] for r in history])
