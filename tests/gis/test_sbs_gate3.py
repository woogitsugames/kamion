"""Geometry and evidence integrity checks for ADR 0103 (no Unity/network)."""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('sbs_gate3', ROOT/'tools/refs/sbs_gate3.py')
sbs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sbs)


def test_true_north_heading_accounts_for_grid_convergence():
    t = Transformer.from_crs(4326,2180,always_xy=True)
    grid = sbs.grid_heading(23.15,53.16,0,t)
    assert 355 < grid < 359  # Bialystok is east of the CS92 central meridian.
    look = sbs.pose(0,0,135,grid,0)
    assert look[0] < 0 and look[1] > 39


def test_fov_and_horizon_projection():
    fov = sbs.vfov(90,16/9)
    assert fov == pytest.approx(58.715507,abs=1e-5)
    pitch = np.degrees(np.arctan((2*0.7-1)*np.tan(np.radians(fov)/2)))
    look = sbs.pose(10,20,130,90,pitch)
    assert look[0] > 10 and look[2] > 130
    with pytest.raises(ValueError): sbs.vfov(180,1)


def test_bilinear_nmt_sampling_and_bounds(tmp_path,monkeypatch):
    np.array([[0,10],[20,30]],dtype='<u2').tofile(tmp_path/'height.r16')
    (tmp_path/'terrain.json').write_text(json.dumps({'bbox':[0,0,1,1],'spacing_m':1,
        'samples':[2,2],'encoding':{'file':'height.r16','offset_m':120,'scale_m_per_unit':0.1}}))
    monkeypatch.setattr(sbs,'ROOT',tmp_path); monkeypatch.setattr(sbs,'REGION',tmp_path)
    sample = sbs.ground_sampler()
    assert sample(0.5,0.5) == pytest.approx(121.5)
    with pytest.raises(ValueError): sample(-1,0)


def test_committed_set_has_unique_licensed_photos_and_file_seated_poses():
    cameras = sbs.read(sbs.REGION/'sbs_cameras.json')['cameras']
    refs = sbs.read(sbs.REGION/'sbs_references.json')['references']
    assert len(refs) >= 20
    assert len({r['source_id'] for r in refs}) == len(refs)
    assert {r['camera'] for r in refs} == {c['id'] for c in cameras}
    assert {r['segment'] for r in refs} == {'G3-A','G3-B'}
    for c,r in zip(cameras,refs):
        assert c['seat']=='file' and c['kind']=='photo_match'
        assert c['id'].startswith('sbs-')
        assert r['author'] and r['license'] in ('CC BY-SA 4.0','CC0','CC BY 3.0')
        assert len(r['sha256'])==64


def test_compose_rejects_missing_and_wrong_aspect(tmp_path,monkeypatch):
    region=tmp_path/'region'; region.mkdir(); renders=tmp_path/'renders'; renders.mkdir()
    Image.new('RGB',(40,30),'gray').save(tmp_path/'photo.png')
    ref={'pose_confidence':'B','camera':'sbs-test','photo':'photo.png','horizon_y_fraction':0.5,'pose_status':'WORKING_VALUE',
         'width':40,'height':30,'author':'Example','license':'CC BY-SA 4.0','captured_at':'2020','page_url':'https://www.mapillary.com/'}
    sbs.write(region/'sbs_references.json',{'references':[ref]})
    monkeypatch.setattr(sbs,'ROOT',tmp_path);monkeypatch.setattr(sbs,'REGION',region)
    with pytest.raises(SystemExit): sbs.compose(renders,tmp_path/'out',historical=True)
    Image.new('RGB',(40,20),'gray').save(renders/'sbs-test.png')
    with pytest.raises(ValueError,match='aspect mismatch'): sbs.compose(renders,tmp_path/'out',historical=True)
    Image.new('RGB',(40,30),'gray').save(renders/'sbs-test.png')
    sbs.compose(renders,tmp_path/'out',historical=True)
    report=sbs.read(tmp_path/'out/metrics.json')
    assert len(report['pairs'])==1 and not report['missing_renders']
    assert report['gate_status']=='UNVERIFIED'


def test_luma_histogram_counts_all_pixels_and_empty_asphalt_is_null():
    m=sbs.measurements(Image.new('RGB',(30,20),'white'),0.5)
    assert sum(m['histogram_32'])==600
    assert m['sky_asphalt_ratio_estimate'] is None


def test_authored_area_masks_and_overlap_rejection():
    top=[[0,0],[1,0],[1,0.4],[0,0.4]]
    bottom=[[0,0.6],[1,0.6],[1,1],[0,1]]
    im=Image.new('RGB',(100,100),'gray')
    m=sbs.measurements(im,0.5,{'sky':[top],'asphalt':[bottom]})
    assert m['sky_asphalt_ratio_estimate']==pytest.approx(1,abs=0.05)
    assert m['mask_method'].startswith('authored')
    with pytest.raises(ValueError,match='overlap'):
        sbs.measurements(im,0.5,{'sky':[top],'asphalt':[top]})


def test_perspective_rectification_rays_and_fisheye_center():
    x,y=sbs.projection_grid(101,101,0.5,'perspective',[0.5,0,0])
    assert x[50,50]==0 and y[50,50]==0
    assert x[50,100]==pytest.approx(50/101)
    fx,fy=sbs.projection_grid(101,101,0.5,'fisheye',[0.5,0,0])
    assert fx[50,50]==0 and fy[50,50]==0
    assert fx[50,100]==pytest.approx(0.5*np.arctan(100/101))
    assert 0<fx[50,100]<x[50,100]


def test_sky_asphalt_brightness_ratio_is_separate_from_area():
    a=np.full((100,100,3),50,dtype='uint8');a[:50]=200
    m=sbs.measurements(Image.fromarray(a),0.5)
    assert m['sky_luma_mean_srgb_estimate']==200
    assert m['asphalt_luma_mean_srgb_estimate']==50
    assert m['sky_asphalt_luma_ratio_estimate']==4
    assert m['sky_asphalt_area_ratio_estimate']!=4


def test_rectification_does_not_fill_missing_pixels(tmp_path):
    a=np.zeros((60,80,3),dtype='uint8');a[:,:,0]=np.arange(80)
    source=tmp_path/'photo.png';Image.fromarray(a).save(source)
    meta={'camera_type':'perspective','camera_parameters':[0.7,0,0],'exif_orientation':3}
    focal,w,h=sbs.rectify(source,meta,tmp_path/'rectified.png')
    assert focal>=0.7 and (w,h)==(1280,960)
    corrected=np.asarray(Image.open(tmp_path/'rectified.png'))
    assert corrected[:,:,0].min()>=a[:,:,0].min()
    assert corrected[:,:,0].max()<=a[:,:,0].max()
    assert sbs.rectified_horizon(0.5,80,60,meta,focal)==0.5
    meta['exif_orientation']=6
    with pytest.raises(ValueError,match='unsupported'):sbs.rectify(source,meta,tmp_path/'invalid.png')


def test_vanishing_horizon_from_road_edges_and_degenerate_rejection():
    assert sbs.vanishing_horizon([[[0,1],[0.4,0.6]],[[1,1],[0.6,0.6]]]) == pytest.approx([0.5,0.5])
    with pytest.raises(ValueError,match='parallel'):
        sbs.vanishing_horizon([[[0,0],[1,0]],[[0,1],[1,1]]])


def test_compose_quarantines_rejected_and_unreviewed_poses(tmp_path,monkeypatch):
    monkeypatch.setattr(sbs,'REGION',tmp_path)
    sbs.write(tmp_path/'sbs_references.json',{'references':[
        {'camera':'bad','pose_confidence':'C','pose_reason':'screen intersection'},
        {'camera':'unreviewed'}]})
    sbs.compose(tmp_path/'renders',tmp_path/'out',historical=True)
    report=sbs.read(tmp_path/'out/metrics.json')
    assert not report['pairs'] and not report['missing_renders']
    assert {r['camera'] for r in report['rejected_poses']}=={'bad','unreviewed'}


def test_all_committed_poses_have_explicit_confidence_and_j1_is_quarantined():
    refs=sbs.read(sbs.REGION/'sbs_references.json')['references']
    bad={'810896133189484','339463879238809','962702164479831','182011943700132','326454015490067','1406533339711789'}
    for ref in refs:
        assert ref['pose_confidence'] in ('A','B','C')
        if ref['source_id'] in bad: assert ref['pose_confidence']=='C'


def test_compose_rejects_capture_from_different_camera_snapshot(tmp_path,monkeypatch):
    monkeypatch.setattr(sbs,'REGION',tmp_path)
    sbs.write(tmp_path/'sbs_references.json',{'references':[]})
    sbs.write(tmp_path/'sbs_cameras.json',{'cameras':[]})
    render=tmp_path/'renders';render.mkdir()
    sbs.write(render/'capture-test.json',{'status':'OK','cameras_sha256':'stale'})
    with pytest.raises(ValueError,match='stale render capture'):
        sbs.compose(render,tmp_path/'out')


def test_capture_hashes_bind_the_actual_render_pixels(tmp_path,monkeypatch):
    import hashlib
    monkeypatch.setattr(sbs,'REGION',tmp_path)
    monkeypatch.setattr(sbs,'ROOT',tmp_path)
    renders=tmp_path/'renders';renders.mkdir()
    photo=tmp_path/'photo.png';Image.new('RGB',(40,30),'gray').save(photo)
    render=renders/'sbs-test.png';Image.new('RGB',(40,30),'gray').save(render)
    ref={'camera':'sbs-test','pose_confidence':'B','photo':'photo.png','horizon_y_fraction':0.5,
         'pose_status':'WORKING_VALUE','width':40,'height':30,'author':'Example','license':'CC BY-SA 4.0',
         'captured_at':'2020','page_url':'https://www.mapillary.com/'}
    sbs.write(tmp_path/'sbs_cameras.json',{'cameras':[]})
    sbs.write(tmp_path/'sbs_references.json',{'references':[ref]})
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    sbs.write(tmp_path/'generated/world_manifest.json',{'world':'fixture'})
    material=tmp_path/'art-source/world/materials/materials_spec.json'
    sbs.write(material,{'materials':'fixture'})
    sbs.write(renders/'capture-test.json',{'status':'OK','cameras':['sbs-test'],
        'git_sha':'a'*40,'main_sha':'b'*40,'tier':'Low','lighting':'overcast','width':40,'height':30,
        'world_manifest_sha256':digest(tmp_path/'generated/world_manifest.json'),'materials_spec_sha256':digest(material),
        'cameras_sha256':digest(tmp_path/'sbs_cameras.json'),
        'references_sha256':digest(tmp_path/'sbs_references.json'),
        'render_sha256':{'sbs-test':digest(render)}})
    sbs.compose(renders,tmp_path/'out')
    assert sbs.read(tmp_path/'out/metrics.json')['provenance_status']=='RECORDED'
    Image.new('RGB',(40,30),'white').save(render)
    with pytest.raises(ValueError,match='render hash/provenance mismatch'):
        sbs.compose(renders,tmp_path/'out')


def test_early_route_commons_candidates_keep_licenses_and_uncertainty():
    refs=sbs.read(sbs.REGION/'sbs_references.json')['references']
    extras=[r for r in refs if r['source_id'] in ('cm109685822','cm92458760')]
    assert len(extras)==2
    assert {r['license'] for r in extras}=={'CC0','CC BY 3.0'}
    for r in extras:
        assert 0<r['segment_station_m']<300 and r['route_distance_m']<15
        assert r['pose_confidence']=='C' and not r['photometric_use']
        assert len(r['source_manifest_sha256'])==64
        assert 'no EXIF' in r['assumptions']


@pytest.mark.parametrize('value',[None,'','D','a',False])
def test_compose_rejects_unknown_confidence_even_in_diagnostics(tmp_path,monkeypatch,value):
    monkeypatch.setattr(sbs,'REGION',tmp_path)
    sbs.write(tmp_path/'sbs_references.json',{'references':[{'camera':'invalid','pose_confidence':value}]})
    with pytest.raises(ValueError,match='invalid pose_confidence'):
        sbs.compose(tmp_path/'renders',tmp_path/'out',historical=True)


@pytest.mark.parametrize('override',[{'typo':1},{'eye_height_m':0},{'horizon_y_fraction':1.01},
                                     {'eye_height_m':float('nan')},{'photometric_use':'false'}])
def test_both_source_types_validate_authored_corrections(override):
    for commons in (False,True):
        with pytest.raises(ValueError):sbs.validate_override('test',override,commons=commons)


def test_commons_rejects_unsupported_rectification_and_sfm_options():
    for override in ({'rectified_horizon_y_fraction':0.5},{'heading_source':'original'}):
        with pytest.raises(ValueError,match='Commons'):
            sbs.validate_override('test',override,commons=True)


def test_legacy_composition_requires_explicit_historical_mode(tmp_path,monkeypatch):
    monkeypatch.setattr(sbs,'REGION',tmp_path)
    sbs.write(tmp_path/'sbs_references.json',{'references':[]})
    with pytest.raises(ValueError,match='historical'):
        sbs.compose(tmp_path/'renders',tmp_path/'out')


@pytest.mark.parametrize('changed',['tier','lighting','git_sha','world_manifest_sha256','materials_spec_sha256'])
def test_capture_groups_cannot_mix_epochs_or_render_states(tmp_path,monkeypatch,changed):
    import hashlib
    monkeypatch.setattr(sbs,'REGION',tmp_path);monkeypatch.setattr(sbs,'ROOT',tmp_path)
    sbs.write(tmp_path/'sbs_references.json',{'references':[]});sbs.write(tmp_path/'sbs_cameras.json',{'cameras':[]})
    world=tmp_path/'generated/world_manifest.json';material=tmp_path/'art-source/world/materials/materials_spec.json'
    sbs.write(world,{'world':1});sbs.write(material,{'materials':1})
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    capture={'status':'OK','cameras':[],'git_sha':'a'*40,'main_sha':'b'*40,'tier':'Low','lighting':'overcast','width':40,'height':30,
             'cameras_sha256':sha(tmp_path/'sbs_cameras.json'),'references_sha256':sha(tmp_path/'sbs_references.json'),
             'world_manifest_sha256':sha(world),'materials_spec_sha256':sha(material)}
    renders=tmp_path/'renders';renders.mkdir();sbs.write(renders/'capture-a.json',capture)
    capture[changed]='different';sbs.write(renders/'capture-b.json',capture)
    with pytest.raises(ValueError,match='mixed render captures'):
        sbs.compose(renders,tmp_path/'out')


def test_landmark_errors_use_exact_bound_pixels_and_render_resolution():
    ref={'camera':'test','comparison_sha256':'a'*64}
    annotation={'camera':'test','comparison_sha256':'a'*64,'render_sha256':'b'*64,'points':[
        {'id':'one','photo':[0.2,0.3],'render':[0.3,0.3]},
        {'id':'two','photo':[0.5,0.5],'render':[0.5,0.6]}]}
    result=sbs.landmark_report([annotation],ref,'b'*64,(100,100))
    assert result['status']=='MATCHED_HASHES' and result['rmse_render_px']==10
    stale=sbs.landmark_report([annotation],ref,'c'*64,(100,100))
    assert stale['status']=='STALE' and not stale['points'] and stale['rmse_render_px'] is None


@pytest.mark.parametrize('points',[
    [{'id':'same','photo':[0,0],'render':[0,0]},{'id':'same','photo':[0,0],'render':[0,0]}],
    [{'id':'bad','photo':[1.1,0],'render':[0,0]}]])
def test_landmark_annotations_reject_ambiguous_or_invalid_points(points):
    ref={'camera':'test','comparison_sha256':'a'*64}
    annotation={'camera':'test','comparison_sha256':'a'*64,'render_sha256':'b'*64,'points':points}
    with pytest.raises(ValueError):sbs.landmark_report([annotation],ref,'b'*64,(100,100))


def test_one_vanishing_point_cannot_claim_enough_pose_anchors():
    ref={'camera':'test','comparison_sha256':'a'*64}
    annotation={'camera':'test','comparison_sha256':'a'*64,'render_sha256':'b'*64,'points':[
        {'id':'VP','photo':[0.5,0.5],'render':[0.5,0.5]}]}
    assert sbs.landmark_report([annotation],ref,'b'*64,(100,100))['status']=='INSUFFICIENT_ANCHORS'


@pytest.mark.parametrize('photo_hash',[None,'','invalid'])
def test_missing_or_invalid_photo_hash_never_binds_landmarks(photo_hash):
    ref={'camera':'test','comparison_sha256':photo_hash}
    annotation={'camera':'test','comparison_sha256':photo_hash,'render_sha256':'b'*64,'points':[
        {'id':'VP','photo':[0.5,0.5],'render':[0.5,0.5]}]}
    result=sbs.landmark_report([annotation],ref,'b'*64,(100,100))
    assert result['status']=='UNBOUND_IMAGES' and not result['points'] and result['rmse_render_px'] is None
