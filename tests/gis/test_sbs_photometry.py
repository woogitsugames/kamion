"""SBS metric semantics: contrast, exclusions and exact pixel-bound sample eligibility."""
from pathlib import Path
import sys
import numpy as np
import pytest
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/refs'))
import sbs_photometry as photometry


def annotation():
    top=[[0,0],[1,0],[1,0.3],[0,0.3]]
    bottom=[[0,0.7],[1,0.7],[1,1],[0,1]]
    return {'camera':'sbs-test','comparison_sha256':'a'*64,'render_sha256':'b'*64,'reference_lighting':'clear',
            'reviewed':True,'review_note':'Manual image check, diagnostic samples only.',
            'masks':{side:{'sky':[top],'asphalt':[bottom]} for side in ('photo','render')}}


def test_uniform_frame_has_no_contrast_or_gradient():
    result=photometry.image_measurements(Image.new('RGB',(100,100),(128,128,128)),0.5)
    assert result['luma_mean_srgb']==128 and result['rms_contrast_srgb']==0
    assert result['robust_michelson_srgb']==0 and result['mean_gradient_srgb_640']==0
    assert sum(result['histogram_32'])==10000


def test_two_level_frame_has_measurable_contrast():
    pixels=np.zeros((100,100,3),dtype='uint8');pixels[:50]=255
    result=photometry.image_measurements(Image.fromarray(pixels),0.5)
    assert result['rms_contrast_srgb']==1 and result['robust_michelson_srgb']==1
    assert result['mean_gradient_srgb_640']>0


def test_vehicle_hood_exclusion_removes_histogram_and_gradient_bias():
    pixels=np.zeros((100,100,3),dtype='uint8');pixels[:60]=200
    exclude=[[0,0.6],[1,0.6],[1,1],[0,1]]
    result=photometry.image_measurements(Image.fromarray(pixels),0.5,{'exclude':[exclude]})
    assert result['luma_mean_srgb']==200 and result['rms_contrast_srgb']==0
    assert result['mean_gradient_srgb_640']==0
    assert 0.38<=result['excluded_fraction']<=0.42
    assert sum(result['histogram_32'])==result['analyzed_pixels']


def test_excluding_every_pixel_is_an_error():
    with pytest.raises(ValueError,match='every analysis pixel'):
        photometry.image_measurements(Image.new('RGB',(10,10),'white'),0.5,{'exclude':[[[0,0],[1,0],[1,1],[0,1]]]})


def test_large_input_uses_declared_common_analysis_resolution():
    result=photometry.image_measurements(Image.new('RGB',(2560,1440),(100,100,100)),0.5)
    assert result['analysis_size_px']==[1280,720] and result['gradient_width_px']==640
    assert result['definition']==photometry.DEFINITION


def test_reviewed_matching_samples_are_diagnostics_not_pose_approval():
    ref={'camera':'sbs-test','comparison_sha256':'a'*64,'pose_confidence':'B','photometric_use':False}
    result=photometry.paired_photometry([annotation()],ref,'b'*64,'clear')
    assert result['status']=='REVIEWED_SAMPLES' and result['use']
    assert len(result['mask_signature'])==64
    assert ref['pose_confidence']=='B' and ref['photometric_use'] is False


@pytest.mark.parametrize('condition,expected',[('pose','EXCLUDED_POSE'),('lighting','LIGHTING_MISMATCH'),('review','UNREVIEWED'),('note','MISSING_REVIEW_NOTE'),('pixels','STALE')])
def test_ineligible_samples_do_not_enter_photometric_trends(condition,expected):
    ref={'camera':'sbs-test','comparison_sha256':'a'*64,'pose_confidence':'B'};record=annotation();lighting='clear';render='b'*64
    if condition=='pose':ref['pose_confidence']='C'
    if condition=='lighting':lighting='overcast'
    if condition=='review':record['reviewed']=False
    if condition=='note':record['review_note']=''
    if condition=='pixels':render='c'*64
    result=photometry.paired_photometry([record],ref,render,lighting)
    assert result['status']==expected and not result['use']


def test_duplicate_samples_are_rejected():
    ref={'camera':'sbs-test','comparison_sha256':'a'*64,'pose_confidence':'B'}
    with pytest.raises(ValueError,match='duplicate'):
        photometry.paired_photometry([annotation(),annotation()],ref,'b'*64,'clear')


def test_camera_fingerprint_tracks_geometry_not_labels():
    camera={'pos':[1,2,3],'look_at':[4,5,6],'fov_deg':60,'type':'persp','seat':'file','pose_confidence':'C'}
    before=photometry.camera_signature(camera)
    camera['pose_confidence']='B';assert photometry.camera_signature(camera)==before
    camera['pos']=[2,2,3];assert photometry.camera_signature(camera)!=before
