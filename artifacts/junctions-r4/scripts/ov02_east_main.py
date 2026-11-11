"""ADR 0110 step 5b: eastbound main carriageway E -892...-754 placed on the orthophoto (7.0 m, 0.8 m left of the way)."""
p = 'Data/Regions/bialystok-industrial-c/overrides.yaml'
s = open(p, encoding='utf-8').read()
anchor = '  - id: dk8-e-split-link-geometry\n'
new = '''  - id: dk8-e-split-main-geometry
    target: {edge: "w23982185:1832975577-4825844767"}
    reason: >-
      ADR 0110 (REVIEW s10-0100 P1-3): eastbound main carriageway after the split node, 139.5 m. Strip along the OSM way
      (artifacts/junctions-r4/xsec/e_main_raw.png, 14 px/m) and plan crops (plan_b2/east_split.jpg): kerb to edge line
      4.2-4.4 m left and 2.65-2.7 m right of the way = 6.95 m, centre 0.8 m left (PTB standard gave 8.0 m centred, whose
      south 1.3 m lay under the chevrons and the separator island: obstacle_in_lane x 10 in build b2).
    confidence: medium
    verify: owner drive
    set:
      width: [[0.0, 8.0], [0.15, 7.0], [0.9, 7.0], [1.0, 7.6]]
      center_offset: [[0.0, 0.0], [0.15, 0.8], [0.9, 0.8], [1.0, 0.4]]
  - id: dk8-e-split-main-geometry-2
    target: {edge: "w490398847:4825844767-4825844765"}
    reason: Placement of dk8-e-split-main-geometry runs out towards the viaduct (deck geometry not touched).
    confidence: low
    verify: owner drive
    set:
      width: [[0.0, 7.6], [1.0, 7.8]]
      center_offset: [[0.0, 0.4], [1.0, 0.3]]
  - id: dk8-e-split-main-geometry-3
    target: {edge: "w490398850:4825844765-1847263318"}
    reason: Same, back on the OSM way and the standard width 28 m after the joint.
    confidence: low
    verify: owner drive
    set:
      width: [[0.0, 7.8], [0.3, 8.0], [1.0, 8.0]]
      center_offset: [[0.0, 0.3], [0.3, 0.0], [1.0, 0.0]]
'''
assert anchor in s
s = s.replace(anchor, new + anchor, 1)
a = s.index('  - id: dk8-e-split-main-lane')
b = s.index('  - id: dk8-e-split-line-solid')
s = s[:a] + s[b:]      # the generated lane line of the main carriageway now runs here itself (no junction plate)
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
