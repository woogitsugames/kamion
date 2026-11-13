# ADR 0172 r1: 182011 - review s17: "camera ~1 lane to the left" (left 40 % footway+lawn vs carriageway with a lane
# left of the camera on the photo). Production = E-537.5 N13 h0 eye1.2. Shift east 1.5/3/4.5 m, one with heading -3.
K = 'sbs-g3-b-182011943700132'
for tag, e, n, h in (('e15', -536.0, 13.0, 0.0), ('e30', -534.5, 13.0, 0.0), ('e45', -533.0, 13.0, 0.0),
                     ('e30h', -534.5, 13.0, 357.0), ('e30n', -534.5, 17.0, 358.0)):
    probe(K, tag, e, n, h, 1.2, note=f'E{e} N{n} h{h} eye1.2')
