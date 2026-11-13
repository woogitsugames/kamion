# ADR 0160 r4: 504348 near teal plate at the left edge (3-4 m, az ~257) = the east island sign (567.1,-704.2) of the
# regenerated world; camera placed so that sign sits at that bearing/distance; heading from the deck VP (296.4).
import math as _m
HZ = 0.76
K = 'sbs-g3-a-504348097385466'
SE = (567.1, -704.2)
for tag, az, d in (('e35', 257.0, 3.5), ('e30', 257.0, 3.0), ('e45', 257.0, 4.5), ('e35a', 250.0, 3.5), ('e35b', 264.0, 3.5)):
    e = SE[0] - d * _m.sin(_m.radians(az)); n = SE[1] - d * _m.cos(_m.radians(az))
    probe(K, tag, e, n, 296.4, 0.9, horizon=HZ, note=f'east sign at az{az} d{d}, h296.4 eye0.9')
