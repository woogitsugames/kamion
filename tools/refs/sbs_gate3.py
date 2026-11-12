"""ADR 0103: offline, reproducible photo-pose cameras and reference | render sheets.

Prepare/compose are offline; fetch-intrinsics explicitly requests public metadata.
No world writes. Coordinates: local E,N,absolute U (not Unity XYZ).
Eye/pitch remain WORKING_VALUE until calibrated in authored_overrides.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageOps
from pyproj import Geod, Transformer
from shapely.geometry import LineString, Point

ROOT = Path(__file__).resolve().parents[2]
REGION = ROOT / 'Data/Regions/bialystok-industrial-c'
OUTPUT = ROOT / 'artifacts/sbs-gate3'
sys.path.insert(0,str(Path(__file__).resolve().parent))
from sbs_photometry import DEFINITION, image_measurements, paired_photometry, camera_signature


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary=path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def save_png(im,path):
    temporary=path.with_name(path.name+'.tmp')
    im.save(temporary,format='PNG')
    temporary.replace(path)


OVERRIDE_FIELDS = {'east_delta_m','north_delta_m','eye_height_m','absolute_u_m','heading_delta_deg',
    'horizontal_fov_deg','horizon_y_fraction','rectified_horizon_y_fraction','heading_source','pose_status',
    'note','masks','pose_confidence','pose_reason','photometric_use','photometric_reason','vanishing_lines','horizon_method'}


def validate_override(camera_id, ov, *, commons=False):
    unknown=set(ov)-OVERRIDE_FIELDS
    if unknown: raise ValueError(f'unknown authored corrections for {camera_id}: {sorted(unknown)}')
    if ov.get('pose_confidence','C') not in ('A','B','C'):
        raise ValueError(f'invalid pose_confidence: {camera_id}')
    if commons and set(ov)&{'rectified_horizon_y_fraction','heading_source'}:
        raise ValueError('Commons has no rectified horizon or SfM heading source')
    for key in ('east_delta_m','north_delta_m','absolute_u_m','heading_delta_deg','eye_height_m','horizontal_fov_deg',
                'horizon_y_fraction','rectified_horizon_y_fraction'):
        if key in ov and (isinstance(ov[key],bool) or not isinstance(ov[key],(int,float)) or not math.isfinite(ov[key])):
            raise ValueError(f'invalid finite number for {key}: {camera_id}')
    if ov.get('eye_height_m',1.7 if commons else 2.2)<=0:
        raise ValueError(f'invalid eye height: {camera_id}')
    for key in ('horizon_y_fraction','rectified_horizon_y_fraction'):
        if key in ov and not 0<ov[key]<1: raise ValueError(f'invalid horizon: {camera_id}')
    if 'photometric_use' in ov and not isinstance(ov['photometric_use'],bool):
        raise ValueError('photometric_use must be boolean')


def vfov(horizontal, aspect):
    if not (1 < horizontal < 179 and aspect > 0):
        raise ValueError('invalid FOV/aspect')
    return math.degrees(2 * math.atan(math.tan(math.radians(horizontal) / 2) / aspect))


def grid_heading(lon, lat, azimuth, transform):
    """Mapillary true-north compass -> EPSG:2180 grid north (meridian convergence matters)."""
    lon2, lat2, _ = Geod(ellps='WGS84').fwd(lon, lat, azimuth, 20)
    x,y = transform.transform(lon,lat)
    x2,y2 = transform.transform(lon2,lat2)
    return math.degrees(math.atan2(x2-x,y2-y)) % 360


def pose(e, n, u, heading, pitch):
    h, p = math.radians(heading), math.radians(pitch)
    return [round(e + 40 * math.sin(h) * math.cos(p), 4),
            round(n + 40 * math.cos(h) * math.cos(p), 4), round(u + 40 * math.sin(p), 4)]


def ground_sampler():
    meta = read(REGION / 'terrain.json')
    values = np.fromfile(ROOT / meta['encoding']['file'], dtype='<u2').reshape(meta['samples'][::-1])
    def sample(x, y):
        i = (x - meta['bbox'][0]) / meta['spacing_m']
        j = (meta['bbox'][3] - y) / meta['spacing_m']
        if not (0 <= i < values.shape[1] - 1 and 0 <= j < values.shape[0] - 1):
            raise ValueError('camera outside NMT coverage')
        a, b = int(i), int(j)
        fx, fy = i - a, j - b
        raw = ((1-fx)*(1-fy)*float(values[b,a]) + fx*(1-fy)*float(values[b,a+1])
               + (1-fx)*fy*float(values[b+1,a]) + fx*fy*float(values[b+1,a+1]))
        return meta['encoding']['offset_m'] + raw * meta['encoding']['scale_m_per_unit']
    return sample


def fetch_intrinsics():
    """Explicit opt-in network step, token only in existing client's Authorization header."""
    from mapillary_fetch import MapillaryClient, resolve_token
    token=resolve_token()
    if not token: raise SystemExit('Mapillary metadata unavailable: no configured token')
    client=MapillaryClient(token,retries=1)
    path=REGION/'sbs_intrinsics.json'
    records=read(path).get('images',{}) if path.exists() else {}
    fields='id,camera_parameters,camera_type,computed_compass_angle,exif_orientation,width,height,geometry,computed_geometry,altitude,computed_altitude'
    for ref in read(REGION/'sbs_references.json')['references']:
        sid=ref['source_id']
        if not sid.isdecimal(): continue  # Commons references have no Mapillary intrinsics.
        if sid in records and 'geometry' in records[sid]: continue
        body=client._get('https://graph.mapillary.com/'+sid,params={'fields':fields}).json()
        records[sid]={k:body[k] for k in fields.split(',') if k in body}
        write(path,{'schema':'kamion/sbs-intrinsics/1','images':records})
    print(f'Cached intrinsics for {len(records)} images; no image downloads or credentials saved.')


def projection_grid(width,height,focal,camera_type,parameters):
    """Pinhole output rays -> Mapillary normalized source coordinates (max dimension units).

    Formula contract: MapillaryJS geometry/camera/{Perspective,Fisheye}Camera.ts and geo/Transform.ts.
    This is a photographic rectification operation, not generated/repainted image content.
    """
    yy,xx=np.indices((height,width),dtype=float)
    scale=max(width,height)
    x=(xx-(width-1)/2)/(scale*focal)
    y=(yy-(height-1)/2)/(scale*focal)
    r2=x*x+y*y
    if camera_type=='fisheye':
        radius=np.sqrt(r2)
        theta=np.arctan(radius)
        factor=np.divide(theta,radius,out=np.ones_like(theta),where=radius>1e-12)
        x,y=x*factor,y*factor
        r2=theta*theta
    source_f,k1,k2=parameters
    d=1+k1*r2+k2*r2*r2
    return source_f*x*d,source_f*y*d


def rectify(photo,metadata,destination):
    # Mapillary thumbnails are already upright. A 180-degree rotation leaves the centered radial model invariant.
    if metadata.get('exif_orientation',1) not in (1,3) or metadata.get('camera_type') not in ('perspective','fisheye'):
        raise ValueError('unsupported camera projection/orientation; cannot claim a pinhole match')
    params=metadata.get('camera_parameters',[])
    if len(params)!=3 or params[0]<=0: raise ValueError('invalid intrinsics')
    with Image.open(photo) as im: source=np.asarray(im.convert('RGB'),dtype=float)
    sh,sw=source.shape[:2]
    width,height=1280,round(1280*sh/sw)
    # Crop to <=90-degree pinhole view and increase focal until every output ray has source pixels.
    focal=max(params[0],0.5)
    for _ in range(60):
        sx,sy=projection_grid(width,height,focal,metadata['camera_type'],params)
        px=sx*max(sw,sh)+(sw-1)/2; py=sy*max(sw,sh)+(sh-1)/2
        if px.min()>=0 and py.min()>=0 and px.max()<sw-1 and py.max()<sh-1: break
        focal*=1.03
    else: raise ValueError('unable to find valid rectified image bounds')
    x0=px.astype(int);y0=py.astype(int)
    fx=(px-x0)[...,None];fy=(py-y0)[...,None]
    out=(source[y0,x0]*(1-fx)*(1-fy)+source[y0,x0+1]*fx*(1-fy)
         +source[y0+1,x0]*(1-fx)*fy+source[y0+1,x0+1]*fx*fy)
    destination.parent.mkdir(parents=True,exist_ok=True)
    save_png(Image.fromarray(np.rint(out).clip(0,255).astype('uint8')),destination)
    return focal,width,height


def rectified_horizon(original_fraction,width,height,metadata,target_focal):
    """Unproject manually marked central horizon point, then project into rectified image."""
    f,k1,k2=metadata['camera_parameters']
    distorted=abs((original_fraction-0.5)*height/max(width,height)/f)
    radius=distorted
    for _ in range(30):
        value=radius*(1+k1*radius**2+k2*radius**4)-distorted
        derivative=1+3*k1*radius**2+5*k2*radius**4
        radius-=value/derivative
    if metadata['camera_type']=='fisheye': radius=math.tan(radius)
    signed=math.copysign(radius,original_fraction-0.5)
    return 0.5+signed*target_focal*max(width,height)/height


def vanishing_horizon(lines):
    """Intersect two authored road-edge lines in normalized rectified photo coordinates.

    This measures a road vanishing point, not a surveyed level horizon on a slope.
    """
    if len(lines) != 2:
        raise ValueError('two vanishing lines required')
    rays=[]
    for line in lines:
        if len(line)!=2 or any(len(p)!=2 or not all(0<=v<=1 for v in p) for p in line):
            raise ValueError('vanishing lines need two normalized points each')
        rays.append(np.cross([*line[0],1], [*line[1],1]))
    point=np.cross(*rays)
    if abs(point[2]) < 1e-9:
        raise ValueError('parallel vanishing lines')
    point=point[:2]/point[2]
    if not all(0<v<1 for v in point):
        raise ValueError('vanishing point outside photo')
    return [round(float(v),7) for v in point]


def prepare(count=20, radius=40):
    manifest = ROOT / 'Data/raw/mapillary/bialystok-industrial-c/manifest.jsonl'
    records = [json.loads(line) for line in manifest.read_text(encoding='utf-8').splitlines() if line.strip()]
    origin = yaml.safe_load((REGION / 'region.yaml').read_text(encoding='utf-8'))['origin']
    transform = Transformer.from_crs(4326, 2180, always_xy=True)
    terrain = ground_sampler()
    config_path = REGION / 'sbs_authored_overrides.json'
    config = read(config_path) if config_path.exists() else {'schema': 'kamion/sbs-overrides/1', 'authored_overrides': {}}
    overrides = config['authored_overrides']
    intrinsics_path=REGION/'sbs_intrinsics.json'
    intrinsics=read(intrinsics_path)['images'] if intrinsics_path.exists() else {}
    eligible = []
    for r in records:
        photo = manifest.parent / r['file']
        if not photo.is_file():
            continue
        with Image.open(photo) as im:
            a = np.asarray(im.convert('RGB').resize((64,48)))
        # Daylight gate: avoid comparing night/dusk dashcam exposures with clear/overcast renders.
        if float(np.median(a[:24])) > 65:
            eligible.append(r)
    cameras, refs, used = [], [], set()
    for segment in read(REGION / 'gate3_segment.json')['segments']:
        line = LineString(segment['points_en'])
        candidates = []
        for r in eligible:
            if r.get('is_pano') or r.get('compass_angle') is None or not r.get('author'):
                continue
            if r.get('license') != 'CC BY-SA 4.0':
                continue
            photo = manifest.parent / r['file']
            if not photo.is_file():
                continue
            x, y = transform.transform(r['lon'], r['lat'])
            point = Point(x-origin['x'], y-origin['y'])
            distance = line.distance(point)
            if distance <= radius:
                candidates.append((r, x, y, line.project(point), distance))
        # Farthest-point sampling along each segment, stable tie-break by image id.
        selected = []
        while len(selected) < count:
            remaining = [c for c in candidates if c[0]['id'] not in used]
            if not remaining:
                raise ValueError(f"{segment['id']}: fewer than {count} unique eligible photos")
            def score(c):
                spread = min(abs(c[3]-s[3]) for s in selected) if selected else -c[3]
                return (-spread, c[4], c[0]['id'])
            chosen = min(remaining, key=score)
            selected.append(chosen)
            used.add(chosen[0]['id'])
        for r, x, y, station, distance in sorted(selected, key=lambda c: (c[3], c[0]['id'])):
            camera_id = 'sbs-' + segment['id'].lower() + '-' + r['id']
            photo = manifest.parent / r['file']
            digest = hashlib.sha256(photo.read_bytes()).hexdigest()
            if digest != r['sha256']:
                raise ValueError(f"photo hash mismatch: {r['id']}")
            with Image.open(photo) as im:
                width, height = im.size
            lens=intrinsics.get(r['id'])
            comparison=photo
            focal=None
            if lens:
                comparison=OUTPUT/'rectified'/(r['id']+'.png')
                cache_path=comparison.with_suffix('.cache.json')
                fingerprint=hashlib.sha256(json.dumps({'source':digest,'lens':lens,'algorithm':1},sort_keys=True).encode()).hexdigest()
                cache=read(cache_path) if cache_path.exists() else {}
                if (cache.get('fingerprint')==fingerprint and comparison.exists()
                        and cache.get('sha256')==hashlib.sha256(comparison.read_bytes()).hexdigest()):
                    focal=cache['focal']
                else:
                    focal,_,_=rectify(photo,lens,comparison)
                    write(cache_path,{'fingerprint':fingerprint,'focal':focal,'sha256':hashlib.sha256(comparison.read_bytes()).hexdigest()})
            ov = overrides.get(camera_id, {})
            validate_override(camera_id,ov)
            confidence = ov.get('pose_confidence', 'C')
            if confidence not in ('A','B','C'):
                raise ValueError(f'invalid pose_confidence: {camera_id}')
            e = x-origin['x'] + ov.get('east_delta_m', 0)
            n = y-origin['y'] + ov.get('north_delta_m', 0)
            eye = ov.get('eye_height_m', 2.2)
            u = ov.get('absolute_u_m', terrain(e+origin['x'], n+origin['y']) + eye)
            true_heading=lens.get('computed_compass_angle',r['compass_angle']) if lens else r['compass_angle']
            if ov.get('heading_source')=='original': true_heading=r['compass_angle']
            elif ov.get('heading_source','computed')!='computed': raise ValueError('heading_source must be original or computed')
            heading = (grid_heading(r['lon'], r['lat'], true_heading, transform) + ov.get('heading_delta_deg', 0)) % 360
            native_hfov=math.degrees(2*math.atan(width/max(width,height)/(2*focal))) if focal else 90
            if lens and 'horizontal_fov_deg' in ov:
                raise ValueError('change rectification focal policy instead of overriding render-only FOV')
            fov = vfov(ov.get('horizontal_fov_deg', native_hfov), width/height)
            horizon = ov.get('horizon_y_fraction', 0.5)
            if lens: horizon=rectified_horizon(horizon,width,height,lens,focal)
            horizon=ov.get('rectified_horizon_y_fraction',horizon)
            if 'vanishing_lines' in ov:
                horizon=vanishing_horizon(ov['vanishing_lines'])[1]
            if not (0 < horizon < 1 and eye > 0):
                raise ValueError(f'invalid authored horizon/eye: {camera_id}')
            pitch = math.degrees(math.atan((2*horizon-1)*math.tan(math.radians(fov)/2)))
            cameras.append({'id': camera_id, 'kind': 'photo_match', 'seat': 'file', 'type': 'persp',
                            'pos': [round(e,4),round(n,4),round(u,4)], 'look_at': pose(e,n,u,heading,pitch),
                            'fov_deg': round(fov,5), 'segment': segment['id'],
                            'pose_confidence': confidence, 'pose_reason': ov.get('pose_reason','Unreviewed pose'),
                            'note': 'ADR0103 photo GPS/heading; NMT+eye/FOV/pitch WORKING_VALUE; see sbs_references.json'})
            refs.append({'camera': camera_id, 'segment': segment['id'], 'photo': photo.relative_to(ROOT).as_posix(),
                         'source_id': r['id'], 'page_url': r['page_url'], 'author': r['author'],
                         'license': r['license'], 'license_url': r['license_url'], 'captured_at': r['captured_at'],
                         'sha256': digest, 'width': width, 'height': height, 'lon': r['lon'], 'lat': r['lat'],
                         'comparison_photo':comparison.relative_to(ROOT).as_posix(),
                         'comparison_sha256':hashlib.sha256(comparison.read_bytes()).hexdigest(),
                         'projection':lens, 'rectified_focal':focal,
                         'heading_grid_deg': heading, 'heading_true_deg': true_heading, 'route_distance_m': round(distance,3),
                         'heading_original_deg':r['compass_angle'],
                         'segment_station_m': round(station,3), 'horizon_y_fraction': horizon,
                         'pose_status': ov.get('pose_status','WORKING_VALUE'),
                         'pose_confidence': confidence, 'pose_reason': ov.get('pose_reason','Unreviewed pose'),
                         'photometric_use': ov.get('photometric_use', False),
                         'photometric_reason': ov.get('photometric_reason','Photometry not reviewed'),
                         'photo_vs_data_age': 'pre-2020: historical reference; data epoch UNVERIFIED' if int(str(r['captured_at'])[:4]) < 2020 else 'data epoch UNVERIFIED',
                         'assumptions': ('NMT/eye/manual horizon WORKING_VALUE; FOV and radial rectification from Mapillary SfM intrinsics. Roll/GPS/SfM accuracy unverified.' if lens else 'NMT bare earth; eye/FOV/pitch WORKING_VALUE. Zero roll; lens distortion not corrected. GPS/compass accuracy unknown.'),
                         'authored_overrides': ov})
    extra_path=REGION/'sbs_extra_references.json'
    for extra in read(extra_path).get('references',[]) if extra_path.exists() else []:
        source_manifest=ROOT/extra['metadata_manifest']
        record=next(r for r in [json.loads(line) for line in source_manifest.read_text(encoding='utf-8-sig').splitlines() if line.strip()] if r['id']==extra['source_id'])
        photo=source_manifest.parent/record['file'];digest=hashlib.sha256(photo.read_bytes()).hexdigest()
        if digest!=record['sha256']: raise ValueError('extra photo hash mismatch')
        if record['license'] not in ('CC0','CC BY 3.0','CC BY 4.0','CC BY-SA 3.0','CC BY-SA 4.0'):
            raise ValueError('unsupported extra reference license')
        camera_id=extra['camera'];ov=overrides.get(camera_id,{})
        validate_override(camera_id,ov,commons=True)
        confidence=ov.get('pose_confidence','C')
        if confidence not in ('A','B','C'): raise ValueError('invalid extra pose confidence')
        x,y=transform.transform(record['lon'],record['lat'])
        e=x-origin['x']+ov.get('east_delta_m',0);n=y-origin['y']+ov.get('north_delta_m',0)
        eye=ov.get('eye_height_m',1.7);u=ov.get('absolute_u_m',terrain(e+origin['x'],n+origin['y'])+eye)
        heading=grid_heading(record['lon'],record['lat'],extra['heading_true_deg'],transform)+ov.get('heading_delta_deg',0)
        with Image.open(photo) as im: width,height=im.size
        fov=vfov(ov.get('horizontal_fov_deg',extra['horizontal_fov_deg']),width/height)
        horizon=ov.get('horizon_y_fraction',extra['horizon_y_fraction'])
        if 'vanishing_lines' in ov: horizon=vanishing_horizon(ov['vanishing_lines'])[1]
        if not (math.isfinite(horizon) and 0<horizon<1 and eye>0): raise ValueError('invalid Commons horizon/eye')
        pitch=math.degrees(math.atan((2*horizon-1)*math.tan(math.radians(fov)/2)))
        segment=next(seg for seg in read(REGION/'gate3_segment.json')['segments'] if seg['id']==extra['segment'])
        line=LineString(segment['points_en']);point=Point(e,n)
        common={'pose_confidence':confidence,'pose_reason':ov.get('pose_reason','Unreviewed Commons pose')}
        cameras.append({'id':camera_id,'kind':'photo_match','seat':'file','type':'persp','pos':[round(e,4),round(n,4),round(u,4)],
                        'look_at':pose(e,n,u,heading,pitch),'fov_deg':round(fov,5),'segment':segment['id'],**common,
                        'note':'ADR0111 Commons GPS; manually inferred heading/FOV/eye/horizon WORKING_VALUE'})
        refs.append({'camera':camera_id,'segment':segment['id'],'photo':photo.relative_to(ROOT).as_posix(),
            'source_id':record['id'],'page_url':record['page_url'],'author':record['author'],'license':record['license'],
            'license_url':record['license_url'],'captured_at':record['captured_at'],'sha256':digest,'comparison_photo':photo.relative_to(ROOT).as_posix(),
            'comparison_sha256':digest,'width':width,'height':height,'lon':record['lon'],'lat':record['lat'],
            'heading_grid_deg':heading,'heading_true_deg':extra['heading_true_deg'],'route_distance_m':round(line.distance(point),3),
            'segment_station_m':round(line.project(point),3),'horizon_y_fraction':horizon,'pose_status':'WORKING_VALUE',**common,
            'photometric_use':ov.get('photometric_use',False),'photometric_reason':ov.get('photometric_reason','Unvalidated masks'),
            'photo_vs_data_age':'data epoch UNVERIFIED','authored_overrides':ov,
            'assumptions':'Public cached Commons metadata, thumbnail has no EXIF; no calibrated lens or roll. Heading/FOV/eye/horizon WORKING_VALUE.',
            'source_manifest_sha256':hashlib.sha256(source_manifest.read_bytes()).hexdigest()})
    write(REGION / 'sbs_cameras.json', {'schema': 'kamion/sbs-cameras/1', 'frame': 'E,N,absolute U', 'cameras': cameras})
    input_hashes={name:hashlib.sha256((REGION/name).read_bytes()).hexdigest()
                  for name in ('region.yaml','terrain.json','gate3_segment.json')}
    write(REGION / 'sbs_references.json', {'schema': 'kamion/sbs-references/1', 'input_sha256':input_hashes,
          'source_manifest_sha256': hashlib.sha256(manifest.read_bytes()).hexdigest(), 'references': refs})
    write(config_path, config)
    lines = ['# ADR 0103 — per-photo attribution (reference sheets only)', '',
             'Photos stay outside git and builds. Source pixels on sheets are rectified/cropped, resized and overlaid.',
             'Photo panels and their modifications: per-photo license below; render panels retain project terms.',
             'Licenses are linked per photo; derivative photo panels follow their source licenses.', '',
             '| Camera | Author | Date | License | Source | SHA256 |', '|---|---|---|---|---|---|']
    for r in refs:
        lines.append(f"| {r['camera']} | {r['author']} | {r['captured_at']} | [{r['license']}]({r['license_url']}) | [{r['source_id']}]({r['page_url']}) | `{r['sha256']}` |")
    (ROOT/'docs/refs/sbs-gate3-attribution.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    OUTPUT.mkdir(parents=True, exist_ok=True)
    coverage=[]
    for segment in read(REGION/'gate3_segment.json')['segments']:
        selected=[r for r in refs if r['segment']==segment['id']]
        coverage.append({'segment':segment['id'],'photos':len(selected),
                         'station_min_m':min(r['segment_station_m'] for r in selected),
                         'station_max_m':max(r['segment_station_m'] for r in selected),
                         'segment_length_m':round(LineString(segment['points_en']).length,3),
                         'max_distance_to_route_m':max(r['route_distance_m'] for r in selected),
                         'authors':sorted({r['author'] for r in selected}),
                         'eligible_poses':sum(r.get('pose_confidence','C') in ('A','B') for r in selected),
                         'verified_poses':sum(r['pose_status']=='VERIFIED' for r in selected)})
    write(OUTPUT/'coverage.json',{'segments':coverage,'note':'Station range is not continuous photo coverage.'})
    contact(refs)
    print(f'Prepared {len(cameras)} distinct photo cameras; pose calibration still required.')


def contact(refs):
    for seg in sorted({r['segment'] for r in refs}):
        group = [r for r in refs if r['segment'] == seg]
        sheet = Image.new('RGB', (960, math.ceil(len(group)/4)*165), '#202020')
        d = ImageDraw.Draw(sheet)
        for i,r in enumerate(group):
            with Image.open(ROOT/r.get('comparison_photo',r['photo'])) as im:
                thumb = ImageOps.contain(im.convert('RGB'), (238,135))
            x,y=(i%4)*240,(i//4)*165
            sheet.paste(thumb,(x,y))
            d.text((x+2,y+136),r['source_id'],fill='white')
            d.text((x+2,y+149),f"s={r['segment_station_m']:.0f} d={r['route_distance_m']:.0f}m",fill='white')
        sheet.save(OUTPUT/f'contact-{seg}.jpg')


def measurements(im,horizon,authored_masks=None):
    return image_measurements(im,horizon,authored_masks)


def landmark_report(annotations, ref, render_digest, render_size):
    """Manual correspondences, bound to exact photo/render pixels; no automatic pose approval."""
    candidates=[a for a in annotations if a.get('camera')==ref['camera']]
    valid_sha=lambda value: isinstance(value,str) and len(value)==64 and all(c in '0123456789abcdef' for c in value.lower())
    if candidates and (not valid_sha(ref.get('comparison_sha256')) or not valid_sha(render_digest)):
        return {'status':'UNBOUND_IMAGES','points':[],'rmse_render_px':None}
    matching=[a for a in candidates if a.get('comparison_sha256')==ref.get('comparison_sha256')
              and a.get('render_sha256')==render_digest]
    if not matching:
        return {'status':'STALE' if candidates else 'UNANNOTATED','points':[],'rmse_render_px':None}
    if len(matching)!=1: raise ValueError('duplicate landmark annotation for the same image pair')
    points=matching[0].get('points',[])
    if not 1<=len(points)<=32: raise ValueError('landmarks require 1-32 points')
    rows=[];ids=set()
    for point in points:
        name=point.get('id')
        if not isinstance(name,str) or not name or name in ids: raise ValueError('landmark IDs must be unique nonempty strings')
        ids.add(name)
        for panel in ('photo','render'):
            xy=point.get(panel,[])
            if len(xy)!=2 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<=1 for v in xy):
                raise ValueError('landmark coordinates must be normalized finite pairs')
        dx=(point['render'][0]-point['photo'][0])*render_size[0]
        dy=(point['render'][1]-point['photo'][1])*render_size[1]
        rows.append({**point,'dx_render_px':round(dx,3),'dy_render_px':round(dy,3),'error_render_px':round(math.hypot(dx,dy),3)})
    return {'status':'MATCHED_HASHES' if len(rows)>=2 else 'INSUFFICIENT_ANCHORS','points':rows,
            'rmse_render_px':round(math.sqrt(sum(r['error_render_px']**2 for r in rows)/len(rows)),3),
            'method':'WORKING_VALUE manually marked correspondences; geometric identity and point placement require review'}


def compose(render_dir, outdir, strict=True, include_rejected=False, historical=False, inputs=None, landmarks_file=None, photometry_file=None):
    # A sealed snapshot changes where bytes are read, not the strength of capture checks.
    # Legacy provenance still requires the separate, explicit historical mode.
    input_dir=Path(inputs) if inputs is not None else REGION
    if inputs is not None and not historical:
        for name in ('sbs_cameras.json','sbs_references.json','world_manifest.json','materials_spec.json'):
            if not (input_dir/name).is_file():raise ValueError(f'incomplete input snapshot: {name}')
    refs=read(input_dir/'sbs_references.json')['references']
    cameras_by_id={c['id']:c for c in read(input_dir/'sbs_cameras.json').get('cameras',[])} if (input_dir/'sbs_cameras.json').exists() else {}
    photometry_path=Path(photometry_file) if photometry_file is not None else input_dir/'sbs_photometry.json'
    photometry_annotations=read(photometry_path).get('annotations',[]) if photometry_path.exists() else []
    photometry_hash=hashlib.sha256(photometry_path.read_bytes()).hexdigest() if photometry_path.exists() else None
    landmark_path=Path(landmarks_file) if landmarks_file is not None else input_dir/'sbs_landmarks.json'
    annotations=read(landmark_path).get('annotations',[]) if landmark_path.exists() else []
    landmark_hash=hashlib.sha256(landmark_path.read_bytes()).hexdigest() if landmark_path.exists() else None
    outdir.mkdir(parents=True,exist_ok=True)
    metrics=[]
    missing=[]
    rejected=[]
    captures=[read(path) for path in render_dir.glob('capture-*.json')]
    camera_hash=hashlib.sha256((input_dir/'sbs_cameras.json').read_bytes()).hexdigest() if (input_dir/'sbs_cameras.json').exists() else None
    reference_hash=hashlib.sha256((input_dir/'sbs_references.json').read_bytes()).hexdigest()
    for capture in captures:
        if capture.get('status')!='OK' or capture.get('cameras_sha256')!=camera_hash or capture.get('references_sha256')!=reference_hash:
            raise ValueError('incomplete or stale render capture; rerender after camera edits')
    warnings=[]
    if not captures and not historical: raise ValueError('capture metadata required; use --historical for legacy diagnostics')
    required=('git_sha','main_sha','world_manifest_sha256','materials_spec_sha256','tier','lighting','width','height')
    incomplete=[c for c in captures if any(not c.get(k) for k in required)]
    if incomplete and not historical: raise ValueError('incomplete capture provenance; rerender or use --historical')
    if incomplete: warnings.append('legacy capture has incomplete provenance')
    complete=[c for c in captures if c not in incomplete]
    for key in ('world_manifest_sha256','materials_spec_sha256','tier','lighting','main_sha'):
        if len({c[key] for c in complete})>1: raise ValueError(f'mixed render captures: {key}')
    if len({c['git_sha'] for c in complete})>1:
        if not historical: raise ValueError('mixed render captures: git_sha')
        warnings.append('different git commits; historical diagnostics only')
    if complete:
        world_path=input_dir/'world_manifest.json' if inputs is not None else REGION/'generated/world_manifest.json'
        material_path=input_dir/'materials_spec.json' if inputs is not None else ROOT/'art-source/world/materials/materials_spec.json'
        for path,key in ((world_path,'world_manifest_sha256'),(material_path,'materials_spec_sha256')):
            if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest()!=complete[0][key]:
                raise ValueError(f'world/material snapshot mismatch: {key}')
    capture_ids=[camera for c in captures for camera in c.get('cameras',[])]
    if len(set(capture_ids))!=len(capture_ids): raise ValueError('duplicate camera capture')
    if set(capture_ids)-{r['camera'] for r in refs}: raise ValueError('capture contains unknown reference cameras')
    provenance=('HISTORICAL_UNVERIFIED' if warnings or not captures else 'HISTORICAL_VERIFIED') if historical else 'RECORDED'
    for r in refs:
        confidence=r.get('pose_confidence','C')
        if confidence not in ('A','B','C'): raise ValueError(f'invalid pose_confidence: {r["camera"]}')
        if confidence not in ('A','B') and not include_rejected:
            stale=outdir/(r['camera']+'.png')
            if stale.exists(): stale.unlink()
            rejected.append({'camera':r['camera'], 'reason':r.get('pose_reason','Unreviewed pose')})
            continue
        render=render_dir/(r['camera']+'.png')
        if not render.exists():
            missing.append(r['camera']); continue
        if captures:
            matching=[c for c in captures if r['camera'] in c.get('cameras',[])]
            digest=hashlib.sha256(render.read_bytes()).hexdigest()
            if len(matching)!=1 or matching[0].get('render_sha256',{}).get(r['camera'])!=digest:
                raise ValueError(f'render hash/provenance mismatch: {r["camera"]}')
        with Image.open(ROOT/r.get('comparison_photo',r['photo'])) as src, Image.open(render) as dst:
            if r.get('sha256') and hashlib.sha256((ROOT/r['photo']).read_bytes()).hexdigest()!=r['sha256']:
                raise ValueError(f"photo hash mismatch: {r['camera']}")
            if r.get('comparison_sha256') and hashlib.sha256((ROOT/r.get('comparison_photo',r['photo'])).read_bytes()).hexdigest()!=r['comparison_sha256']:
                raise ValueError(f"rectified photo hash mismatch: {r['camera']}")
            if captures and matching[0].get('width') and tuple(dst.size)!=(matching[0]['width'],matching[0]['height']):
                raise ValueError(f'capture dimensions mismatch: {r["camera"]}')
            if src.width*dst.height != dst.width*src.height:
                raise ValueError(f"aspect mismatch: {r['camera']}; render at photo aspect ratio")
            left,right=src.convert('RGB'),dst.convert('RGB')
        render_digest=hashlib.sha256(render.read_bytes()).hexdigest()
        observed_photo_sha=hashlib.sha256((ROOT/r.get('comparison_photo',r['photo'])).read_bytes()).hexdigest()
        lighting=matching[0].get('lighting') if captures else None
        tier=matching[0].get('tier') if captures else None
        photo_samples=paired_photometry(photometry_annotations,{**r,'comparison_sha256':observed_photo_sha},render_digest,lighting)
        masks=photo_samples['masks'] or r.get('authored_overrides',{}).get('masks',{})
        m={'camera':r['camera'],'pose_status':r['pose_status'],
           'pose_confidence':r.get('pose_confidence','C'), 'photometric_use':photo_samples['use'],
           'photometry':{k:v for k,v in photo_samples.items() if k!='masks'},'mask_signature':photo_samples['mask_signature'],
           'pose_signature':camera_signature(cameras_by_id.get(r['camera'])),'tier':tier,'lighting':lighting,'metric_definition':DEFINITION,'photo_sha256':r.get('sha256'),
           'render_sha256':hashlib.sha256(render.read_bytes()).hexdigest(), 'comparison_sha256':r.get('comparison_sha256'),
           'photo':measurements(left,r['horizon_y_fraction'],masks.get('photo')),
           'render':measurements(right,r['horizon_y_fraction'],masks.get('render'))}
        if m['photometric_use'] and any(m[panel][region+'_samples']['pixels']<32 for panel in ('photo','render') for region in ('sky','asphalt')):
            m['photometric_use']=False;m['photometry']['status']='INSUFFICIENT_SAMPLE_PIXELS'
        ph=np.array(m['photo']['histogram_32'],dtype=float); ph/=ph.sum()
        rh=np.array(m['render']['histogram_32'],dtype=float); rh/=rh.sum()
        m['landmarks']=landmark_report(annotations,{**r,'comparison_sha256':hashlib.sha256((ROOT/r.get('comparison_photo',r['photo'])).read_bytes()).hexdigest()},m['render_sha256'],right.size)
        m['histogram_l1_distance']=round(float(np.abs(ph-rh).sum()),5)
        metrics.append(m)
        height=round(470*r['height']/r['width'])
        sheet=Image.new('RGB',(960,height+210),'#202020')
        d=ImageDraw.Draw(sheet)
        d.text((8,4),r['camera']+' | '+r.get('pose_confidence','C')+' | '+r['pose_status']+' | anchors '+str(len(m['landmarks']['points'])),fill='white')
        for x,im,label in [(0,left,'PHOTO'),(490,right,'RENDER')]:
            sheet.paste(im.resize((470,height)),(x,24))
            for fraction in (0.25,0.5,0.75):
                d.line((x+470*fraction,24,x+470*fraction,24+height),fill='#808080')
                d.line((x,24+height*fraction,x+470,24+height*fraction),fill='#808080')
            hy=24+height*r['horizon_y_fraction']
            d.line((x,hy,x+470,hy),fill='#ff5050',width=2)
            d.text((x+4,28),label,fill='#ff5050')
        for point in m['landmarks']['points']:
            for panel,x in (('photo',0),('render',490)):
                px=x+470*point[panel][0];py=24+height*point[panel][1]
                d.ellipse((px-4,py-4,px+4,py+4),outline='#dd99ff',width=2)
                d.text((px+5,py-10),point['id'],fill='#dd99ff')
        lines=r.get('authored_overrides',{}).get('vanishing_lines')
        if lines:
            for line in lines:
                d.line([(470*px,24+height*py) for px,py in line],fill='#00ffff',width=2)
            vx,vy=vanishing_horizon(lines);vx*=470;vy=24+height*vy
            d.ellipse((vx-4,vy-4,vx+4,vy+4),outline='#00ffff',width=2)
        for j,text in enumerate([f"Photo: {r['author']} | {r['license']} | {r['captured_at']}",r['page_url'],
                                  'Grid: 25%; red: authored horizon. Photo rectified/cropped if intrinsics cached.',
                                  'Histogram and sky/asphalt estimates: metrics.json; no gate PASS inferred.',
                                  f"Photometric use: {m['photometric_use']} ({m['photometry']['status']}) | {r.get('photo_vs_data_age','Data epoch UNVERIFIED')}"]):
            d.text((6,height+29+j*17),text,fill='white')
        peak=max(float(ph.max()),float(rh.max()),1e-9)
        for hist,color in [(ph,'#55bbff'),(rh,'#ffaa44')]:
            points=[(24+i*28,height+198-float(value)/peak*65) for i,value in enumerate(hist)]
            d.line(points,fill=color,width=2)
        d.text((24,height+119),'sRGB luma histogram: blue PHOTO / orange RENDER (32 bins, normalized)',fill='white')
        save_png(sheet,outdir/(r['camera']+'.png'))
    write(outdir/'metrics.json',{'schema':'kamion/sbs-metrics/2','metric_definition':DEFINITION,'photometry_sha256':photometry_hash,'pairs':metrics,'missing_renders':missing,'rejected_poses':rejected,'render_captures':captures,'provenance_status':provenance,'provenance_warnings':warnings,'landmarks_sha256':landmark_hash,'gate_status':'UNVERIFIED',
          'cameras_sha256':camera_hash})
    print(f'Composed {len(metrics)} pairs; missing {len(missing)} renders.')
    if strict and missing:
        raise SystemExit(2)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    sub=ap.add_subparsers(dest='command',required=True)
    p=sub.add_parser('prepare'); p.add_argument('--count-per-segment',type=int,default=20)
    sub.add_parser('fetch-intrinsics')
    p=sub.add_parser('compose'); p.add_argument('--renders',type=Path,required=True); p.add_argument('--output',type=Path,required=True); p.add_argument('--include-rejected',action='store_true'); p.add_argument('--historical',action='store_true'); p.add_argument('--inputs',type=Path); p.add_argument('--landmarks',type=Path); p.add_argument('--photometry',type=Path)
    p=sub.add_parser('report'); p.add_argument('--runs',type=Path,nargs='+',required=True); p.add_argument('--output',type=Path,required=True); p.add_argument('--recognition',type=Path)
    args=ap.parse_args()
    if args.command=='prepare': prepare(args.count_per_segment)
    elif args.command=='fetch-intrinsics': fetch_intrinsics()
    elif args.command=='report':
        from sbs_report import build_report
        build_report(args.runs,args.output,args.recognition)
    else: compose(args.renders,args.output,include_rejected=args.include_rejected,historical=args.historical,inputs=args.inputs,landmarks_file=args.landmarks,photometry_file=args.photometry)


if __name__=='__main__':
    main()
