"""Complete baseline evidence audit. Full PNG decoding/GLB hashing: heavy required."""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import hashlib,json,zipfile
from PIL import Image

ROOT=Path(__file__).resolve().parents[2];ART=Path(__file__).resolve().parent
EVIDENCE=ART/'evidence';INPUT=EVIDENCE/'inputs'
STATES=('Low-overcast','Low-clear','High-overcast','High-clear')
read=lambda path:json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def audit_archive(path,receipt):
    assert sha(path)==receipt['zip_sha256'],path
    with zipfile.ZipFile(path) as archive:
        expected={r['entry']:r for r in receipt['entries']}
        assert len(expected)==len(receipt['entries'])==len(archive.namelist())
        assert set(archive.namelist())==set(expected)
        for name,row in expected.items():
            data=archive.read(name)
            assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],name


def decode_png(path,*,expected=None,width=None):
    with Image.open(path) as image:
        assert image.format=='PNG',path
        image.load()  # Pixel decode; Image.verify alone would only validate PNG structure/CRC.
        size=image.size
    if expected is not None:assert size==expected,(path,size,expected)
    if width is not None:assert size[0]==width,(path,size)
    return {'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path),'width':size[0],'height':size[1]}


refs=read(INPUT/'sbs_references.json')['references']
by_id={r['camera']:r for r in refs}
ids=set(by_id);eligible={r['camera'] for r in refs if r['pose_confidence'] in ('A','B')}
assert len(refs)==len(ids)==42 and len(eligible)==25
assert len(ids-eligible)==17
cameras=read(INPUT/'sbs_cameras.json')['cameras']
assert len(cameras)==len({c['id'] for c in cameras}) and {c['id'] for c in cameras}==ids
source_paths={'cameras_sha256':INPUT/'sbs_cameras.json','references_sha256':INPUT/'sbs_references.json',
              'world_manifest_sha256':INPUT/'world_manifest.json','materials_spec_sha256':INPUT/'materials_spec.json'}
source_hashes={key:sha(path) for key,path in source_paths.items()}
full=read(ART/'full-render-completed.json');imported=read(ART/'import-completed.json')
assert full['exit_code']==imported['exit_code']==0
for key in ('world_manifest_sha256','materials_spec_sha256'):
    assert full[key]==imported[key]==source_hashes[key]
photos={}
for ref in refs:
    for path_key,hash_key in (('photo','sha256'),('comparison_photo','comparison_sha256')):
        path=ROOT/ref.get(path_key,ref['photo'])
        photos.setdefault(path.relative_to(ROOT).as_posix(),sha(path))
        assert photos[path.relative_to(ROOT).as_posix()]==ref[hash_key]

raw_rows=[];sheet_rows=[];all_captures=[];states={};low_pairs={}
for state in STATES:
    render_dir=EVIDENCE/'renders'/state
    captures=[read(path) for path in sorted(render_dir.glob('capture-*.json'))]
    expected_groups={ (1280,round(1280*r['height']/r['width'])) for r in refs }
    assert len(captures)==len(expected_groups)
    assert {(c['width'],c['height']) for c in captures}==expected_groups
    roster=[camera for c in captures for camera in c['cameras']]
    assert len(roster)==len(set(roster))==42 and set(roster)==ids
    assert {p.stem for p in render_dir.glob('*.png')}==ids
    captured={}
    for capture in captures:
        assert capture['status']=='OK' and capture['tier']+'-'+capture['lighting']==state
        assert capture['git_sha']==full['git_sha']
        for key,value in source_hashes.items():assert capture[key]==value,(state,key)
        assert set(capture['render_sha256'])==set(capture['cameras'])
        for camera,digest in capture['render_sha256'].items():
            ref=by_id[camera]
            assert capture['width']*ref['height']==capture['height']*ref['width']
            row=decode_png(render_dir/(camera+'.png'),expected=(capture['width'],capture['height']))
            assert row['sha256']==digest
            raw_rows.append(row);captured[camera]=digest
    all_captures.extend(captures)
    qualified=read(EVIDENCE/'sheets'/state/'metrics.json')
    excluded=[r['camera'] for r in qualified['rejected_poses']]
    assert len(excluded)==len(set(excluded))==17 and set(excluded)==ids-eligible
    for group,expected in (('sheets',eligible),('diagnostics',ids)):
        directory=EVIDENCE/group/state;metrics=read(directory/'metrics.json')
        roster=[p['camera'] for p in metrics['pairs']]
        assert len(roster)==len(set(roster))==len(expected) and set(roster)==expected
        assert {p.stem for p in directory.glob('*.png')}==expected
        assert metrics['provenance_status']=='RECORDED' and not metrics['missing_renders'] and not metrics['provenance_warnings']
        assert metrics['render_captures']==captures
        assert metrics['cameras_sha256']==source_hashes['cameras_sha256']
        assert metrics['gate_status']=='UNVERIFIED'  # Metrics do not confer D51.
        for key in ('landmarks_sha256','photometry_sha256','metric_definition'):
            assert metrics[key]==qualified[key]
        for name,key in (('sbs_landmarks.json','landmarks_sha256'),('sbs_photometry.json','photometry_sha256')):
            assert metrics[key]==(sha(INPUT/name) if (INPUT/name).exists() else None)
        for pair in metrics['pairs']:
            ref=by_id[pair['camera']]
            assert pair['render_sha256']==captured[pair['camera']]
            assert pair['comparison_sha256']==ref['comparison_sha256'] and pair['photo_sha256']==ref['sha256']
            assert pair['tier']+'-'+pair['lighting']==state and pair['pose_confidence']==ref['pose_confidence']
            row=decode_png(directory/(pair['camera']+'.png'),width=960)
            sheet_rows.append(row)
            if group=='sheets' and state=='Low-overcast':low_pairs[pair['camera']]={**pair,'sheet_sha256':row['sha256']}
    states[state]={'raw':42,'eligible_sheets':25,'diagnostic_sheets':42,
                   'photometric_samples':sum(p.get('photometric_use') is True for p in qualified['pairs'])}
for key in ('git_sha','main_sha',*source_hashes):
    assert len({c[key] for c in all_captures})==1,('mixed epoch',key)
assert len(raw_rows)==168 and len(sheet_rows)==268
assert len({r['path'] for r in raw_rows+sheet_rows})==436
with zipfile.ZipFile(EVIDENCE/'inputs.zip') as archive:
    expected={p.name for p in INPUT.iterdir() if p.is_file()}
    assert len(archive.namelist())==len(expected) and set(archive.namelist())==expected
    for name in expected:assert archive.read(name)==(INPUT/name).read_bytes()

world=read(INPUT/'world_manifest.json');world_files=[]
assert len(world['chunks'])==64
for chunk in world['chunks']:
    for mesh in (chunk,chunk['low']):
        assert sha(ROOT/mesh['file'])==mesh['sha256'],mesh['file']
        world_files.append({'path':mesh['file'],'sha256':mesh['sha256']})
assert len({r['path'] for r in world_files})==len(world_files)==128

review=read(ART/'recognition-r4-baseline.json');native=read(ART/'independent-native-review.json')
request=read(ART/'recognition-native-request.json');registry=read(ROOT/'Data/Regions/bialystok-industrial-c/sbs_recognition.json')
assert review['render_git_sha']==full['git_sha'] and review['sheet_review_status']=='NOT_REVIEWED'
assert len(review['assessments'])==25 and {r['camera'] for r in review['assessments']}==eligible
assert native['status']=='COMPLETE' and native['count']==request['count']==25
assert native['reviewed_run']==review['reviewed_run']=='sbs-r4'
assert native['reviewed_state']==review['reviewed_state']=='Low-overcast'
assert native['render_git_sha']==full['git_sha'] and native['gate_result']==review['gate_result']
assert native['excluded_C']==request['excluded_C']==17
assert len(native['viewed_camera_ids'])==25 and set(native['viewed_camera_ids'])==eligible and not native['missing_camera_ids']
assert len(native['assessments'])==25 and {r['camera'] for r in native['assessments']}==eligible
assert len(request['rows'])==25 and {r['camera'] for r in request['rows']}==eligible
native_by_id={r['camera']:r for r in native['assessments']}
request_by_id={r['camera']:r for r in request['rows']}
assert review['native_review_json_sha256']==sha(ART/'independent-native-review.json')
assert review['request_sha256']==sha(ART/'recognition-native-request.json')
assert sha(ROOT/review['source_review'])==review['source_review_sha256']
assert dict(Counter(r['result'] for r in review['assessments']))==review['counts']==native['counts']
versions=[registry,*registry.get('history',[])]
matched=[v for v in versions if v.get('render_git_sha')==review['render_git_sha'] and v.get('source_review_sha256')==review['source_review_sha256']]
assert len(matched)==1
for key in ('assessments','counts','gate_result','source_review_sha256','render_git_sha'):
    assert matched[0][key]==review[key]
derived=[]
for assessment in review['assessments']:
    pair=low_pairs[assessment['camera']]
    independent=native_by_id[assessment['camera']];bound=request_by_id[assessment['camera']]
    for key in ('result','reason','pose_warning','render_sha256','comparison_sha256'):
        assert independent[key]==assessment[key],(assessment['camera'],key)
    for key in ('render_sha256','comparison_sha256'):assert assessment[key]==pair[key]
    for key in ('render_sha256','comparison_sha256'):assert bound[key]==assessment[key]
    assert bound['render_git_sha']==full['git_sha'] and bound['pose_confidence']==by_id[assessment['camera']]['pose_confidence']
    assert (ROOT/bound['raw']).resolve()==(EVIDENCE/'renders/Low-overcast'/(assessment['camera']+'.png')).resolve()
    assert (ROOT/bound['photo']).resolve()==(ROOT/by_id[assessment['camera']].get('comparison_photo',by_id[assessment['camera']]['photo'])).resolve()
    assert Path(bound['raw_absolute']).resolve()==(ROOT/bound['raw']).resolve()
    assert Path(bound['photo_absolute']).resolve()==(ROOT/bound['photo']).resolve()
    derived.append({'camera':assessment['camera'],'render_sha256':pair['render_sha256'],
                    'comparison_sha256':pair['comparison_sha256'],'derived_sheet_sha256':pair['sheet_sha256'],
                    'sheet_reviewed_by_independent_critic':False})
other=read(ART/'other-states-visual-inspection.json')
other_record=read(ART/'other-states-review-recorded.json')
other_states=set(STATES)-{'Low-overcast'}
assert other['status']=='COMPLETE' and other['count']==len(other['inspections'])==75
assert other['capture_head']==full['git_sha'] and other['upstream_ADR0130_present'] is False
assert not other['missing_camera_ids'] and other['d51_reassessment'] is False
assert other_record['status']=='VERIFIED' and other_record['raw_count']==75 and other_record['unique_photo_count']==25
assert other_record['review_json_sha256']==sha(ART/'other-states-visual-inspection.json')
assert other_record['review_md_sha256']==sha(ART/'OTHER-STATES-VISUAL-REVIEW.md')
assert other_record['request_sha256']==sha(ART/'recognition-native-request.json')
assert {(r['state'],r['camera']) for r in other['inspections']}=={(state,camera) for state in other_states for camera in eligible}
decoded_by_path={r['path']:r for r in raw_rows}
for inspection in other['inspections']:
    raw_path=EVIDENCE/'renders'/inspection['state']/(inspection['camera']+'.png')
    photo_path=ROOT/request_by_id[inspection['camera']]['photo']
    assert inspection['viewed'] is True
    assert Path(inspection['raw_path']).resolve()==raw_path.resolve()
    assert Path(inspection['photo_path']).resolve()==photo_path.resolve()
    assert inspection['render_sha256']==decoded_by_path[raw_path.relative_to(ROOT).as_posix()]['sha256']
    assert inspection['comparison_sha256']==photos[photo_path.relative_to(ROOT).as_posix()]
other_archive=read(ART/'other-states-review-evidence.json')
assert len(other_archive['entries'])==4 and {e['entry'] for e in other_archive['entries']}=={
    'OTHER-STATES-VISUAL-REVIEW.md','other-states-visual-inspection.json',
    'recognition-native-request.json','other-states-review-recorded.json'}
for entry in other_archive['entries']:assert sha(ART/entry['entry'])==entry['sha256']
for stem in ('native-review-evidence','reference-metadata-evidence','other-states-review-evidence'):
    audit_archive(ART/(stem+'.zip'),read(ART/(stem+'.json')))

counter_receipt=read(ART/'counters-completed.json')
assert counter_receipt['current_counter_json_sha256']==sha(ART/'counters/camera-counters.json')
assert counter_receipt['historical_counter_json_sha256']==sha(ART/'counters-vs-r2/camera-counters.json')
for source in counter_receipt['source_logs']+counter_receipt['baseline_source_logs']:
    assert sha(ROOT/source['path'])==source['sha256']
counters=read(ART/'counters/camera-counters.json')['cameras']
assert len(counters)==len({(r['state'],r['camera']) for r in counters})==168
assert {(r['state'],r['camera']) for r in counters}=={(state,camera) for state in STATES for camera in ids}
for row in counters:
    assert row['draws_total_est']==row['draws_static_est']+row['draws_instanced_est']
    assert row['tris_total_k']==row['tris_static_k']+row['tris_instanced_k']

write(ART/'recognition-derived-sheet-binding.json',{'scope':'Mechanical derived-sheet association to reviewed native pixels; no sheet inspection claimed',
    'source_review_sha256':review['source_review_sha256'],'render_git_sha':full['git_sha'],'bindings':derived})
summary={'status':'VERIFIED','scope':'Baseline only; not a later pose variant or phone acceptance',
    'audited_at_utc':datetime.now(timezone.utc).isoformat(),'render_git_sha':full['git_sha'],
    'main_base_sha':all_captures[0]['main_sha'],'source_hashes':source_hashes,'states':states,
    'raw_count':168,'sheet_count':268,'eligible_sheet_count':100,'diagnostic_sheet_count':168,
    'verified_glb_files':world_files,'counter_rows':168,'counter_comparisons':counter_receipt['comparisons'],
    'baseline_d51':{'gate_result':review['gate_result'],'counts':review['counts'],'method':review['review_method']},
    'baseline_review_present_in_registry':True,'registry_sha256':sha(ROOT/'Data/Regions/bialystok-industrial-c/sbs_recognition.json'),
    'other_states_native_inspection':{'status':'COMPLETE','raw_count':75,'photo_count':25,'d51_reassessment':False},
    'capture_input_review':read(INPUT/'sbs_recognition.json')['reviewed_run'],
    'photo_hashes':photos,'captures':all_captures,'raw_files':raw_rows,'sheet_files':sheet_rows}
write(ART/'AUDIT.json',summary)
write(ART/'SHEET-AUDIT.json',{'status':'VERIFIED','scope':'Full pixel decoding in the same baseline audit process',
    'sheet_count':268,'raw_count':168,'unique_png_count':436,'files':sheet_rows,
    'derived_binding_sha256':sha(ART/'recognition-derived-sheet-binding.json')})
print('VERIFIED baseline: 168 fully decoded raw, 268 fully decoded 960px sheets, 128 GLB hashes, 168 counters, native review and exact archives.')
