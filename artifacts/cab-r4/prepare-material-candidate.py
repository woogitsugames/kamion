"""Run only under cab-r4 heavy lease, after the fresh baseline; writes artifacts only."""
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
baseline = json.loads((HERE / 'baseline-sequence.json').read_text(encoding='utf-8-sig'))
if baseline['status'] != 'finished':
    raise RuntimeError('Finish fresh baseline before preparing a material candidate')

spec = importlib.util.spec_from_file_location('cab_cc0', ROOT / 'tools/blender/truck/interior/cc0_leather.py')
cab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cab)
source = ROOT / 'art-source/truck/interior/export/textures'
config = json.loads(cab.CONFIG.read_text(encoding='utf-8-sig'))
if config['plastic'].get('normal_highpass_mm', 0) != 0:
    raise RuntimeError('Expected unfiltered baseline configuration')
output = HERE / 'material-prep'
output.mkdir(exist_ok=True)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


report = {'scope': 'Offline candidate; no game-map writes or visual acceptance',
          'baseline': [], 'candidate': [], 'normal_highpass_mm': 1.5,
          'reference_tile_metres': config['plastic']['tile_metres'],
          'uv_limits': 'Nominal 10 cm tile; inherited per-part UV sizes remain. Not a uniform physical cutoff over every part.',
          'parameter_status': 'WORKING_VALUE', 'status': 'incomplete'}
record = output / 'verification.json'
try:
    # Zero/default must reproduce both current materials before experimenting.
    for profile in ('leather', 'plastic'):
        args, _ = cab.config_args(output / 'reproduction', source / f'High/T_Cab_{profile.title()}_Detail.png', profile=profile)
        if args.normal_highpass_mm != 0:
            raise RuntimeError('Baseline must have high-pass disabled for both materials')
        cab.prepare(args)
        for tier in ('High', 'Medium', 'Low'):
            for kind in ('Detail', 'Normal'):
                name = f'T_Cab_{profile.title()}_{kind}.png'
                original = source / tier / name
                reproduced = output / 'reproduction' / tier / name
                row = {'file': f'{tier}/{name}', 'original_sha256': sha(original), 'reproduced_sha256': sha(reproduced)}
                row['matches'] = row['original_sha256'] == row['reproduced_sha256']
                report['baseline'].append(row)
                if not row['matches']:
                    raise RuntimeError('Disabled path does not reproduce ' + row['file'])

    config['plastic']['normal_highpass_mm'] = 1.5
    candidate_config = output / 'candidate-hp15.json'
    candidate_config.write_text(json.dumps(config, indent=2), encoding='utf-8')
    args, _ = cab.config_args(output / 'candidate-hp15', source / 'High/T_Cab_Plastic_Detail.png', candidate_config, profile='plastic')
    cab.prepare(args)
    for tier in ('High', 'Medium', 'Low'):
        for kind in ('Detail', 'Normal'):
            name = f'T_Cab_Plastic_{kind}.png'
            old = source / tier / name
            new = output / 'candidate-hp15' / tier / name
            row = {'file': f'{tier}/{name}', 'baseline_sha256': sha(old), 'candidate_sha256': sha(new)}
            row['identical'] = row['baseline_sha256'] == row['candidate_sha256']
            if kind == 'Detail' and not row['identical']:
                raise RuntimeError('Candidate changed packed Detail/alpha: ' + row['file'])
            if kind == 'Normal':
                if row['identical']:
                    raise RuntimeError('Candidate normal did not change: ' + row['file'])
                values = np.asarray(Image.open(new).convert('RGB'), dtype=np.float32) / 255 * 2 - 1
                row['max_unit_length_error_8bit'] = float(np.max(np.abs(np.linalg.norm(values, axis=-1) - 1)))
                row['min_normal_z'] = float(values[..., 2].min())
                if row['max_unit_length_error_8bit'] > .015 or row['min_normal_z'] <= 0:
                    raise RuntimeError('Invalid quantized normal: ' + row['file'])
            report['candidate'].append(row)

    sheet = Image.new('RGB', (912, 960), '#dddddd')
    draw = ImageDraw.Draw(sheet)
    for row_index, tier in enumerate(('High', 'Low')):
        for column, folder in enumerate((source, output / 'candidate-hp15')):
            x, y = 8 + column * 452, row_index * 476
            label = f'{tier}: ' + ('baseline' if column == 0 else 'candidate sigma 1.5 mm')
            draw.text((x, y + 4), label, fill='black')
            im = Image.open(folder / tier / 'T_Cab_Plastic_Normal.png').convert('RGB')
            sheet.paste(im.resize((444, 444), Image.Resampling.NEAREST), (x, y + 24))
    draw.text((8, 948), 'Normal-map preview; not a game render or photo comparison', fill='black')
    sheet.save(output / 'normal-map-comparison-960.jpg', quality=94)
    report['status'] = 'PASS: 12/12 baseline maps exact; candidate changes only Plastic normals'
except Exception as exc:
    report['status'] = 'FAIL'
    report['error'] = str(exc)
    raise
finally:
    record.write_text(json.dumps(report, indent=2), encoding='utf-8')
print('CAB_MATERIAL_PREP_RESULT: OK')

