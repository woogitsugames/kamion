def build_thuja(mb, c, height, radius, key, lod):
    habit = key % 3
    profile = THUJA_HABITS[habit]
    if lod:
        profile = (profile[0],profile[2],profile[3],profile[-1])
        if habit == 1:
            profile = (profile[0],profile[1],profile[-1])
    sides = 8 if lod == 0 else 4
    lean = np.array([h01(key,"lx")-.5,h01(key,"ly")-.5]) * .3
    for layer,grow,mat in ((0,0,MAT),(1,.07,HERO_SHELL)):
        if layer and lod:
            continue
        rings, ring_normals = [], []
        for j,(f,rr) in enumerate(profile):
            ring, normals = [], []
            lo, hi = max(0,j-1), min(len(profile)-1,j+1)
            radius_slope = radius*(profile[hi][1]-profile[lo][1])/(height*(profile[hi][0]-profile[lo][0]))
            for i in range(sides):
                angle = i*2*math.pi/sides + key + .24*math.sin(j)
                direction = np.array([math.cos(angle),math.sin(angle)])
                rad = radius*rr*(.86+.28*h01(key,j,i)) + grow
                ring.append(c + np.r_[lean*f*f + direction*rad,
                                      height*f + (grow if j == len(profile)-1 else 0)])
                # The mesh soup duplicates corners: explicit normals join neighbouring
                # Low faces without more sides, vertices, material slots or passes.
                normals.append(np.r_[direction,-radius_slope-np.dot(direction,2*f*lean/height)])
            rings.append(ring)
            ring_normals.append(normals)
        for j in range(1 if layer else 0,len(rings)-1):
            for i in range(sides):
                ii = (i+1)%sides
                uv = foliage_uv(key+i,j)
                if layer:
                    per = 2*math.pi*radius/sides/.6
                    u0,u1 = (i*per+key*.37),(i+1)*per+key*.37
                    v0,v1 = profile[j][0]*height/.6,profile[j+1][0]*height/.6
                    uv = [(u0,v0),(u1,v0),(u1,v1),(u0,v1)]
                normals = [ring_normals[j][i],ring_normals[j][ii],ring_normals[j+1][ii],ring_normals[j+1][i]] if lod else None
                mb.face([rings[j][i],rings[j][ii],rings[j+1][ii],rings[j+1][i]],uv,mat,
                        np.append((rings[j][i]+rings[j][ii])[:2]/2-c[:2],.15),normals=normals)
