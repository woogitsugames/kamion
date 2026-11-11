rep('''    chevron_axis: [[-800.4, 76.4], [-781.9, 76.5]]
    polygon_en: [[-800.4, 76.4], [-793.3, 77.5], [-781.6, 78.4], [-781.2, 77.2], [-781.9, 76.5], [-781.3, 75.6], [-782.3, 75.5]]
    reason: P-21 chevrons in front of the separator nose, tip at station 88 (xsec/km_trunk.png).''','''    chevron_axis: [[-806.0, 76.9], [-781.9, 76.5]]
    chevron_apex: nose
    stripe_rel_deg: 35
    stripe_w_m: 0.3
    stripe_gap_m: 0.3
    polygon_en: [[-806.0, 77.2], [-795.3, 77.53], [-781.6, 78.4], [-781.2, 77.2], [-781.9, 76.5], [-781.3, 75.6],
                 [-782.3, 75.55], [-795.3, 75.77], [-806.0, 76.6]]
    reason: >-
      P-21 chevrons in front of the separator nose. ADR 0100 (REVIEW s10-0095 P1-3): re-traced on the 1 m grid crop
      artifacts/junctions-r3/trace/dk8_front.jpg - borders N 77.53 / 75.77 at E -795.3, 78.4 / 75.6 at the nose; the
      band runs on west under the truck shadow and narrows to 0.6 m at E -806 (was cut at E -800.4). Chevron apex
      towards the nose, arms about 35 deg to the axis, about 1.05 m apart along the axis, stripe about 0.3 m
      (WORKING_VALUE, 0.08 m orthophoto).''')
rep('''    polyline_en: [[-847.6, 75.6], [-828.5, 76.6], [-800.4, 76.4]]
    reason: Solid line between the ramp lane and the main carriageway, stations 41-88 (xsec/km_trunk0.png, km_trunk.png).''','''    polyline_en: [[-847.6, 75.6], [-828.5, 76.6], [-806.0, 76.9]]
    reason: >-
      Solid line between the ramp lane and the main carriageway, stations 41-82 (xsec/km_trunk0.png, km_trunk.png);
      ends where the P-21 band dk8-ramp-split-p21-front starts (ADR 0100).''')
for zid, az in (("west", 11), ("east", 5), ("north", 42)):
    rep(f'''  - id: n10015785253-p21-{zid}
    kind: painted_zone
    stripe_az_deg: {az}
''', f'''  - id: n10015785253-p21-{zid}
    kind: painted_zone
    stripe_az_deg: {az}
    stripe_w_m: 0.25      # ADR 0100: dense hatching on the 0.08 m orthophoto (zones0/n10015785253-p21-*.jpg), pitch ~0.5 m
    stripe_gap_m: 0.25
''')
rep('''    stripe_az_deg: 4
    polygon_en: [[-386.6, -98.1], [-370.4, -109.2], [-358.5, -120.0], [-352.5, -127.5], [-344.6, -136.4],
                 [-346.6, -137.9], [-354.2, -130.8], [-363.9, -120.0], [-376.3, -109.2]]''','''    axis: [[-386.6, -98.1], [-344.6, -136.4]]
    stripe_rel_deg: -29
    stripe_w_m: 0.3
    stripe_gap_m: 0.25
    border_edges: [0, 1, 2, 3]
    polygon_en: [[-386.6, -98.1], [-371.3, -110.1], [-359.4, -120.9], [-353.4, -128.4], [-344.6, -136.4],
                 [-346.6, -137.9], [-354.2, -130.8], [-363.9, -120.0], [-376.3, -109.2]]''')
rep('''      the direction of travel (xsec/fork_link_raw.png).
    confidence: high''','''      the direction of travel (xsec/fork_link_raw.png). ADR 0100: on the 1 m grid crop artifacts/junctions-r3/trace/
      s1440_band.jpg the band is parallel stripes (not chevrons) about 29 deg clockwise from the axis, 0.3 m wide,
      ~0.55 m pitch, hanging from ONE border line on the NE side (no border at the separator kerb); the NE edge was
      1.3 m too far out (moved SW).
    confidence: high''')
rep('''    chevron_axis: [[-329.5, -151.5], [-344.7, -138.0]]
    polygon_en: [[-329.5, -151.5], [-336.2, -145.0], [-340.2, -141.0], [-343.6, -138.0], [-345.9, -138.0],
                 [-345.0, -140.6], [-340.4, -144.8], [-334.8, -149.0]]''','''    chevron_axis: [[-331.95, -150.05], [-346.4, -136.9]]
    chevron_apex: tip
    stripe_rel_deg: 35
    stripe_w_m: 0.3
    stripe_gap_m: 0.35
    polygon_en: [[-331.95, -150.05], [-339.98, -140.26], [-346.0, -135.4], [-346.6, -138.4], [-345.0, -140.3],
                 [-340.2, -143.3]]''')
rep('''The band NW of the
      nose is s1440-diverge-p21-band.''','''The band NW of the
      nose is s1440-diverge-p21-band. ADR 0100: the ADR 0095 outline lay 1-1.5 m SW of the painted band and its
      axis ran along one border (all stripes on one side); re-traced on the 1 m grid crop artifacts/junctions-r3/trace/
      s1440_nose_p.jpg, axis through the middle, V apex towards the tip, arms ~35 deg, ~1.15 m apart along the axis.''')
