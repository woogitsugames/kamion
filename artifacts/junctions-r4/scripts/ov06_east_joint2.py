"""ADR 0110 step 5f: eastbound split - everything is back on the OSM way and the standard widths AT the bridge joint
(b6: the run-out lay on the 11.5 m bridge edge: deck width changing, lines on the bridge kerb, barrier in the lane band)."""
p = 'Data/Regions/bialystok-industrial-c/overrides.yaml'
s = open(p, encoding='utf-8').read()
def cut(s, a_id, b_id):
    a = s.index(f'  - id: {a_id}\n'); b = s.index(f'  - id: {b_id}\n'); return s[:a] + s[b:]
s = cut(s, 'dk8-e-split-main-geometry-2', 'dk8-e-split-link-geometry')
s = cut(s, 'dk8-e-split-link-geometry-2', 'dk8-e-split-p21-front')
old = '''      lane_edges: [0.5, 3.95, 6.85]
      width: 10.6
      center_offset: -1.0
      edge_lines: left
'''
new = '''      lane_edges: [0.5, 3.95, 6.85]
      width: [[0.0, 10.6], [0.8, 10.6], [1.0, 8.0]]
      center_offset: [[0.0, -1.0], [0.8, -1.0], [1.0, 0.0]]
      edge_lines: left
'''
assert old in s; s = s.replace(old, new)
old = '''      width: [[0.0, 3.8], [0.206, 3.8], [0.397, 3.8], [0.616, 3.8], [0.78, 4.3], [1.0, 6.4]]
      center_offset: [[0.0, -3.4], [0.206, -0.85], [0.397, -0.6], [0.616, 1.3], [0.78, 1.75], [1.0, 0.8]]
'''
new = '''      width: [[0.0, 3.8], [0.206, 3.8], [0.397, 3.8], [0.616, 3.8], [0.78, 4.3], [1.0, 7.5]]
      center_offset: [[0.0, -3.4], [0.206, -0.85], [0.397, -0.6], [0.616, 1.3], [0.78, 1.75], [1.0, 0.0]]
'''
assert old in s; s = s.replace(old, new)
s = s.replace("from station 108 it widens to the\n      two lanes of the next edge.", "from station 108 it widens to the\n      7.5 m of the next edge and returns to the OSM way at the bridge joint (deck not touched).")
s = s.replace("and no kerb is generated between the two ribbons\n", "and no kerb is generated between the two ribbons; over the last 28 m it\n      returns to the standard 8.0 m on the OSM way (bridge joint, deck not touched)\n")
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
