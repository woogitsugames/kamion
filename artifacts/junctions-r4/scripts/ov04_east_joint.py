"""ADR 0110 step 5d: eastbound split, run-out at the bridge joint (b4: width profile on the 94 m edge widened the lane
bands of the whole edge -> furniture_in_lane x 9; ramp edge line on the bridge kerb of the main carriageway)."""
import re
p = 'Data/Regions/bialystok-industrial-c/overrides.yaml'
s = open(p, encoding='utf-8').read()
def cut(s, a_id, b_id):
    a = s.index(f'  - id: {a_id}\n'); b = s.index(f'  - id: {b_id}\n'); return s[:a] + s[b:]
s = cut(s, 'dk8-e-split-main-geometry-3', 'dk8-e-split-link-geometry')
s = cut(s, 'dk8-e-split-link-geometry-3', 'dk8-e-split-p21-front')
old = '''      width: [[0.0, 10.6], [1.0, 9.0]]
      center_offset: [[0.0, -1.0], [1.0, -0.4]]
'''
new = '''      width: [[0.0, 10.6], [1.0, 8.0]]
      center_offset: [[0.0, -1.0], [1.0, 0.0]]
'''
assert old in s; s = s.replace(old, new)
old = '''      width: [[0.0, 3.8], [0.206, 3.8], [0.397, 3.8], [0.616, 3.8], [0.78, 4.3], [1.0, 7.2]]
      center_offset: [[0.0, -3.4], [0.206, -0.85], [0.397, -0.6], [0.616, 1.3], [0.78, 1.75], [1.0, 1.2]]
'''
new = '''      width: [[0.0, 3.8], [0.206, 3.8], [0.397, 3.8], [0.616, 3.8], [0.78, 4.3], [1.0, 6.4]]
      center_offset: [[0.0, -3.4], [0.206, -0.85], [0.397, -0.6], [0.616, 1.3], [0.78, 1.75], [1.0, 0.8]]
'''
assert old in s; s = s.replace(old, new)
old = '''      width: [[0.0, 7.2], [1.0, 7.5]]
      center_offset: [[0.0, 1.2], [1.0, 0.9]]
'''
new = '''      width: [[0.0, 6.4], [1.0, 7.5]]
      center_offset: [[0.0, 0.8], [1.0, 0.0]]
'''
assert old in s; s = s.replace(old, new)
s = s.replace('reason: The widened plate of dk8-e-split-main-geometry runs out towards the viaduct over this 11.5 m edge.',
              'reason: The widened plate of dk8-e-split-main-geometry runs out to the standard 8.0 m on the OSM way over this 11.5 m edge (viaduct deck not touched).')
s = s.replace('reason: Continuation of dk8-e-split-link-geometry over the 11.5 m edge at the bridge joint (placement and width run on).',
              'reason: dk8-e-split-link-geometry runs back to the OSM way and 7.5 m over the 11.5 m edge at the bridge joint.')
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
