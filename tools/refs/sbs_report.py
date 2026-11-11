"""Offline SBS report: recognition remains authoritative; photometric trends use matched samples only."""
from __future__ import annotations
from collections import Counter
from datetime import datetime,timezone
import json
import math
from pathlib import Path
import re
import shutil
import statistics
from sbs_photometry import valid_sha

ROOT=Path(__file__).resolve().parents[2]
STATES=('Low-overcast','Low-clear','High-overcast','High-clear')


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def compatibility(before,after):
    if any(row.get('pose_confidence') not in ('A','B') for row in (before,after)):return 'EXCLUDED_POSE'
    for key in ('comparison_sha256','pose_signature'):
        if not all(valid_sha(row.get(key)) for row in (before,after)):return 'MISSING_IDENTITY'
        if before[key]!=after[key]:return 'SOURCE_CHANGED' if key=='comparison_sha256' else 'POSE_CHANGED'
    if not before.get('metric_definition') or before.get('metric_definition')!=after.get('metric_definition'):return 'METRIC_DEFINITION_CHANGED'
    if not before.get('tier') or not before.get('lighting') or any(before.get(k)!=after.get(k) for k in ('tier','lighting')):return 'RENDER_STATE_CHANGED'
    for panel in ('photo','render'):
        for key in ('source_size_px','analysis_size_px'):
            values=[row.get(panel,{}).get(key) for row in (before,after)]
            if any(not isinstance(v,list) or len(v)!=2 or any(isinstance(x,bool) or not isinstance(x,int) or x<=0 for x in v) for v in values):return 'MISSING_RESOLUTION'
            if values[0]!=values[1]:return 'RESOLUTION_CHANGED'
        gradients=[row.get(panel,{}).get('gradient_width_px') for row in (before,after)]
        if any(isinstance(x,bool) or not isinstance(x,int) or x<=0 for x in gradients):return 'MISSING_RESOLUTION'
        if gradients[0]!=gradients[1]:return 'RESOLUTION_CHANGED'
    if not all(row.get('photometric_use') is True and row.get('photometry',{}).get('status')=='REVIEWED_SAMPLES' for row in (before,after)):return 'UNQUALIFIED_SAMPLES'
    if not all(valid_sha(row.get('mask_signature')) for row in (before,after)):return 'MISSING_MASK_IDENTITY'
    if before['mask_signature']!=after['mask_signature']:return 'MASK_CHANGED'
    return 'COMPARABLE'


def number(value):return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)


def sample_error(pair,key):
    photo=pair.get('photo',{}).get(key);render=pair.get('render',{}).get(key)
    return abs(render-photo) if number(photo) and number(render) else None


def trend_between(before,after):
    previous={p['camera']:p for p in before};current={p['camera']:p for p in after}
    skipped=Counter();rows=[]
    for camera in sorted(set(previous)|set(current)):
        if camera not in previous or camera not in current:
            skipped['COHORT_CHANGED']+=1;continue
        a,b=previous[camera],current[camera];status=compatibility(a,b)
        if status!='COMPARABLE':skipped[status]+=1;continue
        row={'camera':camera}
        if number(a.get('histogram_l1_distance')) and number(b.get('histogram_l1_distance')):
            row['histogram_l1_change']=b['histogram_l1_distance']-a['histogram_l1_distance']
        for key,label in (('asphalt_luma_mean_srgb_estimate','asphalt_luma_error_change'),('rms_contrast_srgb','contrast_error_change')):
            first,last=sample_error(a,key),sample_error(b,key)
            if first is not None and last is not None:row[label]=last-first
        rows.append(row)
    medians={key:round(statistics.median([r[key] for r in rows if key in r]),6)
             for key in ('histogram_l1_change','asphalt_luma_error_change','contrast_error_change') if any(key in r for r in rows)}
    return {'status':'COMPARABLE_SAMPLES' if rows else 'NO_COMPARABLE_SAMPLES','pairs':len(rows),'camera_ids':[r['camera'] for r in rows],
            'skipped':dict(skipped),'median_changes':medians,
            'note':'Diagnostic image samples, not D51 recognition or a measured material albedo.'}


def safe_camera(camera):
    if not isinstance(camera,str) or not re.fullmatch(r'sbs-[A-Za-z0-9_-]+',camera):raise ValueError('unsafe camera ID')
    return camera


def run_id(path):
    name=path.name if path.name.startswith('sbs-') else path.parent.name
    name=re.sub(r'[^A-Za-z0-9_-]','-',name)
    if not name or name in ('.','..'):raise ValueError('invalid report run name')
    return name


def collect_run(path,outdir):
    path=Path(path);name=run_id(path);states={};times=[];epochs=set()
    ref_path=path/'inputs/sbs_references.json'
    references=read(ref_path).get('references',[]) if ref_path.exists() else []
    refs={r['camera']:r for r in references}
    for state in STATES:
        metric_file=path/'sheets'/state/'metrics.json'
        if not metric_file.exists():continue
        metrics=read(metric_file)
        if metrics.get('missing_renders'):raise ValueError(f'incomplete SBS run: {path} {state}')
        if len({p['camera'] for p in metrics.get('pairs',[])})!=len(metrics.get('pairs',[])):raise ValueError('duplicate metric camera')
        rejected={r['camera']:r.get('reason','') for r in metrics.get('rejected_poses',[])}
        records={p['camera']:{**p,'sheet_root':path/'sheets'/state} for p in metrics.get('pairs',[])}
        if set(records)&set(rejected):raise ValueError('qualified metrics overlap excluded roster')
        diagnostic_file=path/'diagnostics'/state/'metrics.json'
        if diagnostic_file.exists():
            diagnostic=read(diagnostic_file)
            for key in ('render_captures','cameras_sha256','metric_definition'):
                if diagnostic.get(key)!=metrics.get(key):raise ValueError('diagnostic provenance differs from qualified metrics')
            for p in diagnostic.get('pairs',[]):
                if p['camera'] in records:continue
                if p['camera'] not in rejected or p.get('pose_confidence')!='C':raise ValueError('diagnostic cannot promote rejected or unknown pose')
                records[p['camera']]={**p,'sheet_root':path/'diagnostics'/state}
        rejected={r['camera']:r.get('reason','') for r in metrics.get('rejected_poses',[])}
        for camera,reason in rejected.items():records.setdefault(camera,{'camera':camera,'pose_confidence':'C','pose_reason':reason})
        pairs=[]
        for camera,record in records.items():
            safe_camera(camera);ref=refs.get(camera,{})
            pair={**record,'author':ref.get('author',''),'license':ref.get('license',''),'source_url':ref.get('page_url','')}
            sheet_root=pair.pop('sheet_root',None);pair['image']=None
            if sheet_root is not None:
                source=sheet_root/(camera+'.png')
                if not source.is_file():raise ValueError(f'missing report sheet: {source}')
                relative=Path('frames')/name/state/(camera+'.png');target=outdir/relative;target.parent.mkdir(parents=True,exist_ok=True)
                if source.resolve()!=target.resolve():shutil.copy2(source,target)
                pair['image']=relative.as_posix()
            if pair.get('pose_confidence') not in ('A','B','C'):raise ValueError('invalid report pose confidence')
            pairs.append(pair)
        captures=metrics.get('render_captures',[])
        for capture in captures:
            if capture.get('captured_at_utc'):times.append(capture['captured_at_utc'])
            if capture.get('git_sha'):epochs.add(capture['git_sha'])
        states[state]={'pairs':pairs,'eligible':sum(p.get('pose_confidence') in ('A','B') for p in pairs),
            'excluded':sum(p.get('pose_confidence')=='C' for p in pairs),'photometric_samples':sum(p.get('photometric_use') is True for p in pairs),
            'provenance_status':metrics.get('provenance_status','UNVERIFIED'),'metric_definition':metrics.get('metric_definition'),
            'render_git_sha':captures[0].get('git_sha') if captures else None,'main_base_sha':captures[0].get('main_sha') if captures else None}
    if not states:raise ValueError(f'no SBS metrics found: {path}')
    return {'id':name,'captured_at_utc':max(times) if times else None,'render_git_shas':sorted(epochs),'states':states,
            'reference_snapshot':'CAPTURED_INPUTS' if references else 'MISSING_REFERENCE_SNAPSHOT'}


def build_report(run_paths,outdir,recognition_file=None):
    outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
    runs=[collect_run(Path(path),outdir) for path in run_paths]
    if len({r['id'] for r in runs})!=len(runs):raise ValueError('duplicate report run IDs')
    runs.sort(key=lambda r:r.get('captured_at_utc') or '')
    recognition_path=Path(recognition_file) if recognition_file is not None else ROOT/'Data/Regions/bialystok-industrial-c/sbs_recognition.json'
    if not recognition_path.is_file():raise ValueError('recognition review file required; refusing to hide existing D51 verdict')
    recognition=read(recognition_path)
    review_by_camera={r['camera']:r for r in recognition.get('assessments',[])}
    for run in runs:
        for state in run['states'].values():
            for pair in state['pairs']:
                review=review_by_camera.get(pair['camera'])
                pair['last_recognition_review']=review
                pair['review_matches_current_pixels']=bool(review and all(valid_sha(pair.get(key)) and valid_sha(review.get(key)) and review[key]==pair[key] for key in ('render_sha256','comparison_sha256')))
    trends=[]
    for first,last in zip(runs,runs[1:]):
        for state in STATES:
            if state in first['states'] and state in last['states']:
                trends.append({'from':first['id'],'to':last['id'],'state':state,**trend_between(first['states'][state]['pairs'],last['states'][state]['pairs'])})
    data={'schema':'kamion/sbs-report/2','generated_at_utc':datetime.now(timezone.utc).isoformat(),'timezone':'Europe/Warsaw',
        'gate_note':'D51 recognisability is independent of image contrast, sky, grass tone and textures. Metrics never grant gate PASS.',
        'recognition':recognition,'runs':runs,'trends':trends}
    serialized=json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)
    (outdir/'data.json').write_text(serialized+'\n',encoding='utf-8')
    template=Path(__file__).with_name('sbs_report_template.html').read_text(encoding='utf-8-sig')
    page=template.replace('__SBS_DATA_JSON__',serialized.replace('<',r'\u003c'))
    (outdir/'index.html').write_text(page,encoding='utf-8')
    print(f'Report: {len(runs)} runs, {len(trends)} state comparisons; {outdir / "index.html"}')
    return data
