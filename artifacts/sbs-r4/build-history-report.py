"""Offline report assembly: metadata/PNG file copying, no image decode or rendering."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys

ROOT=Path(__file__).resolve().parents[2];ART=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools/refs'))
from sbs_report import build_report

read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
states=('Low-overcast','Low-clear','High-overcast','High-clear')
paths=[ROOT/f'artifacts/sbs-r{number}/evidence' for number in (1,2,3,4)]
for path in paths:
    assert (path/'inputs/sbs_references.json').is_file(),path
    for state in states:
        for group in ('sheets','diagnostics'):assert (path/group/state/'metrics.json').is_file(),(path,group,state)
composition=read(ART/'composition-completed.json');full=read(ART/'full-render-completed.json')
assert composition['exit_code']==full['exit_code']==0
registry=ROOT/'Data/Regions/bialystok-industrial-c/sbs_recognition.json'
review=read(ART/'recognition-r4-baseline.json')
assert review['render_git_sha']==full['git_sha']
out=ROOT/'artifacts/sbs-gate3/latest'
data=build_report(paths,out,recognition_file=registry)
assert {run['id'] for run in data['runs']}=={'sbs-r1','sbs-r2','sbs-r3','sbs-r4'}
current=next(run for run in data['runs'] if run['id']=='sbs-r4')
assert set(current['states'])==set(states)
assert current['reference_snapshot']=='CAPTURED_INPUTS'
for state in states:
    row=current['states'][state]
    assert row['eligible']==25 and row['excluded']==17 and len(row['pairs'])==42
    assert row['render_git_sha']==full['git_sha'] and row['provenance_status']=='RECORDED'
eligible=[p for p in current['states']['Low-overcast']['pairs'] if p['pose_confidence'] in ('A','B')]
assert len(eligible)==25 and all(p['review_matches_current_pixels'] for p in eligible)
assert all(p['last_recognition_review']['reviewed_run']=='sbs-r4' for p in eligible)
assert data['recognition']['gate_result']==review['gate_result']=='FAIL'
receipt={'generated_at_utc':datetime.now(timezone.utc).isoformat(),'source_head':None,
    'scope':'Four-round offline history assembly; pixel-bound native D51, not a new visual or phone verdict',
    'runs':[run['id'] for run in data['runs']],'current_render_git_sha':full['git_sha'],
    'current_registry_sha256':sha(registry),'index_sha256':sha(out/'index.html'),'data_sha256':sha(out/'data.json'),
    'current_low_overcast_review_matches':25,'state_photometric_samples':{s:current['states'][s]['photometric_samples'] for s in states},
    'trend_count':len(data['trends'])}
(ART/'report-completed.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Report assembly verified: four rounds, 16 states, 25 pixel-matched native baseline assessments.')
