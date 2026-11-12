"""Report every captured view, with independent static and instanced budgets."""
import csv
import hashlib
import json
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MAIN = Path(r'C:\Users\matma\Documents\Claude\kamion')
STATIC = re.compile(r'^(.*?): objects=(\d+) drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)')
INSTANCED = re.compile(r'^  (.*?) instanced .*: draws (\d+), instances (\d+), triangles (\d+)k')

def read_stats(path):
    result = {}
    seen_instanced = set()
    for line in path.read_text().splitlines():
        if match := STATIC.match(line):
            camera, objects, draws, shadows, tris = match.groups()
            if camera in result:
                raise RuntimeError(f'Duplicate static statistics: {path}: {camera}')
            result[camera] = dict(objects=int(objects), static_draws=int(draws),
                                  shadow_draws=int(shadows), static_tris_k=int(tris),
                                  instanced_draws=0, instances=0, instanced_tris_k=0)
        if match := INSTANCED.match(line):
            camera, draws, instances, tris = match.groups()
            if camera not in result or camera in seen_instanced:
                raise RuntimeError(f'Missing/duplicate instanced statistics: {path}: {camera}')
            seen_instanced.add(camera)
            result[camera].update(instanced_draws=int(draws), instances=int(instances),
                                  instanced_tris_k=int(tris))
    if not result or set(result) != seen_instanced:
        raise RuntimeError(f'Incomplete statistics (including instancing): {path}')
    return result

def pair(left, right, target, titles):
    frames = [Image.open(path).convert('RGB') for path in (left, right)]
    height = min(360, max(round(frame.height * 480 / frame.width) for frame in frames))
    sheet = Image.new('RGB', (960, height + 34), 'white')
    draw = ImageDraw.Draw(sheet)
    for column, (source, title) in enumerate(zip(frames, titles)):
        frame = ImageOps.contain(source, (480, height))
        sheet.paste(frame, (column*480, 30))
        draw.text((column*480+3, 5), title[:72], fill='black')
    sheet.save(target, quality=93)

rows = []
for frozen in json.loads((HERE/'evidence-inputs.json').read_text(encoding='utf-8-sig'))['files']:
    actual = hashlib.sha256((ROOT/frozen['path']).read_bytes()).hexdigest()
    if actual.lower() != frozen['sha256'].lower():
        raise RuntimeError(f"Camera/reference input changed: {frozen['path']}")
if not (HERE/'After.complete').exists():
    raise RuntimeError('After matrix has not completed')

# Check the recorded inputs as well as current camera files. An unchanged camera
# alone would not isolate the facade change if sky, light or quality drifted.
capture_audit = []
phase_hashes = {'before':{}, 'after':{}}
allowed_changes = {
    'game/Assets/_Project/World/Import/WorldEdgeBuilder.cs',
    'tools/worldgen/streetscape/far_field.py',
    'game/Assets/_Project/Rendering/Shaders/WorldSurface.shader',
    'Data/Regions/bialystok-industrial-c/generated/world_manifest.json',
    'game/Assets/_Generated/World/bialystok-industrial-c/WorldC.unity',
    'game/Assets/_Generated/World/bialystok-industrial-c/WorldC_High.unity',
    'game/Assets/_Generated/World/bialystok-industrial-c/Meshes/world_edge.asset',
    'game/Assets/_Generated/World/bialystok-industrial-c/Meshes/Low/world_edge_far.asset',
    'game/Assets/_Generated/World/bialystok-industrial-c/Meshes/High/world_edge_far.asset',
}
required_changes = {
    'game/Assets/_Project/World/Import/WorldEdgeBuilder.cs',
}
native_input_groups = json.loads((HERE/'native-camera-groups.json').read_text(encoding='utf-8-sig'))['groups']
for tier in ('Low','High'):
    for lighting in ('clear','overcast'):
        config = f'{tier}-{lighting}'
        captures = [(HERE/'before'/config,HERE/'after'/config)]
        captures += [(HERE/'before-photo'/config/g['id'],HERE/'after-photo'/config/g['id'])
                     for g in native_input_groups]
        for before_dir,after_dir in captures:
            inputs = []
            for phase,directory in (('before',before_dir),('after',after_dir)):
                doc = json.loads((directory/'capture-inputs.json').read_text(encoding='utf-8-sig'))
                hashes = doc.get('inputs_sha256',doc.get('input_sha256'))
                if not hashes or doc['phase'] != phase or doc['tier'] != tier or doc['lighting'] != lighting:
                    raise RuntimeError(f'Incorrect capture identity: {directory}')
                normalized = {('artifacts/edge-r6/proof-cameras.json' if key == 'proof-cameras.json' else key):value.lower()
                              for key,value in hashes.items()}
                for key,value in normalized.items():
                    if phase_hashes[phase].setdefault(key,value) != value:
                        raise RuntimeError(f'Input drift within {phase}: {key}')
                inputs.append(normalized)
            old,new = inputs
            if old.keys() != new.keys():
                raise RuntimeError(f'Capture fingerprint coverage changed: {before_dir}')
            changed = {key for key in old if old[key] != new[key]}
            if changed - allowed_changes or not required_changes <= changed:
                raise RuntimeError(f'Unexpected/missing input changes: {before_dir}: {sorted(changed)}')
            capture_audit.append(dict(before=str(before_dir.relative_to(HERE)),
                                      after=str(after_dir.relative_to(HERE)),changed=sorted(changed),
                                      unchanged_inputs=len(old)-len(changed)))
(HERE/'capture-inputs-audit.json').write_text(json.dumps(capture_audit,indent=2),encoding='utf-8')
pairs = HERE / 'pairs'
pairs.mkdir(exist_ok=True)

def append_matrix(config, before_dir, after_dir, expected_ids=None):
        before = read_stats(before_dir / 'stats.txt')
        after = read_stats(after_dir / 'stats.txt')
        assert before.keys() == after.keys(), (config, before.keys() ^ after.keys())
        if expected_ids is not None:
            assert set(before) == set(expected_ids), (config, set(before) ^ set(expected_ids))
        for camera in before:
            b, a = before[camera], after[camera]
            draws = a['static_draws']+a['instanced_draws']-b['static_draws']-b['instanced_draws']
            bt = b['static_tris_k']+b['instanced_tris_k']
            at = a['static_tris_k']+a['instanced_tris_k']
            shadows = a['shadow_draws'] - b['shadow_draws']
            row = dict(configuration=config, camera=camera, before=b, after=a,
                       delta_draws=draws, delta_tris_k=at-bt,
                       delta_static_draws=a['static_draws']-b['static_draws'],
                       delta_instanced_draws=a['instanced_draws']-b['instanced_draws'],
                       delta_shadow_draws=shadows,
                       low_budget_pass=(draws <= 0 and shadows <= 0 and at <= bt*1.02 and
                                        a['static_draws'] <= b['static_draws'] and
                                        a['instanced_draws'] <= b['instanced_draws']) if config.startswith('Low') else None)
            rows.append(row)
            if camera.startswith('edge-'):
                pair(before_dir/f'{camera}.png', after_dir/f'{camera}.png',
                     pairs/f'{config}-{camera}.jpg', (f'Przed | {camera} | {config}', f'Po | {camera} | {config}'))

native_groups = json.loads((HERE/'native-camera-groups.json').read_text(encoding='utf-8-sig'))['groups']
proof_ids = {row['id'] for row in json.loads((HERE/'proof-cameras.json').read_text(encoding='utf-8-sig'))['cameras']}
generic_camera_ids = None
for tier in ('Low','High'):
    for lighting in ('clear','overcast'):
        config = f'{tier}-{lighting}'
        ids = set(read_stats(HERE/'before'/config/'stats.txt'))
        if not proof_ids <= ids:
            raise RuntimeError(f'Missing frozen proof cameras: {config}: {proof_ids-ids}')
        if generic_camera_ids is None:
            generic_camera_ids = ids
        elif ids != generic_camera_ids:
            raise RuntimeError(f'Generic camera matrix drifted: {config}')
        append_matrix(config, HERE/'before'/config, HERE/'after'/config)
        for group in native_groups:
            name = group['id']
            append_matrix(f'{config}-photo-{name}', HERE/'before-photo'/config/name,
                          HERE/'after-photo'/config/name, group['camera_ids'])
(HERE/'measurements.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
with (HERE/'all-cameras.csv').open('w', newline='', encoding='utf-8-sig') as stream:
    base_fields = ['configuration', 'camera', 'delta_draws', 'delta_tris_k', 'low_budget_pass',
                   'delta_static_draws','delta_instanced_draws','delta_shadow_draws']
    fields = list(base_fields)
    fields += [f'{phase}_{key}' for phase in ('before', 'after') for key in rows[0]['before']]
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        flat = {key:row[key] for key in base_fields}
        flat.update({f'{phase}_{key}':value for phase in ('before','after') for key,value in row[phase].items()})
        writer.writerow(flat)

refs = json.loads((ROOT/'Data/Regions/bialystok-industrial-c/sbs_references.json').read_text())['references']
photo_index = []
excluded = []
for ref in refs:
    camera = ref['camera']
    confidence = ref.get('pose_confidence', 'C')
    if confidence not in ('A','B','C'):
        raise ValueError(f'Unknown pose confidence: {camera} {confidence}')
    if confidence == 'C':
        excluded.append(dict(camera=camera,reason='pose_confidence C'))
        continue
    frozen_photo = HERE/'reference-photos'/f'{camera}.png'
    photo = frozen_photo
    if not photo.exists():
        raise FileNotFoundError(f'Accepted comparison photo unavailable: {photo}')
    expected = ref.get('comparison_sha256') or ref.get('sha256')
    if not expected or hashlib.sha256(photo.read_bytes()).hexdigest() != expected:
        raise RuntimeError(f'Reference photo hash mismatch: {camera}')
    with Image.open(photo) as source_image:
        source_size = source_image.size
    group = f'{source_size[0]}x{source_size[1]}'
    for config in ('Low-clear','High-clear','Low-overcast','High-overcast'):
        render = HERE/'after-photo'/config/group/f'{camera}.png'
        if not render.exists():
            raise FileNotFoundError(f'Photographic comparison requires the native-aspect render: {render}')
        with Image.open(render) as render_image:
            if render_image.size != source_size:
                raise RuntimeError(f'Photograph/render dimensions differ: {camera}')
        target = pairs/f'photo-{config}-{camera}.jpg'
        pair(photo, render, target, (f"Zdjecie | {ref['author']} | {ref['license']}", f'Render | {config} | poza {confidence}/WORKING_VALUE'))
        photo_index.append(dict(camera=camera, configuration=config, pair=target.name,
                                photo=str(photo), render=str(render), source=ref['page_url'], author=ref['author'],
                                source_dimensions=source_size, matching_dimensions=True,
                                license=ref['license'], pose=confidence, photometry='UNVERIFIED'))
(HERE/'photo-index.json').write_text(json.dumps(photo_index, indent=2), encoding='utf-8')
(HERE/'excluded-references.json').write_text(json.dumps(excluded,indent=2),encoding='utf-8')
low = [row for row in rows if row['configuration'].startswith('Low')]
summary = dict(pairs=len(rows), photographic_pairs=len(photo_index), low_pairs=len(low),
               generic_cameras_per_configuration=len(generic_camera_ids),
               frozen_proof_cameras=len(proof_ids),
               native_cameras_per_configuration=sum(len(g['camera_ids']) for g in native_groups),
               low_failures=[row for row in low if not row['low_budget_pass']],
               note='Editor CPU estimates with rounded triangles; no device GPU claim. High R8 pre-post limits final photometry.')
(HERE/'budget-summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
print(json.dumps({key:value for key,value in summary.items() if key != 'low_failures'}))
print('Low budget failures:', len(summary['low_failures']))
if summary['low_failures']:
    raise RuntimeError('Low budget regression; inspect all-cameras.csv before accepting the change')
