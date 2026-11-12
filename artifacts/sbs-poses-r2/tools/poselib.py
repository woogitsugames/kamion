"""ADR 0130 helper: replicate tools/refs/sbs_gate3.py prepare() camera formula for single cameras
(no photo download/rectification), build diagnostic probe camera files and ortho top-down maps."""
from __future__ import annotations
import json, math, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/refs'))
import sbs_gate3 as S  # noqa: E402
from pyproj import Transformer  # noqa: E402
import yaml  # noqa: E402

REGION = ROOT / 'Data/Regions/bialystok-industrial-c'
TR = Transformer.from_crs(4326, 2180, always_xy=True)
ORIGIN = yaml.safe_load((REGION / 'region.yaml').read_text(encoding='utf-8'))['origin']
_terrain = None


def terrain(e, n):
    global _terrain
    if _terrain is None:
        _terrain = S.ground_sampler()
    return _terrain(e + ORIGIN['x'], n + ORIGIN['y'])


def refs():
    return {r['camera']: r for r in S.read(REGION / 'sbs_references.json')['references']}


def overrides():
    return S.read(REGION / 'sbs_authored_overrides.json')['authored_overrides']


def camera(ref, ov, cam_id=None):
    """Exactly the Mapillary branch of prepare(); returns (camera dict, derived info)."""
    lens = ref['projection']
    focal = ref['rectified_focal']
    width, height = ref['width'], ref['height']
    x, y = TR.transform(ref['lon'], ref['lat'])
    e = x - ORIGIN['x'] + ov.get('east_delta_m', 0)
    n = y - ORIGIN['y'] + ov.get('north_delta_m', 0)
    eye = ov.get('eye_height_m', 2.2)
    u = ov.get('absolute_u_m', terrain(e, n) + eye)
    true_heading = lens.get('computed_compass_angle', ref['heading_original_deg']) if lens else ref['heading_original_deg']
    if ov.get('heading_source') == 'original':
        true_heading = ref['heading_original_deg']
    heading = (S.grid_heading(ref['lon'], ref['lat'], true_heading, TR) + ov.get('heading_delta_deg', 0)) % 360
    native_hfov = math.degrees(2 * math.atan(width / max(width, height) / (2 * focal))) if focal else 90
    fov = S.vfov(ov.get('horizontal_fov_deg', native_hfov), width / height)
    horizon = ov.get('horizon_y_fraction', 0.5)
    if lens:
        horizon = S.rectified_horizon(horizon, width, height, lens, focal)
    horizon = ov.get('rectified_horizon_y_fraction', horizon)
    if 'vanishing_lines' in ov:
        horizon = S.vanishing_horizon(ov['vanishing_lines'])[1]
    pitch = math.degrees(math.atan((2 * horizon - 1) * math.tan(math.radians(fov) / 2)))
    cam = {'id': cam_id or ref['camera'], 'kind': 'photo_match', 'seat': 'file', 'type': 'persp',
           'pos': [round(e, 4), round(n, 4), round(u, 4)], 'look_at': S.pose(e, n, u, heading, pitch),
           'fov_deg': round(fov, 5), 'segment': ref['segment'],
           'pose_confidence': ov.get('pose_confidence', 'C'), 'pose_reason': ov.get('pose_reason', 'Unreviewed pose'),
           'note': 'ADR0103 photo GPS/heading; NMT+eye/FOV/pitch WORKING_VALUE; see sbs_references.json'}
    return cam, {'gps_en': [x - ORIGIN['x'], y - ORIGIN['y']], 'heading': heading, 'pitch': pitch,
                 'hfov': native_hfov, 'horizon_rect': horizon, 'terrain_u': terrain(e, n)}


def verify_all():
    R, O = refs(), overrides()
    prod = {c['id']: c for c in S.read(REGION / 'sbs_cameras.json')['cameras']}
    bad = []
    for cid, r in R.items():
        if not r['source_id'].isdecimal():
            continue
        c, _ = camera(r, O.get(cid, {}))
        p = prod[cid]
        d = max(abs(a - b) for a, b in zip(c['pos'] + c['look_at'] + [c['fov_deg']], p['pos'] + p['look_at'] + [p['fov_deg']]))
        if d > 2e-3:
            bad.append((cid, d))
    return bad


if __name__ == '__main__':
    print('mismatches:', verify_all())


# ---------- probes and maps ----------
from PIL import Image, ImageDraw  # noqa: E402
Image.MAX_IMAGE_PIXELS = None
_ortho = None


def ortho():
    global _ortho
    if _ortho is None:
        meta = S.read(REGION / 'ortho.json')
        _ortho = (Image.open(ROOT / meta['file']).convert('RGB'), meta)
    return _ortho


def road_edges():
    g = S.read(REGION / 'roads.graph.json')
    out = []
    for e in g['edges']:
        pts = [(x - ORIGIN['x'], y - ORIGIN['y']) for x, y in e['geometry']]
        a = e['attrs']
        out.append((pts, {k: (v.get('v') if isinstance(v, dict) else v) for k, v in a.items()}))
    return out


def draw_map(path, center, half=70, cams=(), scale=4):
    """cams: list of (label, camera dict, colour, hfov_deg)."""
    im, meta = ortho()
    x0, y0 = meta['bounds'][0], meta['bounds'][3]
    res = meta['res_m']
    def px(e, n):
        X, Y = e + ORIGIN['x'], n + ORIGIN['y']
        return ((X - x0) / res, (y0 - Y) / res)
    cx, cy = px(*center)
    r = half / res
    crop = im.crop((int(cx - r), int(cy - r), int(cx + r), int(cy + r))).resize((int(2 * half * scale), int(2 * half * scale)))
    d = ImageDraw.Draw(crop)
    k = scale * res
    def loc(e, n):
        X, Y = px(e, n)
        return ((X - (int(cx - r))) * k, (Y - (int(cy - r))) * k)
    for pts, a in road_edges():
        if all(abs(p[0] - center[0]) > half * 1.5 or abs(p[1] - center[1]) > half * 1.5 for p in pts):
            continue
        col = '#ff00ff' if a.get('bridge') else '#00ffff'
        d.line([loc(*p) for p in pts], fill=col, width=1)
    for label, c, col, hfov in cams:
        e, n = c['pos'][:2]
        le, ln = c['look_at'][:2]
        h = math.atan2(le - e, ln - n)
        p = loc(e, n)
        for s in (-1, 1):
            a = h + s * math.radians(hfov / 2)
            d.line([p, loc(e + 60 * math.sin(a), n + 60 * math.cos(a))], fill=col, width=1)
        d.ellipse((p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3), outline=col, width=2)
        d.text((p[0] + 4, p[1] - 4), label, fill=col)
    # 10 m scale bar
    d.line([(10, crop.height - 10), (10 + 10 * scale, crop.height - 10)], fill='white', width=3)
    d.text((12, crop.height - 24), '10 m  N up', fill='white')
    crop.save(path)


def road_axis(center, radius=25):
    """Dominant heading of nearest road edge segment (deg grid) for reference."""
    best = None
    for pts, a in road_edges():
        for p, q in zip(pts, pts[1:]):
            mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
            dd = math.hypot(mx - center[0], my - center[1])
            if dd < radius and (best is None or dd < best[0]):
                best = (dd, math.degrees(math.atan2(q[0] - p[0], q[1] - p[1])) % 360, a.get('name'), a.get('oneway'), a.get('lanes'), a.get('bridge'))
    return best
