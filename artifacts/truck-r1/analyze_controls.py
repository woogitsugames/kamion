"""Display-space causal controls, not an HDR radiance measurement."""
import json
import numpy as np
from PIL import Image
from measure import ROOT, main, luminance

cases = ['white-on', 'white-off', 'dark-on', 'dark-off', 'no-pane']
data = {}
for case in cases:
    stage = 'control-' + case
    main(stage)
    data[case] = json.loads((ROOT / (stage + '-metrics.json')).read_text(encoding='utf8'))

def door_mean(case, condition):
    box = data[case][condition]['truck-34']['door']['native_box']
    with Image.open(ROOT / ('control-' + case) / condition / 'truck-34.png') as im:
        return float(luminance(im.convert('RGB').crop(box)).mean())

result = {}
for condition in data['white-on']:
    row = {}
    for paint in ['white', 'dark']:
        row[paint + '_coat_delta_mean_display_points'] = door_mean(paint + '-on', condition) - door_mean(paint + '-off', condition)
        for switch in ['on', 'off']:
            row[paint + '_door_profile_' + switch] = data[paint + '-' + switch][condition]['truck-34']['door']['legacy1024']['vertical_profile_range_points']
    if condition in data['no-pane']:
        actual = data['white-on'][condition]['truck-34']['glass']['legacy1024']['sigma_display_points']
        reference = data['no-pane'][condition]['truck-34']['glass']['legacy1024']['sigma_display_points']
        row['glass_sigma'] = actual
        row['no_windscreen_sigma'] = reference
        row['D44_ratio_same_crop'] = actual / reference if reference else None
    result[condition] = row
(ROOT / 'controls-summary.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf8')
print(json.dumps(result, indent=2, ensure_ascii=False))
