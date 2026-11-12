"""Unapplied r5 design. Copy function into life_props only after baseline review.

Requires the existing module's Mesh and np. Dimensions besides EPAL nominal
envelope/height/board count are WORKING_VALUE; no certification marks.
"""


def pallets_empty(n):
    h = .144*n
    out = []
    for lod in (0, 1):
        m = Mesh()
        rnd = np.random.default_rng(n)
        for layer in range(n):
            dx, dy = rnd.uniform(-.03, .03, 2)
            z = layer*.144
            # Three bottom runners; all boards are 22 mm thick. Retain the
            # old 1 mm inter-layer seam at the bottom/top of every pallet.
            for y in (-.3275, 0, .3275):
                m.box('pallet_wood', [dx, dy+y, z+.012], .6, .0725, .011)
            if lod == 0:
                for x in (-.5275, 0, .5275):
                    m.box('pallet_wood', [dx+x, dy, z+.110], .0725, .4, .011)
                y = -.4
                for width in (.145, .1, .145, .1, .145):
                    m.box('pallet_wood', [dx, dy+y+width/2, z+.132], .6, width/2, .011)
                    y += width+.04125
            else:
                # Upper deck + cross-board depth combined. Side/end fork
                # openings and bottom runners remain actual geometry.
                m.box('pallet_wood', [dx, dy, z+.121], .6, .4, .022)
            for x in (-.5275, 0, .5275):
                for y in (-.3275, 0, .3275):
                    x0, x1 = dx+x-.0725, dx+x+.0725
                    y0, y1 = dy+y-.0725, dy+y+.0725
                    z0, z1 = z+.023, z+.099
                    # Both horizontal block caps are entirely covered by
                    # bottom runners/cross boards; retain all four visible
                    # side walls with outward winding and metre-based UV.
                    uv = ((0, 0), (.145, 0), (.145, .076), (0, .076))
                    for quad in (
                        ((x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1)),
                        ((x1,y1,z0),(x0,y1,z0),(x0,y1,z1),(x1,y1,z1)),
                        ((x0,y1,z0),(x0,y0,z0),(x0,y0,z1),(x0,y1,z1)),
                        ((x1,y0,z0),(x1,y1,z0),(x1,y1,z1),(x1,y0,z1))):
                        m.quad('pallet_wood', *quad, uv=uv)
        out.append(m)
    col = Mesh()
    col.box('collision_steel', [0, 0, h/2], .6, .4, h/2)
    return out[0], out[1], col
