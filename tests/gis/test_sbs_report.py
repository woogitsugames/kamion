"""Report regression checks: matched cohorts, pixel-bound reviews and offline HTML."""
from pathlib import Path
import json
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/refs'))
import sbs_report as report


def pair():
    return dict(camera='sbs-test',pose_confidence='B',comparison_sha256='a'*64,render_sha256='b'*64,
                pose_signature='c'*64,mask_signature='d'*64,metric_definition='v2',tier='Low',lighting='clear',
                photometric_use=True,photometry={'status':'REVIEWED_SAMPLES'},histogram_l1_distance=0.5,
                photo={'source_size_px':[1280,960],'analysis_size_px':[1280,960],'gradient_width_px':640,'asphalt_luma_mean_srgb_estimate':70,'rms_contrast_srgb':0.5},
                render={'source_size_px':[1280,960],'analysis_size_px':[1280,960],'gradient_width_px':640,'asphalt_luma_mean_srgb_estimate':90,'rms_contrast_srgb':0.8})


@pytest.mark.parametrize('key,value,reason',[
    ('pose_confidence','C','EXCLUDED_POSE'),('comparison_sha256','e'*64,'SOURCE_CHANGED'),
    ('pose_signature','f'*64,'POSE_CHANGED'),('metric_definition','v3','METRIC_DEFINITION_CHANGED'),
    ('lighting','overcast','RENDER_STATE_CHANGED'),('tier','High','RENDER_STATE_CHANGED'),
    ('photometric_use',False,'UNQUALIFIED_SAMPLES'),('mask_signature','e'*64,'MASK_CHANGED'),
    ('pose_signature',None,'MISSING_IDENTITY'),('mask_signature',None,'MISSING_MASK_IDENTITY')])
def test_trend_rejects_incompatible_samples(key,value,reason):
    a=pair();b=pair();b[key]=value
    assert report.compatibility(a,b)==reason
    assert report.trend_between([a],[b])['pairs']==0


def test_trend_uses_matched_cohort_and_measures_error_change():
    a=pair();b=pair();b['histogram_l1_distance']=0.3;b['render']['asphalt_luma_mean_srgb_estimate']=75
    b['render']['rms_contrast_srgb']=0.6
    extra=pair();extra['camera']='sbs-extra'
    result=report.trend_between([a,extra],[b])
    assert result['pairs']==1 and result['camera_ids']==['sbs-test']
    assert result['skipped']=={'COHORT_CHANGED':1}
    assert result['median_changes']=={'histogram_l1_change':-0.2,'asphalt_luma_error_change':-15,'contrast_error_change':-0.2}


def fixture_run(tmp_path):
    run=tmp_path/'sbs-r2'/'evidence';sheets=run/'sheets/Low-clear';sheets.mkdir(parents=True)
    (sheets/'sbs-test.png').write_bytes(b'image-fixture')
    (sheets/'metrics.json').write_text(json.dumps({'pairs':[pair()],'missing_renders':[],
        'rejected_poses':[{'camera':'sbs-rejected','reason':'Uncalibrated'}],
        'render_captures':[{'captured_at_utc':'2026-11-11T22:00:00Z','git_sha':'e'*40,'main_sha':'f'*40}]}),encoding='utf-8')
    inputs=run/'inputs';inputs.mkdir()
    (inputs/'sbs_references.json').write_text(json.dumps({'references':[{'camera':'sbs-test','author':'</script><script>alert(1)</script>','license':'CC0','page_url':'https://example.com/photo'}]}),encoding='utf-8')
    return run


def test_report_exports_offline_frames_and_escapes_embedded_json(tmp_path):
    run=fixture_run(tmp_path);out=tmp_path/'latest'
    review=tmp_path/'recognition.json';review.write_text(json.dumps({'gate_result':'FAIL','assessments':[{'camera':'sbs-test','result':'PARTIAL','render_sha256':'b'*64,'comparison_sha256':'a'*64}]}))
    data=report.build_report([run],out,review)
    assert (out/'frames/sbs-r2/Low-clear/sbs-test.png').read_bytes()==b'image-fixture'
    assert data['runs'][0]['states']['Low-clear']['excluded']==1
    assert data['runs'][0]['states']['Low-clear']['pairs'][0]['review_matches_current_pixels'] is True
    html=(out/'index.html').read_text(encoding='utf-8')
    assert '</script><script>alert(1)</script>' not in html
    embedded=html.split('<script id="sbs-data" type="application/json">')[1].split('</script>')[0]
    assert json.loads(embedded)==data
    assert '__SBS_DATA_JSON__' not in html
    assert data['recognition']['gate_result']=='FAIL'


def test_changed_render_does_not_inherit_old_recognition(tmp_path):
    run=fixture_run(tmp_path);review=tmp_path/'review.json'
    review.write_text(json.dumps({'assessments':[{'camera':'sbs-test','render_sha256':'f'*64}]}))
    data=report.build_report([run],tmp_path/'out',review)
    assert not data['runs'][0]['states']['Low-clear']['pairs'][0]['review_matches_current_pixels']


@pytest.mark.parametrize('camera',['../escape','sbs-../escape','C:/bad','sbs-x\\bad','<script>'])
def test_report_refuses_path_escape(camera):
    with pytest.raises(ValueError):report.safe_camera(camera)


def test_missing_qualified_sheet_is_not_silently_hidden(tmp_path):
    run=fixture_run(tmp_path);(run/'sheets/Low-clear/sbs-test.png').unlink()
    with pytest.raises(ValueError,match='missing report sheet'):report.build_report([run],tmp_path/'out')


def test_resolution_change_is_not_comparable():
    a=pair();b=pair();b['render']['source_size_px']=[640,480]
    assert report.compatibility(a,b)=='RESOLUTION_CHANGED'
    del b['render']['source_size_px']
    assert report.compatibility(a,b)=='MISSING_RESOLUTION'


def test_missing_review_cannot_erase_existing_fail(tmp_path):
    run=fixture_run(tmp_path)
    with pytest.raises(ValueError,match='recognition review file required'):
        report.build_report([run],tmp_path/'out',tmp_path/'typo.json')


def test_diagnostic_cannot_promote_rejected_pose(tmp_path):
    run=fixture_run(tmp_path);diag=run/'diagnostics/Low-clear';diag.mkdir(parents=True)
    p=pair();p['camera']='sbs-rejected'
    metrics=json.loads((run/'sheets/Low-clear/metrics.json').read_text());metrics['pairs']=[p]
    (diag/'metrics.json').write_text(json.dumps(metrics))
    with pytest.raises(ValueError,match='diagnostic cannot promote'):
        report.build_report([run],tmp_path/'out')


def test_diagnostic_requires_same_capture_epoch(tmp_path):
    run=fixture_run(tmp_path);diag=run/'diagnostics/Low-clear';diag.mkdir(parents=True)
    metrics=json.loads((run/'sheets/Low-clear/metrics.json').read_text());metrics['render_captures'][0]['git_sha']='a'*40
    (diag/'metrics.json').write_text(json.dumps(metrics))
    with pytest.raises(ValueError,match='diagnostic provenance differs'):
        report.build_report([run],tmp_path/'out')


def test_changed_photo_does_not_inherit_review_of_same_render(tmp_path):
    run=fixture_run(tmp_path);review=tmp_path/'review.json'
    review.write_text(json.dumps({'assessments':[{'camera':'sbs-test','render_sha256':'b'*64,'comparison_sha256':'f'*64}]}))
    data=report.build_report([run],tmp_path/'out',review)
    assert not data['runs'][0]['states']['Low-clear']['pairs'][0]['review_matches_current_pixels']


def test_gradient_resolution_must_be_known():
    a=pair();b=pair()
    del a['photo']['gradient_width_px'];del b['photo']['gradient_width_px']
    assert report.compatibility(a,b)=='MISSING_RESOLUTION'


def test_history_keeps_old_pixels_attached_to_old_verdict(tmp_path):
    run=fixture_run(tmp_path);review=tmp_path/'review.json'
    old={'reviewed_run':'sbs-r1','assessments':[{'camera':'sbs-test','result':'PARTIAL',
         'render_sha256':'b'*64,'comparison_sha256':'a'*64}]}
    latest={'reviewed_run':'sbs-r3','assessments':[{'camera':'sbs-test','result':'RECOGNISABLE',
            'render_sha256':'f'*64,'comparison_sha256':'a'*64}],'history':[old]}
    review.write_text(json.dumps(latest))
    data=report.build_report([run],tmp_path/'out',review)
    row=data['runs'][0]['states']['Low-clear']['pairs'][0]
    assert row['review_matches_current_pixels']
    assert row['last_recognition_review']['result']=='PARTIAL'
    assert row['last_recognition_review']['reviewed_run']=='sbs-r1'
    latest['assessments'][0]['render_sha256']='b'*64
    review.write_text(json.dumps(latest))
    data=report.build_report([run],tmp_path/'out',review)
    assert data['runs'][0]['states']['Low-clear']['pairs'][0]['last_recognition_review']['reviewed_run']=='sbs-r3'


def test_unreviewed_pixels_use_run_snapshot_not_future_reason(tmp_path):
    run=fixture_run(tmp_path);review=tmp_path/'review.json'
    old={'reviewed_run':'sbs-r1','assessments':[{'camera':'sbs-test','reason':'old scene',
         'render_sha256':'c'*64,'comparison_sha256':'a'*64}]}
    (run/'inputs/sbs_recognition.json').write_text(json.dumps(old))
    latest={'reviewed_run':'sbs-r3','assessments':[{'camera':'sbs-test','reason':'future scene',
            'render_sha256':'f'*64,'comparison_sha256':'a'*64}]}
    review.write_text(json.dumps(latest))
    data=report.build_report([run],tmp_path/'out',review)
    row=data['runs'][0]['states']['Low-clear']['pairs'][0]
    assert not row['review_matches_current_pixels']
    assert row['last_recognition_review']['reason']=='old scene'
    assert row['last_recognition_review']['reviewed_run']=='sbs-r1'


@pytest.mark.parametrize('history',[None,{},[None],['bad']])
def test_malformed_recognition_history_is_rejected(history):
    with pytest.raises(ValueError,match='recognition history'):
        report.recognition_versions({'history':history})


def test_missing_hashes_cannot_match_history():
    p={'camera':'sbs-test'}
    version={'assessments':[{'camera':'sbs-test','result':'PARTIAL'}]}
    assert not report.pixel_match(p,report.review_for_pair(p,[version],version))


@pytest.mark.parametrize('snapshot',[None,{'assessments':[]}])
def test_missing_snapshot_or_camera_does_not_attach_future_review(snapshot):
    p=pair()
    future={'assessments':[{'camera':'sbs-test','reason':'future scene',
                           'render_sha256':'f'*64,'comparison_sha256':'a'*64}]}
    assert report.review_for_pair(p,[future],snapshot) is None
