"""SBS image measurements and hash-bound manual sample annotations (not a D51 gate)."""
from __future__ import annotations
import hashlib
import json
import math
import numpy as np
from PIL import Image, ImageDraw

DEFINITION = 'srgb-luma-v2-width1280-gradient640'


def digest_json(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')).hexdigest()


def valid_sha(value):
    return isinstance(value,str) and len(value)==64 and all(c in '0123456789abcdef' for c in value.lower())


def polygon_mask(polygons,size):
    mask=Image.new('1',size)
    draw=ImageDraw.Draw(mask)
    for polygon in polygons:
        if len(polygon)<3 or any(len(p)!=2 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<=1 for v in p) for p in polygon):
            raise ValueError('mask polygons require >=3 normalized finite points')
        draw.polygon([(x*(size[0]-1),y*(size[1]-1)) for x,y in polygon],fill=1)
    return np.asarray(mask,dtype=bool)


def roi_stats(luma,mask):
    values=luma[mask]
    if not values.size:return {'pixels':0,'mean':None,'std':None,'p10':None,'p90':None,'rms_contrast':None}
    mean=float(values.mean());std=float(values.std())
    return {'pixels':int(values.size),'mean':round(mean,3),'std':round(std,3),
            'p10':round(float(np.percentile(values,10)),3),'p90':round(float(np.percentile(values,90)),3),
            'rms_contrast':round(std/mean,6) if mean else None}


def image_measurements(im,horizon,authored_masks=None):
    source_size=im.size
    im=im.convert('RGB')
    if im.width>1280:im=im.resize((1280,round(im.height*1280/im.width)),Image.Resampling.LANCZOS)
    a=np.asarray(im,dtype=float);luma=a@np.array([0.2126,0.7152,0.0722]);yy,xx=np.indices(luma.shape)
    sky=(yy<luma.shape[0]*horizon)&(luma>115)&(a[:,:,2]>=a[:,:,0]*0.95)
    asphalt=(yy>luma.shape[0]*max(horizon,0.55))&(xx>luma.shape[1]*0.2)&(xx<luma.shape[1]*0.8)&(np.ptp(a,axis=2)<35)&(luma>25)&(luma<180)
    method='WORKING_VALUE RGB/position heuristic, not semantic ground truth'
    excluded=np.zeros(luma.shape,dtype=bool)
    if authored_masks is not None:
        unknown=set(authored_masks)-{'sky','asphalt','exclude'}
        if unknown:raise ValueError(f'unknown mask labels: {sorted(unknown)}')
        excluded=polygon_mask(authored_masks.get('exclude',[]),im.size)
        if 'sky' in authored_masks or 'asphalt' in authored_masks:
            sky=polygon_mask(authored_masks.get('sky',[]),im.size)
            asphalt=polygon_mask(authored_masks.get('asphalt',[]),im.size)
            if np.any(sky&asphalt):raise ValueError('sky/asphalt masks overlap')
            method='authored normalized polygons; manual samples, not semantic ground truth'
        elif excluded.any():method+='; authored exclusions'
    valid=~excluded
    if not valid.any():raise ValueError('mask excludes every analysis pixel')
    sky=sky&valid;asphalt=asphalt&valid
    hist=np.histogram(luma[valid],bins=32,range=(0,256))[0]
    whole=roi_stats(luma,valid);sky_stats=roi_stats(luma,sky);asphalt_stats=roi_stats(luma,asphalt)
    low,high=[float(v) for v in np.percentile(luma[valid],[5,95])]
    gw=min(640,im.width);gh=max(1,round(im.height*gw/im.width))
    probe=np.asarray(im.resize((gw,gh),Image.Resampling.LANCZOS),dtype=float)@np.array([0.2126,0.7152,0.0722])
    vmask=np.asarray(Image.fromarray(valid).resize((gw,gh),Image.Resampling.NEAREST),dtype=bool)
    gradient_sum=0.0;gradient_count=0
    for axis in (0,1):
        if probe.shape[axis]<2:continue
        deltas=np.abs(np.diff(probe,axis=axis))
        pairs=(vmask[:-1,:]&vmask[1:,:]) if axis==0 else (vmask[:,:-1]&vmask[:,1:])
        gradient_sum+=float(deltas[pairs].sum());gradient_count+=int(pairs.sum())
    sky_luma=sky_stats['mean'];asphalt_luma=asphalt_stats['mean']
    return {'definition':DEFINITION,'source_size_px':list(source_size),'analysis_size_px':list(im.size),
        'analyzed_pixels':whole['pixels'],'excluded_fraction':round(float(excluded.mean()),6),
        'luma_mean_srgb':whole['mean'],'luma_std_srgb':whole['std'],'luma_p05_srgb':round(low,3),'luma_p95_srgb':round(high,3),
        'rms_contrast_srgb':whole['rms_contrast'],'robust_michelson_srgb':round((high-low)/(high+low),6) if high+low else None,
        'mean_gradient_srgb_640':round(gradient_sum/gradient_count,6) if gradient_count else 0.0,'gradient_width_px':gw,
        'histogram_32':hist.tolist(),'sky_fraction_estimate':round(float(sky.mean()),5),
        'asphalt_fraction_estimate':round(float(asphalt.mean()),5),
        'sky_asphalt_ratio_estimate':round(float(sky.sum()/asphalt.sum()),5) if asphalt.any() else None,
        'sky_asphalt_area_ratio_estimate':round(float(sky.sum()/asphalt.sum()),5) if asphalt.any() else None,
        'sky_luma_mean_srgb_estimate':sky_luma,'asphalt_luma_mean_srgb_estimate':asphalt_luma,
        'sky_asphalt_luma_ratio_estimate':round(sky_luma/asphalt_luma,5) if sky_luma is not None and asphalt_luma else None,
        'sky_samples':sky_stats,'asphalt_samples':asphalt_stats,'mask_method':method}


def paired_photometry(annotations,ref,render_sha,lighting):
    candidates=[a for a in annotations if a.get('camera')==ref['camera']]
    result={'status':'STALE' if candidates else 'UNANNOTATED','use':False,'masks':None,'mask_signature':None}
    photo_sha=ref.get('comparison_sha256')
    if not valid_sha(photo_sha) or not valid_sha(render_sha):return {**result,'status':'UNBOUND_IMAGES'}
    matching=[a for a in candidates if a.get('comparison_sha256')==photo_sha and a.get('render_sha256')==render_sha]
    if not matching:return result
    if len(matching)!=1:raise ValueError('duplicate photometry annotation for the same image pair')
    record=matching[0];masks=record.get('masks')
    if not isinstance(masks,dict) or set(masks)!={'photo','render'}:raise ValueError('photometry needs photo/render masks')
    for panel in ('photo','render'):
        if not {'sky','asphalt'}<=set(masks[panel]):raise ValueError('photometry needs both sky and asphalt samples')
        for polygons in masks[panel].values():polygon_mask(polygons,(32,32))
    result.update(masks=masks,mask_signature=digest_json(masks),review_note=record.get('review_note',''))
    if ref.get('pose_confidence') not in ('A','B'):return {**result,'status':'EXCLUDED_POSE'}
    if record.get('reviewed') is not True:return {**result,'status':'UNREVIEWED'}
    if not record.get('review_note'):return {**result,'status':'MISSING_REVIEW_NOTE'}
    if lighting not in ('clear','overcast','lowsun','dusk') or record.get('reference_lighting')!=lighting:
        return {**result,'status':'LIGHTING_MISMATCH'}
    return {**result,'status':'REVIEWED_SAMPLES','use':True}


def camera_signature(camera):
    if camera is None:return None
    return digest_json({key:camera.get(key) for key in ('pos','look_at','fov_deg','type','seat')})
