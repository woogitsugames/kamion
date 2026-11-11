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
        assert r['author'] and r['license']=='CC BY-SA 4.0'
        assert len(r['sha256'])==64


def test_compose_rejects_missing_and_wrong_aspect(tmp_path,monkeypatch):
    region=tmp_path/'region'; region.mkdir(); renders=tmp_path/'renders'; renders.mkdir()
    Image.new('RGB',(40,30),'gray').save(tmp_path/'photo.png')
    ref={'camera':'sbs-test','photo':'photo.png','horizon_y_fraction':0.5,'pose_status':'WORKING_VALUE',
         'width':40,'height':30,'author':'Example','license':'CC BY-SA 4.0','captured_at':'2020','page_url':'https://www.mapillary.com/'}
    sbs.write(region/'sbs_references.json',{'references':[ref]})
    monkeypatch.setattr(sbs,'ROOT',tmp_path);monkeypatch.setattr(sbs,'REGION',region)
    with pytest.raises(SystemExit): sbs.compose(renders,tmp_path/'out')
    Image.new('RGB',(40,20),'gray').save(renders/'sbs-test.png')
    with pytest.raises(ValueError,match='aspect mismatch'): sbs.compose(renders,tmp_path/'out')
    Image.new('RGB',(40,30),'gray').save(renders/'sbs-test.png')
    sbs.compose(renders,tmp_path/'out')
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
