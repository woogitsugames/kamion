"""ADR 0110 step 5c: eastbound split, second layout (b3 left a kerbed gap between the two ribbons under the chevrons):
the MAIN carriageway carries the hatching / island zone beyond its two lanes (lane_edges + width), the ramp is the
3.8-4.3 m lane along the south kerb."""
p = 'Data/Regions/bialystok-industrial-c/overrides.yaml'
s = open(p, encoding='utf-8').read()
a = s.index('  - id: dk8-e-split-main-geometry\n')
b = s.index('  - id: dk8-e-split-p21-front')
new = '''  - id: dk8-e-split-main-geometry
    target: {edge: "w23982185:1832975577-4825844767"}
    reason: >-
      ADR 0110 (REVIEW s10-0100 P1-3): eastbound DK8 after the split node, 139.5 m to the bridge joint. Orthophoto
      (artifacts/junctions-r4/trace/e_split_band.jpg 50 px/m, plan_b2/east_split.jpg 20 px/m, xsec/e_main_raw.png): north
      kerb about 4.3 m left of the OSM way, lane line 0.35 m left, solid line / top border of the chevrons 2.55 m right
      (N 64.2 / 59.75 / 56.9 at E -815) = two lanes 3.45 + 2.9 m; south of them the painted wedge (0.75 -> 3 m) and from
      E -805.6 the kerbed separator. lane_edges (from the left edge) + width: the carriageway runs on under the hatching
      and the island to the ramp lane, so they keep asphalt under them and no kerb is generated between the two ribbons
      (the standard gave 8.0 m centred on the way: its right lane lay under the chevrons and the island).
      Readings +-0.5 m between crops (WORKING_VALUE).
    confidence: medium
    verify: owner drive
    set:
      lane_edges: [0.5, 3.95, 6.85]
      width: 10.6
      center_offset: -1.0
      edge_lines: left
  - id: dk8-e-split-main-geometry-2
    target: {edge: "w490398847:4825844767-4825844765"}
    reason: The widened plate of dk8-e-split-main-geometry runs out towards the viaduct over this 11.5 m edge.
    confidence: low
    verify: owner drive
    set:
      width: [[0.0, 10.6], [1.0, 9.0]]
      center_offset: [[0.0, -1.0], [1.0, -0.4]]
  - id: dk8-e-split-main-geometry-3
    target: {edge: "w490398850:4825844765-1847263318"}
    reason: Same, back to the standard 8.0 m on the OSM way 19 m after the joint (viaduct deck not touched).
    confidence: low
    verify: owner drive
    set:
      width: [[0.0, 9.0], [0.2, 8.0], [1.0, 8.0]]
      center_offset: [[0.0, -0.4], [0.2, 0.0], [1.0, 0.0]]
  - id: dk8-e-split-link-geometry
    target: {edge: "w173956079:1832975577-2256069814"}
    reason: >-
      ADR 0110 (REVIEW s10-0100 P1-3): eastbound ramp to Rondo Putry, first 139 m after the split node. OSM lanes=3 gave
      an 11.5 m ribbon centred on the way; on the 0.08 m orthophoto it is ONE lane 3.6-4.3 m wide whose south kerb runs
      5.3 / 2.75 / 2.5 / 0.6 / 0.4 / 2.4 m right of the way at stations 0 / 29 / 55 / 86 / 108 / 139 (kerb at N 50.4 /
      51.05 / 52.1 / 51.2 / 48.5 / 42.6; crops artifacts/junctions-r4/trace/e_split_band.jpg, plan_b0x/east_split_w.jpg,
      east_split_e.jpg, xsec/e_link_raw.png). The generated south edge lay 3-4 m beyond it. The ribbon is that lane (the
      hatching and the island lie on the main carriageway, dk8-e-split-main-geometry); from station 108 it widens to the
      two lanes of the next edge. Readings +-0.5 m (WORKING_VALUE).
    confidence: medium
    verify: owner drive
    set:
      lanes: 1
      width: [[0.0, 3.8], [0.206, 3.8], [0.397, 3.8], [0.616, 3.8], [0.78, 4.3], [1.0, 7.2]]
      center_offset: [[0.0, -3.4], [0.206, -0.85], [0.397, -0.6], [0.616, 1.3], [0.78, 1.75], [1.0, 1.2]]
      edge_lines: right
  - id: dk8-e-split-link-geometry-2
    target: {edge: "w257367449:2256069814-2256069811"}
    reason: Continuation of dk8-e-split-link-geometry over the 11.5 m edge at the bridge joint (placement and width run on).
    confidence: low
    verify: owner drive
    set:
      width: [[0.0, 7.2], [1.0, 7.5]]
      center_offset: [[0.0, 1.2], [1.0, 0.9]]
  - id: dk8-e-split-link-geometry-3
    target: {edge: "w249431348:2256069811-2629251364"}
    reason: The placement of dk8-e-split-link-geometry fades back to the OSM way over the first 35 m (no jog at the joint).
    confidence: low
    verify: owner drive
    set:
      center_offset: [[0.0, 0.9], [0.2, 0.0], [1.0, 0.0]]
'''
s = s[:a] + new + s[b:]
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
