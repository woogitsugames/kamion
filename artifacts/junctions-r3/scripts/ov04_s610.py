D = "    stripe_w_m: 0.28      # ADR 0100: dense hatching on the 0.08 m orthophoto (trace/s610_centre.jpg, s610_ns.jpg), pitch ~0.56 m\n    stripe_gap_m: 0.28\n"
rep('''  - id: s610-north-arm-p21-median
    kind: painted_zone
    stripe_az_deg: -15
''', '''  - id: s610-north-arm-p21-median
    kind: painted_zone
    stripe_az_deg: 20     # ADR 0100: was -15 (stripes ran the wrong way), trace/s610_ns.jpg left
''' + D)
rep('''  - id: s610-p21-centre
    kind: painted_zone
    stripe_az_deg: 30
''', '''  - id: s610-p21-centre
    kind: painted_zone
    stripe_az_deg: 19     # ADR 0100: measured 19 deg on trace/s610_centre.jpg (stripe (330,480) -> (760,330), 55.6 px/m)
''' + D)
rep('''  - id: s610-p21-west
    kind: painted_zone
    stripe_az_deg: 15
''', '''  - id: s610-p21-west
    kind: painted_zone
    stripe_az_deg: 15
''' + D)
rep('''  - id: s610-p21-south
    kind: painted_zone
    stripe_az_deg: 20
''', '''  - id: s610-p21-south
    kind: painted_zone
    stripe_az_deg: 20
''' + D)
