"""Metadata-only photo-pose hypotheses; no generator, mesh or raster processing."""
import json
import math
from pathlib import Path
from pyproj import Geod, Transformer

ev = Path(__file__).resolve().parent
root = ev.parents[2]
photo = next(p for p in json.loads((ev / 'reference/provenance.json').read_text(encoding='utf-8-sig'))['images']
             if p['id'] == '1911352299378570')
selected = next(p for p in json.loads((ev / 'shelter-camera-evidence.json').read_text(encoding='utf-8-sig'))['selected']
                if p['osm_node'] == 5802408812)['selected_instance']
origin = json.loads((ev / 'manifest-before.json').read_text(encoding='utf-8-sig'))['origin_epsg2180']
project = Transformer.from_crs(4326, 2180, always_xy=True)
east, north = project.transform(photo['lon'], photo['lat'])
lon2, lat2, _ = Geod(ellps='WGS84').fwd(photo['lon'], photo['lat'], photo['compass_angle'], 100)
east2, north2 = project.transform(lon2, lat2)
grid_heading = math.atan2(east2-east, north2-north)
local = [east-origin['x'], north-origin['y']]
de, dn = selected['e']-local[0], selected['n']-local[1]
target_bearing = math.atan2(de, dn)
relative = (target_bearing-grid_heading+math.pi)%(2*math.pi)-math.pi
# The 960 x 720 source preview has a low horizon, roughly 2/3 down the image.
# This is a manual visual hypothesis, not recovered camera calibration.
horizon_fraction = .665
aspect = 4/3
ground = selected['z']  # route_start has no elevation; no false road-height claim
height = 1.65
cameras = []
fits = []
for vfov in (45, 55, 65):
    pitch = math.atan((2*horizon_fraction-1)*math.tan(math.radians(vfov/2)))
    cameras.append(dict(id=f'furniture-photo-1911352299378570-v{vfov}', type='persp', fov_deg=vfov,
        pos=[round(local[0],3),round(local[1],3),round(ground+height,3)],
        look_at=[round(local[0]+50*math.sin(grid_heading),3),
                 round(local[1]+50*math.cos(grid_heading),3),round(ground+height+50*math.tan(pitch),3)],
        note='WORKING_VALUE photo GPS/compass hypothesis; FOV, horizon, road height and eye height uncalibrated'))
    # Manual target observations from the 960 x 720 preview. A one-object fit is
    # explicitly circular for its assumed dimensions, not independent calibration.
    observed_u, observed_ground_v = .646, .701
    forward = [math.sin(grid_heading), math.cos(grid_heading)]
    right = [math.cos(grid_heading), -math.sin(grid_heading)]
    depth = de*forward[0]+dn*forward[1]
    lateral = de*right[0]+dn*right[1]
    desired = depth*(2*observed_u-1)*aspect*math.tan(math.radians(vfov/2))
    shift = lateral-desired
    fitted = [local[0]+shift*right[0], local[1]+shift*right[1]]
    slope = (1-2*observed_ground_v)*math.tan(math.radians(vfov/2))
    relative_z = depth*(math.sin(pitch)+slope*math.cos(pitch))/(math.cos(pitch)-slope*math.sin(pitch))
    camera_z = ground-relative_z
    cameras.append(dict(id=f'furniture-photo-1911352299378570-fit-v{vfov}',type='persp',fov_deg=vfov,
        pos=[round(fitted[0],3),round(fitted[1],3),round(camera_z,3)],
        look_at=[round(fitted[0]+50*forward[0],3),round(fitted[1]+50*forward[1],3),
                 round(camera_z+50*math.tan(pitch),3)],
        note='WORKING_VALUE one-object photo fit; nominal model and manual horizon, not recovered camera or metric validation'))
    fits.append(dict(vfov_deg=vfov,lateral_shift_m=shift,source_en=fitted,camera_z_m=camera_z,
        implied_road_height_if_eye_165_m=camera_z-height,observed_target_u=observed_u,
        observed_ground_v=observed_ground_v))
result = dict(photo_id=photo['id'], original_sha256=photo['sha256'], source_lon_lat=[photo['lon'],photo['lat']],
    source_compass_deg=photo['compass_angle'], grid_heading_deg=math.degrees(grid_heading)%360,
    source_position_en=local, shelter_instance=selected, distance_to_shelter_m=math.hypot(de,dn),
    target_relative_bearing_deg=math.degrees(relative), horizon_fraction_working=horizon_fraction,
    image_aspect=aspect, assumed_road_height_m=ground, assumed_eye_height_m=height,
    caveat='Pose hypotheses only. No matched-frame or metric/photo calibration claim until inspected against renders.',
    source_provenance='reference/provenance.json')
result['one_object_fits_working'] = fits
result['fit_caveat'] = 'Manual image points and nominal generated shelter ground. Inspect road/background too; never present this fit as independent dimensional evidence.'
(ev / 'photo-cameras.json').write_text(json.dumps(dict(cameras=cameras),indent=2)+'\n',encoding='utf-8')
(ev / 'photo-camera-evidence.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(cameras=len(cameras),local_en=local,distance_m=result['distance_to_shelter_m'],
    grid_heading_deg=result['grid_heading_deg'],target_relative_deg=math.degrees(relative))))
