"""ADR 0110 step 5: eastbound split E -892...-754 by geometry (link width / placement profile) + re-traced paint."""
p = 'Data/Regions/bialystok-industrial-c/overrides.yaml'
s = open(p, encoding='utf-8').read()
a = s.index('  - id: dk8-e-split-p21-front')
b = s.index('  - id: dk8-e-split-barrier')
new = '''  - id: dk8-e-split-link-geometry
    target: {edge: "w173956079:1832975577-2256069814"}
    reason: >-
      ADR 0110 (REVIEW s10-0100 P1-3): eastbound ramp to Rondo Putry, first 139 m after the split node. OSM lanes=3 gave
      an 11.5 m ribbon centred on the way; on the 0.08 m orthophoto it is ONE lane 3.6-4.5 m wide whose south kerb runs
      5.3 -> 2.75 -> 2.5 -> 0.6 -> 0.4 -> 2.4 m right of the way at stations 0 / 29 / 55 / 86 / 108 / 139 (kerb at
      N 50.4 / 51.05 / 52.1 / 51.2 / 48.5 / 42.6; crops artifacts/junctions-r4/trace/e_split_band.jpg 50 px/m,
      plan_b0x/east_split_w.jpg, east_split_e.jpg 17 px/m, xsec/e_link_raw.png). The generated south edge lay 3-4 m
      beyond it. The ribbon now runs from that kerb to the south edge of the main carriageway (so the chevrons and the
      separator island keep asphalt under them). Readings +-0.5 m (WORKING_VALUE). The main carriageway itself lies
      about 1.5 m south of the orthophoto here (viaduct approach, not rebuilt).
    confidence: medium
    verify: owner drive
    set:
      lanes: 1
      width: [[0.0, 10.6], [0.206, 5.5], [0.397, 4.5], [0.616, 4.1], [0.78, 6.0], [1.0, 7.2]]
      center_offset: [[0.0, 0.0], [0.206, 0.0], [0.397, -0.25], [0.616, 1.45], [0.78, 2.6], [1.0, 1.2]]
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
  - id: dk8-e-split-p21-front
    kind: painted_zone
    chevron_axis: [[-831.0, 56.3], [-806.0, 55.3]]
    chevron_apex: tip
    stripe_rel_deg: 35
    stripe_w_m: 0.3
    stripe_gap_m: 0.55
    polygon_en: [[-831.0, 56.65], [-806.2, 56.65], [-805.7, 56.2], [-805.6, 55.75], [-805.9, 55.1], [-806.2, 53.9],
                 [-813.0, 54.5], [-821.0, 55.2], [-831.0, 55.9]]
    reason: >-
      P-21 chevrons in front of the separator nose (apex west). ADR 0110 (REVIEW s10-0100 P1-3): re-traced at 50 px/m
      (artifacts/junctions-r4/trace/e_split_band.jpg): the band is 0.75-1.0 m wide at E -831 and 2.75-3.0 m at the
      nose (south border N 55.9 / 55.2 / 54.5 / 53.9 at E -831 / -821 / -813 / -806.2); the r3 wedge was at most 1.2 m.
    confidence: high
    verify: owner drive
  - id: dk8-e-split-island
    kind: traffic_island
    surface: sidewalk_paving
    polygon_en: [[-805.6, 55.75], [-805.2, 56.45], [-804.4, 56.68], [-796.0, 56.5], [-788.0, 55.6], [-788.0, 53.4],
                 [-797.0, 54.5], [-804.4, 54.9], [-805.2, 55.05]]
    reason: >-
      Kerbed paved separator east of the nose E -805.6 N 55.75. ADR 0110: its east part drifts south with the ramp
      (plan_b0x/east_split_e.jpg: N 52.7-55.1 at E -797); it runs on with the barrier to the bridge joint E -754 -
      traced to E -788 (beyond it the two ribbons separate and the generator builds the kerbs).
    confidence: medium
    verify: owner drive
'''
s = s[:a] + new + s[b:]
old = '''    polygon_en: [[-806.3, 54.65], [-795.5, 54.7], [-795.5, 53.0]]
'''
new = '''    polygon_en: [[-806.2, 53.9], [-806.0, 55.0], [-797.0, 54.45], [-796.5, 53.3]]   # ADR 0110: 1 m band sliding SE (was a wedge)
'''
assert old in s
s = s.replace(old, new)
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
