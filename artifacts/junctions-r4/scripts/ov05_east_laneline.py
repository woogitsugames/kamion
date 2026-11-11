"""ADR 0110 step 5e: eastbound split - broken lane line of the main carriageway (render b4: the plate drew it solid,
with a gap where the r3 paint_clear polygon lay)."""
p = 'Data/Regions/bialystok-industrial-c/overrides.yaml'
s = open(p, encoding='utf-8').read()
anchor = '  - id: dk8-e-split-line-solid\n'
L = [(-890.0, 56.2), (-875.0, 57.6), (-860.0, 59.2), (-845.0, 59.6), (-829.0, 60.15), (-812.0, 59.65), (-796.0, 59.15), (-786.0, 58.9), (-770.0, 57.25), (-756.0, 56.2)]
up = [[x, round(y + 0.6, 2)] for x, y in L]
dn = [[x, round(y - 0.6, 2)] for x, y in reversed(L)]
new = f'''  - id: dk8-e-split-main-lane-clear
    kind: paint_clear
    polygon_en: {up + dn}
    reason: >-
      ADR 0110: the generated line on the lane boundary of the main carriageway (0.35 m left of the OSM way after
      dk8-e-split-main-geometry) comes out solid on the junction plate (render b4 r3_e_split_top); cleared +-0.6 m and
      repainted broken (next override).
    confidence: high
    verify: owner drive
  - id: dk8-e-split-main-lane
    kind: painted_line
    line: P-1
    polyline_en: {[list(q) for q in L]}
    reason: Broken lane line of the main carriageway E -890...-756 (orthophoto N 59.75 at E -815, plan_b2/east_split.jpg).
    confidence: medium
    verify: owner drive
'''
assert anchor in s
s = s.replace(anchor, new + anchor, 1)
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
