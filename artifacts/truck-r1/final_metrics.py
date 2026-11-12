"""Matched final windshield controls, lamp clipping and owner-method paint profile."""
import json
from measure import ROOT, main

for stage in ('final-candidate', 'final-control-no-pane'):
    main(stage)
before = json.loads((ROOT / 'before-metrics.json').read_text(encoding='utf8'))
final = json.loads((ROOT / 'final-candidate-metrics.json').read_text(encoding='utf8'))
no_pane = json.loads((ROOT / 'final-control-no-pane-metrics.json').read_text(encoding='utf8'))
rows = {}
for condition, data in final.items():
    lamp_old = before[condition]['truck-front']['left_lamp']
    lamp = data['truck-front']['left_lamp']
    glass = data['truck-34']['glass']['legacy1024']
    row = {
        'lamp_ge254_before': lamp_old['all_channels_ge254_pixels'],
        'lamp_ge254_after': lamp['all_channels_ge254_pixels'],
        'door_profile_before': before[condition]['truck-34']['door']['legacy1024']['vertical_profile_range_points'],
        'door_profile_after': data['truck-34']['door']['legacy1024']['vertical_profile_range_points'],
        'glass_median_after': glass['p50_display_percent'],
        'glass_sigma_after': glass['sigma_display_points'],
    }
    if condition in no_pane:
        sigma = no_pane[condition]['truck-34']['glass']['legacy1024']['sigma_display_points']
        row.update(no_pane_sigma=sigma, D44_sigma_ratio=glass['sigma_display_points']/sigma if sigma else None)
    rows[condition] = row
(ROOT / 'final-summary.json').write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding='utf8')
print(json.dumps(rows, indent=2, ensure_ascii=False))
