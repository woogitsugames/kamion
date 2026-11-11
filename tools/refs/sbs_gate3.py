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
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageOps
from pyproj import Geod, Transformer
from shapely.geometry import LineString, Point

ROOT = Path(__file__).resolve().parents[2]
REGION = ROOT / 'Data/Regions/bialystok-industrial-c'
OUTPUT = ROOT / 'artifacts/sbs-gate3'


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
                focal,_,_=rectify(photo,lens,comparison)
            ov = overrides.get(camera_id, {})
            allowed = {'east_delta_m','north_delta_m','eye_height_m','absolute_u_m','heading_delta_deg',
                       'horizontal_fov_deg','horizon_y_fraction','rectified_horizon_y_fraction','heading_source','pose_status','note','masks'}
            if set(ov)-allowed:
                raise ValueError(f"unknown authored corrections for {camera_id}: {sorted(set(ov)-allowed)}")
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
            if not (0 < horizon < 1 and eye > 0):
                raise ValueError(f'invalid authored horizon/eye: {camera_id}')
            pitch = math.degrees(math.atan((2*horizon-1)*math.tan(math.radians(fov)/2)))
            cameras.append({'id': camera_id, 'kind': 'photo_match', 'seat': 'file', 'type': 'persp',
                            'pos': [round(e,4),round(n,4),round(u,4)], 'look_at': pose(e,n,u,heading,pitch),
                            'fov_deg': round(fov,5), 'segment': segment['id'],
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
                         'assumptions': ('NMT/eye/manual horizon WORKING_VALUE; FOV and radial rectification from Mapillary SfM intrinsics. Roll/GPS/SfM accuracy unverified.' if lens else 'NMT bare earth; eye/FOV/pitch WORKING_VALUE. Zero roll; lens distortion not corrected. GPS/compass accuracy unknown.'),
                         'authored_overrides': ov})
    write(REGION / 'sbs_cameras.json', {'schema': 'kamion/sbs-cameras/1', 'frame': 'E,N,absolute U', 'cameras': cameras})
    input_hashes={name:hashlib.sha256((REGION/name).read_bytes()).hexdigest()
                  for name in ('region.yaml','terrain.json','gate3_segment.json')}
    write(REGION / 'sbs_references.json', {'schema': 'kamion/sbs-references/1', 'input_sha256':input_hashes,
          'source_manifest_sha256': hashlib.sha256(manifest.read_bytes()).hexdigest(), 'references': refs})
    write(config_path, config)
    lines = ['# ADR 0103 — per-photo attribution (reference sheets only)', '',
             'Photos stay outside git and builds. Source pixels on sheets are rectified/cropped, resized and overlaid.',
             'Photo panels and their modifications: CC BY-SA 4.0; render panels retain project terms.',
             'License: https://creativecommons.org/licenses/by-sa/4.0/', '',
             '| Camera | Author | Date | Source | SHA256 |', '|---|---|---|---|---|']
    for r in refs:
        lines.append(f"| {r['camera']} | {r['author']} | {r['captured_at']} | [Mapillary {r['source_id']}]({r['page_url']}) | `{r['sha256']}` |")
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


def measurements(im, horizon, authored_masks=None):
    a = np.asarray(im.convert('RGB'),dtype=float)
    luma = a @ np.array([0.2126,0.7152,0.0722])
    yy,xx=np.indices(luma.shape)
    # Deliberately labelled estimates: no semantic segmenter or ground-truth masks.
    sky=(yy<luma.shape[0]*horizon)&(luma>115)&(a[:,:,2]>=a[:,:,0]*0.95)
    asphalt=(yy>luma.shape[0]*max(horizon,0.55))&(xx>luma.shape[1]*0.2)&(xx<luma.shape[1]*0.8)&(np.ptp(a,axis=2)<35)&(luma>25)&(luma<180)
    method='WORKING_VALUE RGB/position heuristic, not semantic ground truth'
    if authored_masks is not None:
        masks=[]
        for label in ('sky','asphalt'):
            mask=Image.new('1',im.size)
            draw=ImageDraw.Draw(mask)
            for polygon in authored_masks.get(label,[]):
                if len(polygon)<3 or any(not (0<=x<=1 and 0<=y<=1) for x,y in polygon):
                    raise ValueError('mask polygons require >=3 normalized points')
                draw.polygon([(x*(im.width-1),y*(im.height-1)) for x,y in polygon],fill=1)
            masks.append(np.asarray(mask,dtype=bool))
        sky,asphalt=masks
        if np.any(sky & asphalt): raise ValueError('sky/asphalt masks overlap')
        method='authored normalized polygons; see sbs_authored_overrides.json'
    hist=np.histogram(luma,bins=32,range=(0,256))[0]
    sky_luma=float(luma[sky].mean()) if sky.any() else None
    asphalt_luma=float(luma[asphalt].mean()) if asphalt.any() else None
    return {'luma_mean_srgb': round(float(luma.mean()),3), 'histogram_32':hist.tolist(),
            'sky_fraction_estimate':round(float(sky.mean()),5),
            'asphalt_fraction_estimate':round(float(asphalt.mean()),5),
            'sky_asphalt_ratio_estimate':round(float(sky.sum()/asphalt.sum()),5) if asphalt.any() else None,
            'sky_asphalt_area_ratio_estimate':round(float(sky.sum()/asphalt.sum()),5) if asphalt.any() else None,
            'sky_luma_mean_srgb_estimate':round(sky_luma,3) if sky_luma is not None else None,
            'asphalt_luma_mean_srgb_estimate':round(asphalt_luma,3) if asphalt_luma is not None else None,
            'sky_asphalt_luma_ratio_estimate':round(sky_luma/asphalt_luma,5) if sky_luma is not None and asphalt_luma else None,
            'mask_method':method}


def compose(render_dir, outdir, strict=True):
    refs=read(REGION/'sbs_references.json')['references']
    outdir.mkdir(parents=True,exist_ok=True)
    metrics=[]
    missing=[]
    for r in refs:
        render=render_dir/(r['camera']+'.png')
        if not render.exists():
            missing.append(r['camera']); continue
        with Image.open(ROOT/r.get('comparison_photo',r['photo'])) as src, Image.open(render) as dst:
            if r.get('sha256') and hashlib.sha256((ROOT/r['photo']).read_bytes()).hexdigest()!=r['sha256']:
                raise ValueError(f"photo hash mismatch: {r['camera']}")
            if r.get('comparison_sha256') and hashlib.sha256((ROOT/r.get('comparison_photo',r['photo'])).read_bytes()).hexdigest()!=r['comparison_sha256']:
                raise ValueError(f"rectified photo hash mismatch: {r['camera']}")
            if src.width*dst.height != dst.width*src.height:
                raise ValueError(f"aspect mismatch: {r['camera']}; render at photo aspect ratio")
            left,right=src.convert('RGB'),dst.convert('RGB')
        masks=r.get('authored_overrides',{}).get('masks',{})
        m={'camera':r['camera'],'pose_status':r['pose_status'], 'photo_sha256':r.get('sha256'),
           'render_sha256':hashlib.sha256(render.read_bytes()).hexdigest(), 'comparison_sha256':r.get('comparison_sha256'),
           'photo':measurements(left,r['horizon_y_fraction'],masks.get('photo')),
           'render':measurements(right,r['horizon_y_fraction'],masks.get('render'))}
        ph=np.array(m['photo']['histogram_32'],dtype=float); ph/=ph.sum()
        rh=np.array(m['render']['histogram_32'],dtype=float); rh/=rh.sum()
        m['histogram_l1_distance']=round(float(np.abs(ph-rh).sum()),5)
        metrics.append(m)
        height=round(470*r['height']/r['width'])
        sheet=Image.new('RGB',(960,height+190),'#202020')
        d=ImageDraw.Draw(sheet)
        d.text((8,4),r['camera']+' | '+r['pose_status'],fill='white')
        for x,im,label in [(0,left,'PHOTO'),(490,right,'RENDER')]:
            sheet.paste(im.resize((470,height)),(x,24))
            for fraction in (0.25,0.5,0.75):
                d.line((x+470*fraction,24,x+470*fraction,24+height),fill='#808080')
                d.line((x,24+height*fraction,x+470,24+height*fraction),fill='#808080')
            hy=24+height*r['horizon_y_fraction']
            d.line((x,hy,x+470,hy),fill='#ff5050',width=2)
            d.text((x+4,28),label,fill='#ff5050')
        for j,text in enumerate([f"Photo: {r['author']} | {r['license']} | {r['captured_at']}",r['page_url'],
                                  'Grid: 25%; red: authored horizon. Photo rectified/cropped if intrinsics cached.',
                                  'Histogram and sky/asphalt estimates: metrics.json; no gate PASS inferred.']):
            d.text((6,height+29+j*17),text,fill='white')
        peak=max(float(ph.max()),float(rh.max()),1e-9)
        for hist,color in [(ph,'#55bbff'),(rh,'#ffaa44')]:
            points=[(24+i*28,height+178-float(value)/peak*65) for i,value in enumerate(hist)]
            d.line(points,fill=color,width=2)
        d.text((24,height+99),'sRGB luma histogram: blue PHOTO / orange RENDER (32 bins, normalized)',fill='white')
        save_png(sheet,outdir/(r['camera']+'.png'))
    write(outdir/'metrics.json',{'pairs':metrics,'missing_renders':missing,'gate_status':'UNVERIFIED',
          'cameras_sha256':hashlib.sha256((REGION/'sbs_cameras.json').read_bytes()).hexdigest()
              if (REGION/'sbs_cameras.json').exists() else None})
    print(f'Composed {len(metrics)} pairs; missing {len(missing)} renders.')
    if strict and missing:
        raise SystemExit(2)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    sub=ap.add_subparsers(dest='command',required=True)
    p=sub.add_parser('prepare'); p.add_argument('--count-per-segment',type=int,default=20)
    sub.add_parser('fetch-intrinsics')
    p=sub.add_parser('compose'); p.add_argument('--renders',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    if args.command=='prepare': prepare(args.count_per_segment)
    elif args.command=='fetch-intrinsics': fetch_intrinsics()
    else: compose(args.renders,args.output)


if __name__=='__main__':
    main()
